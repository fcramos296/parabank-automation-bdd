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
- AWS CLI authenticated locally for infrastructure administration;
- Terraform 1.10+;
- permissions to create/update IAM, VPC, ECR, ECS, CloudWatch and S3 resources.

## Remote Terraform state

The 2.0 line stores Terraform state in a dedicated private S3 backend:

```text
s3://parabank-qa-terraform-state-986033946222-us-east-1/release-2.0-aws/terraform.tfstate
```

The backend uses:

- S3 server-side encryption;
- bucket versioning;
- public-access blocking;
- native S3 state locking through `use_lockfile = true`;
- a state bucket separate from the Allure artifacts bucket.

The backend bucket is a bootstrap dependency and is therefore created outside the main Terraform state. On the first setup only, run:

```powershell
$env:AWS_PROFILE = "parabank"
.\bootstrap_backend.ps1
```

For an existing local state that must be migrated into S3:

```powershell
terraform init -migrate-state -reconfigure
```

Review and accept the migration prompt only after confirming the local `terraform.tfstate` is the recovered/current state.

After migration, validate:

```powershell
terraform state list
terraform plan
```

The expected result after a synchronized apply is:

```text
No changes. Your infrastructure matches the configuration.
```

Do not commit `terraform.tfstate`, `terraform.tfstate.*` or plan files.

## New clone workflow

Once the remote backend exists, a new workstation does not need imports or a copied state file. The normal flow is:

```powershell
git clone https://github.com/fcramos296/parabank-automation-bdd.git
cd parabank-automation-bdd
git switch release/2.0-aws
$env:AWS_PROFILE = "parabank"
cd infra\terraform
terraform init
terraform plan
```

Terraform downloads the existing state from S3 automatically.

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

The repository also validates `terraform fmt` and `terraform validate` in GitHub Actions with `terraform init -backend=false`, so CI validation does not require backend credentials and never applies infrastructure.

## Deploy or update

```bash
terraform apply
```

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

Terraform ignores runtime drift in `container_definitions` so it does not replace a CI-generated task revision with the bootstrap image during infrastructure maintenance.

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
- the Terraform state bucket is private, encrypted and versioned;
- S3 native lock files prevent concurrent Terraform state writes;
- `iam:PassRole` is limited to the ECS task/execution roles;
- task and GitHub permissions are scoped to project resources where supported.
