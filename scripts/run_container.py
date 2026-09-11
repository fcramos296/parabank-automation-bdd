from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

import boto3
import requests

from config.settings import settings
from scripts.parabank_env import parabank_is_ready


PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"
ALLURE_RESULTS_DIR = REPORTS_DIR / "allure-results"
SUPPORTED_BROWSERS = ("chromium", "firefox", "webkit")
FEATURE_SCOPES = {
    "login": PROJECT_ROOT / "features" / "login.feature",
    "registration": PROJECT_ROOT / "features" / "registration.feature",
    "transfer": PROJECT_ROOT / "features" / "transfer.feature",
}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run ParaBank E2E tests from a prebuilt container image.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--scope",
        choices=tuple(FEATURE_SCOPES),
        help="Execute only one feature scope.",
    )
    parser.add_argument(
        "--tags",
        help="Behave tag expression. Example: --tags '@smoke'",
    )
    parser.add_argument(
        "--browser",
        choices=SUPPORTED_BROWSERS,
        default="chromium",
        help="Playwright browser bundled in the runner image.",
    )
    return parser.parse_args(argv)


def wait_for_sut() -> None:
    timeout = settings.LOCAL_STARTUP_TIMEOUT_SECONDS
    deadline = time.monotonic() + timeout

    print(f"[container] Waiting for ParaBank at {settings.BASE_URL} ...")

    while time.monotonic() < deadline:
        if parabank_is_ready(settings.BASE_URL):
            print("[container] ParaBank is ready.")
            return

        time.sleep(2)

    raise RuntimeError(
        "ParaBank did not become ready within "
        f"{timeout:.0f} seconds at {settings.BASE_URL}."
    )


def prepare_allure_results() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    if ALLURE_RESULTS_DIR.exists():
        shutil.rmtree(ALLURE_RESULTS_DIR)

    ALLURE_RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def build_behave_command(args: argparse.Namespace) -> list[str]:
    command = [sys.executable, "-m", "behave"]

    if args.scope:
        feature_path = FEATURE_SCOPES[args.scope]
        command.append(str(feature_path.relative_to(PROJECT_ROOT)))

    if args.tags:
        command.extend(["--tags", args.tags])

    command.extend(
        [
            "-D",
            "headless=true",
            "-D",
            f"browser={args.browser}",
        ]
    )

    return command


def get_task_execution_id() -> str:
    metadata_uri = os.getenv("ECS_CONTAINER_METADATA_URI_V4")

    if metadata_uri:
        try:
            response = requests.get(
                f"{metadata_uri}/task",
                timeout=3,
            )
            response.raise_for_status()

            task_arn = str(response.json().get("TaskARN", ""))

            if task_arn:
                return task_arn.rsplit("/", maxsplit=1)[-1]

        except requests.RequestException as exc:
            print(
                "[container][WARN] "
                f"Unable to read ECS task metadata: {exc}"
            )

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    suffix = uuid.uuid4().hex[:8]

    return f"local-{timestamp}-{suffix}"


def upload_allure_results() -> str | None:
    bucket = os.getenv("ALLURE_RESULTS_S3_BUCKET")

    if not bucket:
        print(
            "[container] ALLURE_RESULTS_S3_BUCKET is not configured; "
            "skipping S3 upload."
        )
        return None

    artifacts = sorted(
        artifact
        for artifact in ALLURE_RESULTS_DIR.rglob("*")
        if artifact.is_file()
    )

    if not artifacts:
        print("[container] No Allure results found to upload.")
        return None

    task_id = get_task_execution_id()
    prefix = f"tasks/{task_id}/allure-results"

    s3 = boto3.client("s3")

    print(
        f"[container] Uploading {len(artifacts)} Allure artifacts "
        f"to s3://{bucket}/{prefix}/"
    )

    for artifact in artifacts:
        relative_path = artifact.relative_to(ALLURE_RESULTS_DIR).as_posix()
        object_key = f"{prefix}/{relative_path}"

        s3.upload_file(
            str(artifact),
            bucket,
            object_key,
        )

    s3_uri = f"s3://{bucket}/{prefix}/"

    print(f"[container] Allure upload completed: {s3_uri}")

    return s3_uri


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        wait_for_sut()
        prepare_allure_results()

        command = build_behave_command(args)

        print("[container] Starting Behave suite.")
        print("[container] Command: " + " ".join(command))

        completed = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            check=False,
        )

        test_exit_code = int(completed.returncode)

        print(f"[container] Allure results: {ALLURE_RESULTS_DIR}")

        try:
            upload_allure_results()
        except Exception as exc:
            print(f"[container][ERROR] Failed to upload Allure results: {exc}")

            if test_exit_code == 0:
                return 1

        return test_exit_code

    except KeyboardInterrupt:
        print("[container] Execution cancelled.")
        return 130

    except Exception as exc:
        print(f"[container][ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
