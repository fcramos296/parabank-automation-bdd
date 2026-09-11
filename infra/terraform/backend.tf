terraform {
  backend "s3" {
    bucket       = "parabank-qa-terraform-state-986033946222-us-east-1"
    key          = "release-2.0-aws/terraform.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true
  }
}
