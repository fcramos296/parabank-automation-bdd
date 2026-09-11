# AWS QA Infrastructure

Terraform definition for the ephemeral ParaBank E2E environment on AWS.

## What this creates

- Amazon ECR repository for the Playwright/Behave runner image;
- Amazon ECS cluster;
- Fargate task definition with `parabank` and `tests` containers in the same task;
- isolated VPC with two public subnets and an outbound-only security group;
- CloudWatch Logs for both containers;
- private S3 bucket reserved for Allure artifacts;
- ECS execution/task roles;
- GitHub Actions IAM role authenticated through OIDC.

No load balancer or inbound security-group rule is required. Both containers share the Fargate task network namespace and the runner reaches ParaBank at:

```text
http://localhost:8080/parabank
```

The public subnets are used only so the ephemeral task can pull container images and reach AWS/public endpoints without introducing a NAT Gateway. `ecs run-task` must use `assignPublicIp=ENABLED`. The task security group has no inbound rules.

## Prerequisites

- AWS account;
- AWS CLI authenticated locally for the first Terraform deployment;
- Terraform 1.6+;
- permissions to create IAM, VPC, ECR, ECS, CloudWatch and S3 resources.

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

The OIDC trust is intentionally restricted to the exact Git refs listed in `github_allowed_refs`.

## Validate

```bash
terraform fmt -recursive
terraform init
terraform validate
terraform plan
```

The repository also validates `terraform fmt` and `terraform validate` in GitHub Actions without applying infrastructure.

## Deploy

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

The GitHub Actions role receives only the permissions needed for this workflow: push the runner image to its ECR repository, register/run/inspect the QA ECS task, pass the two ECS roles, access the Allure bucket and read the task logs.

## ECR image strategy

The ECR repository is immutable. CI should publish the runner using the Git commit SHA rather than `latest`:

```text
<account>.dkr.ecr.<region>.amazonaws.com/parabank-qa-test-runner:<git-sha>
```

The Terraform task definition uses `runner_image_tag` as a bootstrap revision. The next CI increment will push the SHA-tagged image and register a new task-definition revision using that exact image.

## Fargate task lifecycle

The intended execution is:

```text
GitHub Actions
    -> OIDC assume-role
    -> build test runner
    -> push SHA image to ECR
    -> register task revision
    -> ecs run-task
         parabank + tests
    -> inspect tests container exit code
    -> collect evidence
    -> task disappears
```

The test container already waits for ParaBank readiness, so ECS only needs to start both containers in the same task. When the essential `tests` container exits, ECS terminates the ephemeral task and CI will use its exit code as the quality gate.

## State note

This first infrastructure increment intentionally leaves Terraform backend configuration external. For a personal/demo account, bootstrap can use local state. Before shared/team usage, move state to a protected remote backend with locking.
