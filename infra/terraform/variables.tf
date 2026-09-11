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

variable "github_repository_owner_id" {
  description = "Immutable GitHub repository owner ID used in OIDC subject claims."
  type        = string
  default     = "297217694"
}

variable "github_repository_id" {
  description = "Immutable GitHub repository ID used in OIDC subject claims."
  type        = string
  default     = "1363052182"
}

variable "github_allowed_refs" {
  description = "Exact Git refs allowed to assume the GitHub Actions OIDC role."
  type        = list(string)
  default = [
    "refs/heads/release/2.0-aws",
  ]
}

variable "runner_image_tag" {
  description = "Image tag referenced by the bootstrap ECS task definition. CI registers later revisions using immutable run-specific tags."
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
