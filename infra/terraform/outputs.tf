output "aws_account_id" {
  description = "AWS account where the QA infrastructure is deployed."
  value       = data.aws_caller_identity.current.account_id
}

output "aws_region" {
  description = "AWS region used by the QA infrastructure."
  value       = var.aws_region
}

output "ecr_repository_url" {
  description = "ECR repository used by the containerized test runner."
  value       = aws_ecr_repository.runner.repository_url
}

output "ecs_cluster_name" {
  description = "ECS cluster that hosts ephemeral E2E tasks."
  value       = aws_ecs_cluster.qa.name
}

output "ecs_cluster_arn" {
  description = "ECS cluster ARN."
  value       = aws_ecs_cluster.qa.arn
}

output "task_definition_arn" {
  description = "Bootstrap ECS task definition ARN."
  value       = aws_ecs_task_definition.qa.arn
}

output "task_definition_family" {
  description = "ECS task definition family used by CI revisions."
  value       = aws_ecs_task_definition.qa.family
}

output "github_actions_role_arn" {
  description = "IAM role assumed by GitHub Actions through OIDC."
  value       = aws_iam_role.github_actions.arn
}

output "allure_results_bucket" {
  description = "Private S3 bucket reserved for Allure artifacts."
  value       = aws_s3_bucket.allure.bucket
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group for ParaBank and test-runner logs."
  value       = aws_cloudwatch_log_group.ecs.name
}

output "fargate_subnet_ids" {
  description = "Subnets to pass to ecs run-task."
  value       = aws_subnet.public[*].id
}

output "fargate_security_group_id" {
  description = "Security group to pass to ecs run-task."
  value       = aws_security_group.fargate.id
}
