resource "aws_s3_bucket" "allure" {
  bucket_prefix = "${local.name_prefix}-allure-"
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "allure" {
  bucket = aws_s3_bucket.allure.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "allure" {
  bucket = aws_s3_bucket.allure.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "allure" {
  bucket = aws_s3_bucket.allure.id

  rule {
    id     = "expire-allure-artifacts"
    status = "Enabled"

    expiration {
      days = var.allure_retention_days
    }
  }
}
