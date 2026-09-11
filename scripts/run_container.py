from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Sequence

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

        print(f"[container] Allure results: {ALLURE_RESULTS_DIR}")
        return int(completed.returncode)

    except KeyboardInterrupt:
        print("[container] Execution cancelled.")
        return 130

    except Exception as exc:
        print(f"[container][ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
