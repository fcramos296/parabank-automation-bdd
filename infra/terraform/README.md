# AWS QA Infrastructure

Terraform definition for the ephemeral ParaBank E2E environment used by **version 2.0** on `release/2.0-aws`.

## What this creates

- Amazon ECR repository for the Playwright/Behave runner image;
- Amazon ECS cluster;
- Fargate task definition with `parabank` and `tests` containers in the same task;
- isolated VPC with two public subnets and an outbound-only security group;
- CloudWatch Logs for both containers;
- private S3 bucket for Allure artifacts;
- ECS execution/task roles;
- GitHub Actions IAM role authenticated through OIDC.

No load balancer or inbound security-group rule is required. Both containers share the Fargate task network namespace and the runner reaches ParaBank at:

```text
http://localhost:8080/parabank
```

The public subnets are used so the ephemeral task can pull container images and reach AWS/public endpoints without introducing a NAT Gateway. `ecs run-task` uses `assignPublicIp=ENABLED`. The task security group has no inbound rules.

## Prerequisites

- AWS account;
- AWS CLI authenticated locally for the first deployment and for infrastructure updates that change IAM trust;
- Terraform 1.6+;
- permissions to create/update IAM, VPC, ECR, ECS, CloudWatch and S3 resources.

## Configure

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars
```

Review at minimum:

```hcl
aws_region        = "us-east-1"
github_repository = "fcramos296/parabank-automation-bdd"
```

The OIDC trust is intentionally restricted to the exact Git refs listed in `github_allowed_refs`. The repository default authorizes only:

```text
refs/heads/release/2.0-aws
```

`main` is intentionally excluded from the AWS trust policy so the stable 1.x line cannot assume the 2.0 AWS role.

## Validate

```bash
terraform fmt -recursive
terraform init
terraform validate
terraform plan
```

The repository also validates `terraform fmt` and `terraform validate` in GitHub Actions without applying infrastructure.

## Deploy or update

```bash
terraform apply
```

After creating `release/2.0-aws`, an existing environment provisioned with the previous branch trust must receive one new `terraform apply` so the live IAM role trusts the release branch.

Important outputs:

```bash
terraform output ecr_repository_url
terraform output ecs_cluster_name
terraform output task_definition_arn
terraform output github_actions_role_arn
terraform output allure_results_bucket
terraform output fargate_subnet_ids
terraform output fargate_security_group_id
```

## GitHub OIDC

Terraform creates the IAM OIDC provider for:

```text
https://token.actions.githubusercontent.com
```

with audience `sts.amazonaws.com`.

If the AWS account already has this GitHub OIDC provider, import it into this Terraform state before applying instead of creating a duplicate:

```bash
terraform import aws_iam_openid_connect_provider.github \
  arn:aws:iam::<ACCOUNT_ID>:oidc-provider/token.actions.githubusercontent.com
```

The GitHub Actions role receives only the permissions required by the Fargate workflow: push the runner image to ECR, register/run/inspect the QA ECS task, pass the two ECS roles, access the Allure bucket and read task logs.

## ECR image strategy

The ECR repository is immutable. The AWS workflow publishes a unique runner image for each execution instead of overwriting `latest`.

Example:

```text
<account>.dkr.ecr.<region>.amazonaws.com/parabank-qa-test-runner:<commit-and-run-identity>
```

The Terraform task definition uses `runner_image_tag` only for the bootstrap revision. During each AWS execution, GitHub Actions pushes the new image and registers a new task-definition revision pointing to that exact image.

## Fargate task lifecycle

The implemented execution is:

```text
GitHub Actions
    -> OIDC assume-role
    -> authenticate to ECR
    -> build test runner
    -> push immutable runner image
    -> register ECS task revision
    -> ecs run-task
         parabank + tests
    -> wait for completion
    -> inspect tests container exit code
    -> read CloudWatch evidence
    -> retrieve Allure results from S3
    -> enforce quality gate
    -> cleanup task when required
```

The test container waits for ParaBank readiness before starting Behave. The `tests` container exit code is used as the functional quality gate.

## Security notes

- no long-lived AWS keys are required by GitHub Actions;
- OIDC trust is restricted to `release/2.0-aws`;
- the Fargate security group has no ingress rules;
- the Allure S3 bucket blocks public access and uses server-side encryption;
- `iam:PassRole` is limited to the ECS task/execution roles;
- task and GitHub permissions are scoped to project resources where supported.

## State note

Terraform backend configuration remains external. For a personal/demo account, bootstrap may use local state. Before shared/team usage, move state to a protected remote backend with locking and controlled access.
