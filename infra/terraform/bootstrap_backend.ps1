param(
    [string]$Profile = "parabank",
    [string]$Region = "us-east-1",
    [string]$Bucket = "parabank-qa-terraform-state-986033946222-us-east-1",
    [string]$ExpectedAccountId = "986033946222"
)

$ErrorActionPreference = "Stop"
$env:AWS_PROFILE = $Profile

$AccountId = (
    aws sts get-caller-identity `
        --query Account `
        --output text
).Trim()

if ($LASTEXITCODE -ne 0) {
    throw "Unable to validate the AWS identity for profile '$Profile'."
}

if ($AccountId -ne $ExpectedAccountId) {
    throw "Refusing to create the backend in AWS account '$AccountId'. Expected '$ExpectedAccountId'."
}

aws s3api head-bucket --bucket $Bucket 2>$null
$BucketExists = $LASTEXITCODE -eq 0

if (-not $BucketExists) {
    Write-Host "Creating Terraform state bucket: $Bucket"

    if ($Region -eq "us-east-1") {
        aws s3api create-bucket `
            --bucket $Bucket `
            --region $Region | Out-Null
    }
    else {
        aws s3api create-bucket `
            --bucket $Bucket `
            --region $Region `
            --create-bucket-configuration "LocationConstraint=$Region" | Out-Null
    }

    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create Terraform state bucket '$Bucket'."
    }
}
else {
    Write-Host "Terraform state bucket already exists: $Bucket"
}

aws s3api put-public-access-block `
    --bucket $Bucket `
    --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true | Out-Null

aws s3api put-bucket-encryption `
    --bucket $Bucket `
    --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}' | Out-Null

aws s3api put-bucket-versioning `
    --bucket $Bucket `
    --versioning-configuration Status=Enabled | Out-Null

aws s3api put-bucket-tagging `
    --bucket $Bucket `
    --tagging 'TagSet=[{Key=Project,Value=parabank-qa},{Key=Environment,Value=test},{Key=ManagedBy,Value=TerraformBackend}]' | Out-Null

Write-Host ""
Write-Host "Terraform backend bucket is ready."
Write-Host "Bucket : $Bucket"
Write-Host "Region : $Region"
Write-Host "Account: $AccountId"
Write-Host ""
Write-Host "Next command:"
Write-Host "terraform init -migrate-state -reconfigure"
