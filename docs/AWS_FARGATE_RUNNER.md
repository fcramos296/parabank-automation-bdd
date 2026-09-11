# AWS Fargate - Containerized Test Runner

This document describes the AWS execution model used by **ParaBank Automation BDD 2.0**.

The repository intentionally keeps two maintained lines:

- `main`: stable 1.x implementation focused on local Docker execution and the original CI pipeline;
- `release/2.0-aws`: AWS-enabled implementation using ECS/Fargate, ECR, S3, CloudWatch, Terraform and GitHub OIDC.

The AWS version is maintained independently and is not intended to be merged into `main`.

## Containerized runner

The local developer workflow remains available through `scripts/run.py`. It verifies Docker, recreates ParaBank, prepares the Python environment and runs Behave.

Inside ECS/Fargate, orchestration belongs to ECS rather than to the test container. `scripts/run_container.py` therefore has a smaller responsibility:

1. wait for the ParaBank container to become ready;
2. run Behave headlessly;
3. preserve the Behave exit code;
4. write Allure results to `reports/allure-results`;
5. publish the generated results to the configured S3 bucket when running in AWS.

`Dockerfile.tests` is based on:

```text
mcr.microsoft.com/playwright/python:v1.62.0-noble
```

The image version intentionally matches `playwright==1.62.0` from `requirements.txt`.

Build locally:

```bash
docker build -f Dockerfile.tests -t parabank-automation:local .
```

## Local container validation

`compose.runner.yaml` starts:

- `parabank`: official ParaBank image;
- `tests`: containerized Playwright/Behave runner.

Run the complete suite:

```bash
docker compose -f compose.runner.yaml up --build --abort-on-container-exit --exit-code-from tests
```

Run only smoke:

```bash
docker compose -f compose.runner.yaml up -d parabank
docker compose -f compose.runner.yaml run --rm tests --tags "@smoke"
docker compose -f compose.runner.yaml down --volumes --remove-orphans
```

Local Allure results are written to:

```text
reports/allure-results
```

The container runner is validated by `.github/workflows/container-runner.yml` when runner-related files change on `release/2.0-aws`.

## AWS architecture

Terraform under `infra/terraform/` provisions the runtime used by version 2.0:

- Amazon ECR repository for the test-runner image;
- Amazon ECS cluster;
- Fargate task definition containing `parabank` and `tests` containers;
- dedicated VPC with two public subnets;
- security group with no inbound rules;
- CloudWatch Logs;
- private S3 bucket for Allure artifacts;
- ECS execution and task IAM roles;
- GitHub Actions IAM role authenticated through OIDC.

For local Compose the runner reaches ParaBank through the service name:

```text
LOCAL_BASE_URL=http://parabank:8080/parabank
```

In Fargate both containers belong to the same task and share the task network namespace, so the test runner uses:

```text
LOCAL_BASE_URL=http://localhost:8080/parabank
```

No load balancer or inbound security-group rule is required for the SUT.

## GitHub OIDC isolation

The AWS role trust policy is intentionally restricted to this exact Git ref:

```text
refs/heads/release/2.0-aws
```

The `main` branch is not authorized to assume the AWS deployment role.

After changing the trusted branch in Terraform, apply the updated infrastructure once from an authenticated workstation or AWS CloudShell so the live IAM trust policy matches the repository configuration:

```bash
cd infra/terraform
terraform init
terraform plan
terraform apply
```

## Terraform validation

Terraform is statically validated by `.github/workflows/terraform-validate.yml` using:

```bash
terraform fmt -check -recursive
terraform init -backend=false -input=false
terraform validate -no-color
```

This workflow validates source code only; it does not create or modify AWS resources.

## Initial AWS bootstrap

The first infrastructure deployment requires credentials for the target AWS account because Terraform creates the GitHub OIDC provider and IAM role used by later GitHub Actions runs.

From an authenticated workstation or AWS CloudShell:

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform plan
terraform apply
```

Important outputs:

```bash
terraform output github_actions_role_arn
terraform output ecr_repository_url
terraform output ecs_cluster_name
terraform output task_definition_family
terraform output allure_results_bucket
terraform output fargate_subnet_ids
terraform output fargate_security_group_id
```

If the AWS account already contains the GitHub Actions OIDC provider, import it into this Terraform state before applying. See `infra/terraform/README.md`.

## AWS Fargate workflow

`.github/workflows/aws-fargate-e2e.yml` implements the complete remote execution flow:

```text
GitHub Actions
    -> request GitHub OIDC token
    -> assume the AWS IAM role
    -> authenticate to ECR
    -> build Dockerfile.tests
    -> tag the runner image with the current execution identity
    -> push the image to ECR
    -> register a new ECS task-definition revision
    -> run the ephemeral Fargate task
         parabank + tests
    -> wait for task completion
    -> inspect the tests container exit code
    -> print CloudWatch test logs
    -> download Allure results from S3
    -> upload Allure results as a GitHub Actions artifact
    -> enforce the quality gate
    -> stop the task if cleanup is required
```

The workflow is manual (`workflow_dispatch`) and accepts:

- a Behave tag expression;
- the Playwright browser (`chromium`, `firefox` or `webkit`).

The test result is considered successful only when the `tests` container returns exit code `0` and Allure evidence is retrieved successfully.

## Evidence and retention

During AWS execution:

- application/test logs are sent to CloudWatch Logs;
- Allure result files are persisted to the private S3 bucket;
- GitHub Actions downloads those files and publishes them as a workflow artifact;
- S3 and CloudWatch retention are controlled by Terraform variables.

## Security model

The AWS implementation follows a deliberately small access surface:

- no long-lived AWS access keys in GitHub;
- OIDC trust restricted to `release/2.0-aws`;
- `iam:PassRole` restricted to the ECS task/execution roles;
- S3 public access blocked;
- S3 server-side encryption enabled;
- no inbound security-group rules for the Fargate task;
- IAM permissions scoped to the project resources wherever AWS supports resource-level scoping.

## Versioning decision

Version 2.0 remains isolated on:

```text
release/2.0-aws
```

The stable 1.x implementation remains on:

```text
main
```

This separation allows the local/Docker implementation and the AWS/Fargate implementation to evolve independently without forcing cloud infrastructure into the stable 1.x line.
