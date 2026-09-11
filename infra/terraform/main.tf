data "aws_caller_identity" "current" {}

data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  name_prefix  = "${var.project_name}-${var.environment}"
  runner_image = "${aws_ecr_repository.runner.repository_url}:${var.runner_image_tag}"

  github_repository_parts = split("/", var.github_repository)

  github_subjects = [
    for ref in var.github_allowed_refs :
    "repo:${local.github_repository_parts[0]}@${var.github_repository_owner_id}/${local.github_repository_parts[1]}@${var.github_repository_id}:ref:${ref}"
  ]
}
