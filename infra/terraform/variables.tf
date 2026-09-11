variable "aws_region" {
  description = "AWS region used by the QA infrastructure."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Base name used for AWS resources."
  type        = string
  default     = "parabank-qa"
}

variable "environment" {
  description = "Logical environment name."
  type        = string
  default     = "test"
}

variable "github_repository" {
  description = "GitHub repository allowed to assume the AWS deployment role."
  type        = string
  default     = "fcramos296/parabank-automation-bdd"
}

variable "github_allowed_refs" {
  description = "Exact Git refs allowed to assume the GitHub Actions OIDC role."
  type        = list(string)
  default = [
    "refs/heads/main",
    "refs/heads/feat/aws-fargate-e2e",
  ]
}

variable "runner_image_tag" {
  description = "Image tag referenced by the bootstrap ECS task definition. CI will later register revisions using commit-SHA tags."
  type        = string
  default     = "bootstrap"
}

variable "parabank_image" {
  description = "ParaBank container image used by the Fargate task."
  type        = string
  default     = "parasoft/parabank:baseline"
}

variable "task_cpu" {
  description = "Fargate task CPU units."
  type        = number
  default     = 2048
}

variable "task_memory" {
  description = "Fargate task memory in MiB."
  type        = number
  default     = 4096
}

variable "log_retention_days" {
  description = "CloudWatch log retention period."
  type        = number
  default     = 14
}

variable "allure_retention_days" {
  description = "Number of days Allure artifacts are retained in S3."
  type        = number
  default     = 30
}

variable "vpc_cidr" {
  description = "CIDR used by the isolated QA VPC."
  type        = string
  default     = "10.42.0.0/16"
}
