# AWS Fargate - Containerized Test Runner

This branch evolves the ParaBank E2E suite toward AWS ECS/Fargate while keeping the delivered `main` implementation untouched.

## Containerized runner

The existing `scripts/run.py` owns the local developer workflow: it verifies Docker, recreates ParaBank, prepares Python dependencies and runs Behave.

Inside ECS/Fargate, orchestration belongs to ECS rather than to the test container. `scripts/run_container.py` therefore has a smaller responsibility:

1. wait for an already-started ParaBank instance;
2. run Behave headlessly;
3. return the Behave exit code;
4. write Allure results to `reports/allure-results`.

`Dockerfile.tests` is based on:

```text
mcr.microsoft.com/playwright/python:v1.62.0-noble
```

The image version intentionally matches `playwright==1.62.0` from `requirements.txt`.

Build locally:

```bash
docker build -f Dockerfile.tests -t parabank-automation:local .
```

## Local end-to-end validation

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

Allure results are mounted to:

```text
reports/allure-results
```

The container runner is also validated by `.github/workflows/container-runner.yml` whenever runner-related files change.

## AWS infrastructure now defined

The second increment adds Terraform under `infra/terraform/` for the AWS runtime. It is ready to provision:

- Amazon ECR repository for the test-runner image;
- Amazon ECS cluster;
- Fargate task definition containing `parabank` and `tests`;
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

In Fargate both containers belong to the same task, so the test runner uses:

```text
LOCAL_BASE_URL=http://localhost:8080/parabank
```

No load balancer or inbound rule is required for the SUT.

## Terraform validation

The Terraform source is statically validated by `.github/workflows/terraform-validate.yml` using:

```bash
terraform fmt -check -recursive
terraform init -backend=false -input=false
terraform validate -no-color
```

This workflow does not create AWS resources.

## Initial AWS bootstrap

The first `terraform apply` requires credentials for the target AWS account because the deployment itself creates the GitHub OIDC provider and the IAM role that future GitHub Actions runs will assume.

From an authenticated workstation or AWS CloudShell:

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform plan
terraform apply
```

After the apply, record these outputs:

```bash
terraform output github_actions_role_arn
terraform output ecr_repository_url
terraform output ecs_cluster_name
terraform output task_definition_family
terraform output allure_results_bucket
terraform output fargate_subnet_ids
terraform output fargate_security_group_id
```

If the AWS account already has the GitHub Actions OIDC provider, import it into this Terraform state before applying. See `infra/terraform/README.md`.

## Next increment

After the AWS bootstrap, the next workflow will:

```text
GitHub Actions
    -> request OIDC token
    -> assume the AWS IAM role
    -> build Dockerfile.tests
    -> tag image with Git commit SHA
    -> push image to ECR
    -> register an ECS task-definition revision
    -> run the ephemeral Fargate task
    -> wait for completion
    -> inspect the tests container exit code
    -> collect Allure/CloudWatch evidence
```

The existing production-like project on `main` remains unchanged while AWS work stays isolated on `feat/aws-fargate-e2e`.
