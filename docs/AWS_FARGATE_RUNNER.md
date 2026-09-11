# AWS Fargate - Containerized Test Runner

This branch introduces the first step toward running the ParaBank E2E suite on AWS ECS/Fargate: a self-contained Playwright/Behave test-runner image.

## Why a separate runner image?

The existing `scripts/run.py` owns the local developer workflow: it verifies Docker, recreates the ParaBank container, prepares Python dependencies and runs Behave.

Inside ECS/Fargate, Docker orchestration belongs to ECS rather than to the test container. The runner therefore needs to:

1. wait for an already-started ParaBank instance;
2. run Behave headlessly;
3. return the Behave exit code;
4. leave Allure results in `reports/allure-results` for later collection.

That responsibility is implemented by `scripts/run_container.py`.

## Runner image

`Dockerfile.tests` is based on:

```text
mcr.microsoft.com/playwright/python:v1.62.0-noble
```

The image version intentionally matches `playwright==1.62.0` from `requirements.txt` so the Python package and bundled browser executables stay compatible.

Build it locally:

```bash
docker build -f Dockerfile.tests -t parabank-automation:local .
```

## Local end-to-end validation

`compose.runner.yaml` starts two containers:

- `parabank`: the official ParaBank image;
- `tests`: the new automation runner image.

The test container waits until ParaBank responds successfully before starting Behave.

Run the complete suite:

```bash
docker compose -f compose.runner.yaml up --build --abort-on-container-exit --exit-code-from tests
```

Clean up afterward:

```bash
docker compose -f compose.runner.yaml down --volumes --remove-orphans
```

Allure result files are mounted back to the host under:

```text
reports/allure-results
```

## Running a subset

Because the image uses `scripts/run_container.py` as its entrypoint, arguments can be passed directly.

Example smoke execution:

```bash
docker compose -f compose.runner.yaml run --rm tests --tags "@smoke"
```

Example transfer feature:

```bash
docker compose -f compose.runner.yaml run --rm tests --scope transfer
```

Example Firefox execution:

```bash
docker compose -f compose.runner.yaml run --rm tests --browser firefox --tags "@smoke"
```

## How this maps to ECS/Fargate

For local Docker Compose the runner reaches ParaBank through the Compose service name:

```text
LOCAL_BASE_URL=http://parabank:8080/parabank
```

For the planned ECS/Fargate task, ParaBank and the runner will be containers in the same task. The runner configuration will therefore use:

```text
LOCAL_BASE_URL=http://localhost:8080/parabank
```

The test code itself does not change. Only the runtime configuration changes.

## Next step

The next infrastructure increment is to create:

- an Amazon ECR repository for this runner image;
- an ECS cluster and Fargate task definition;
- IAM roles and GitHub OIDC authentication;
- CloudWatch Logs;
- a result-export strategy for Allure artifacts, initially using S3.

The existing `main` workflow remains untouched while this work is developed on `feat/aws-fargate-e2e`.
