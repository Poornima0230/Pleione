from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import pandas as pd
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel, Field


router = APIRouter(
    prefix="/api/screening-runs",
    tags=["Screening Runs"],
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = BASE_DIR / "data"
RUNS_DIR = DATA_DIR / "screening_runs"
LOGS_DIR = RUNS_DIR / "logs"
RUNS_FILE = RUNS_DIR / "runs.json"

RUNS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# CURRENT PIPELINE
# ============================================================

PIPELINE = [
    {
        "key": "module_a",
        "label": "Module A",
        "description": "0h peer-based anomaly detection",
        "script": BASE_DIR / "scripts" / "module_A_train.py",
        "output": DATA_DIR / "module_A" / "module_A_all_predictions.csv",
    },
    {
        "key": "module_b",
        "label": "Module B",
        "description": "0h + 24h future-risk forecasting",
        "script": BASE_DIR / "scripts" / "module_B_train.py",
        "output": DATA_DIR / "module_B" / "module_B_predictions.csv",
    },
    {
        "key": "module_c",
        "label": "Module C",
        "description": "Final screening risk decision",
        "script": BASE_DIR / "scripts" / "module_C.py",
        "output": DATA_DIR / "module_C" / "module_C_all_results.csv",
    },
]


# ============================================================
# RUNTIME STATE
# ============================================================

RUN_LOCK = threading.Lock()


# ============================================================
# MODELS
# ============================================================

class ScreeningRunCreate(BaseModel):
    lot_id: Optional[str] = None
    notes: Optional[str] = Field(default=None, max_length=1000)


# ============================================================
# HELPERS
# ============================================================

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def python_executable() -> str:
    """
    Prefer the project's Windows virtual environment.
    Otherwise use the Python executable running FastAPI.
    """

    candidates = [
        BASE_DIR / "venv" / "Scripts" / "python.exe",
        BASE_DIR / ".venv" / "Scripts" / "python.exe",
        BASE_DIR / "venv" / "bin" / "python",
        BASE_DIR / ".venv" / "bin" / "python",
    ]

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    return sys.executable


def relative_path(path: Path) -> str:
    try:
        return str(path.relative_to(BASE_DIR)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def load_runs() -> list[dict[str, Any]]:
    if not RUNS_FILE.exists():
        return []

    try:
        with RUNS_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            return data

        return []

    except Exception:
        return []


def save_runs(runs: list[dict[str, Any]]) -> None:
    temp_file = RUNS_FILE.with_suffix(".tmp")

    with temp_file.open("w", encoding="utf-8") as f:
        json.dump(runs, f, indent=2)

    temp_file.replace(RUNS_FILE)


def get_run(run_id: str) -> Optional[dict[str, Any]]:
    runs = load_runs()

    for run in runs:
        if run.get("run_id") == run_id:
            return run

    return None


def update_run(run_id: str, **updates: Any) -> dict[str, Any]:
    runs = load_runs()

    for index, run in enumerate(runs):
        if run.get("run_id") == run_id:
            run.update(updates)
            runs[index] = run
            save_runs(runs)
            return run

    raise KeyError(f"Run not found: {run_id}")


def append_log(run_id: str, module_key: str, message: str) -> None:
    log_file = LOGS_DIR / f"{run_id}_{module_key}.log"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with log_file.open("a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")


def output_signature(path: Path) -> Optional[dict[str, Any]]:
    if not path.exists():
        return None

    stat = path.stat()

    return {
        "mtime_ns": stat.st_mtime_ns,
        "size": stat.st_size,
    }


def count_csv_rows(path: Path) -> Optional[int]:
    if not path.exists():
        return None

    try:
        df = pd.read_csv(path)
        return int(len(df))
    except Exception:
        return None


def artifact_info(path: Path) -> dict[str, Any]:
    exists = path.exists()

    info: dict[str, Any] = {
        "path": relative_path(path),
        "exists": exists,
        "bytes": None,
        "modified_at": None,
        "row_count": None,
    }

    if not exists:
        return info

    stat = path.stat()

    info["bytes"] = stat.st_size
    info["modified_at"] = datetime.fromtimestamp(
        stat.st_mtime,
        tz=timezone.utc,
    ).isoformat()

    info["row_count"] = count_csv_rows(path)

    return info


def build_module_states() -> dict[str, dict[str, Any]]:
    result = {}

    for module in PIPELINE:
        result[module["key"]] = {
            "key": module["key"],
            "label": module["label"],
            "description": module["description"],
            "status": "not_started",
            "started_at": None,
            "finished_at": None,
            "duration_seconds": None,
            "script": relative_path(module["script"]),
            "output": relative_path(module["output"]),
            "artifact": artifact_info(module["output"]),
            "error": None,
        }

    return result


def build_artifacts() -> list[dict[str, Any]]:
    return [
        {
            "module": module["key"],
            "label": module["label"],
            "path": relative_path(module["output"]),
            "exists": module["output"].exists(),
            "row_count": count_csv_rows(module["output"]),
            "bytes": module["output"].stat().st_size
            if module["output"].exists()
            else None,
            "modified_at": (
                datetime.fromtimestamp(
                    module["output"].stat().st_mtime,
                    tz=timezone.utc,
                ).isoformat()
                if module["output"].exists()
                else None
            ),
        }
        for module in PIPELINE
    ]


def build_summary() -> dict[str, Any]:
    summary: dict[str, Any] = {
        "component_count": None,
        "module_a": {},
        "module_b": {},
        "module_c": {},
    }

    # --------------------------------------------------------
    # Module A
    # --------------------------------------------------------

    module_a_file = DATA_DIR / "module_A" / "module_A_all_predictions.csv"

    if module_a_file.exists():
        try:
            df = pd.read_csv(module_a_file)

            summary["module_a"] = {
                "total": int(len(df)),
                "status_counts": {
                    str(k): int(v)
                    for k, v in df["module_a_status"]
                    .value_counts(dropna=False)
                    .to_dict()
                    .items()
                }
                if "module_a_status" in df.columns
                else {},
            }

            summary["component_count"] = int(len(df))

        except Exception:
            pass

    # --------------------------------------------------------
    # Module B
    # --------------------------------------------------------

    module_b_file = DATA_DIR / "module_B" / "module_B_predictions.csv"

    if module_b_file.exists():
        try:
            df = pd.read_csv(module_b_file)

            summary["module_b"] = {
                "total": int(len(df)),
                "risk_counts": {
                    str(k): int(v)
                    for k, v in df["failure_risk"]
                    .value_counts(dropna=False)
                    .to_dict()
                    .items()
                }
                if "failure_risk" in df.columns
                else {},
            }

            if summary["component_count"] is None:
                summary["component_count"] = int(len(df))

        except Exception:
            pass

    # --------------------------------------------------------
    # Module C
    # --------------------------------------------------------

    module_c_file = DATA_DIR / "module_C" / "module_C_all_results.csv"

    if module_c_file.exists():
        try:
            df = pd.read_csv(module_c_file)

            summary["module_c"] = {
                "total": int(len(df)),
                "decision_counts": {
                    str(k): int(v)
                    for k, v in df["final_decision"]
                    .value_counts(dropna=False)
                    .to_dict()
                    .items()
                }
                if "final_decision" in df.columns
                else {},
                "future_risk_counts": {
                    str(k): int(v)
                    for k, v in df["future_risk"]
                    .value_counts(dropna=False)
                    .to_dict()
                    .items()
                }
                if "future_risk" in df.columns
                else {},
                "evidence_counts": {
                    str(k): int(v)
                    for k, v in df["evidence_level"]
                    .value_counts(dropna=False)
                    .to_dict()
                    .items()
                }
                if "evidence_level" in df.columns
                else {},
            }

            if summary["component_count"] is None:
                summary["component_count"] = int(len(df))

        except Exception:
            pass

    return summary


def current_run() -> Optional[dict[str, Any]]:
    runs = load_runs()

    active = [
        run
        for run in runs
        if run.get("status") in {"queued", "running"}
    ]

    if not active:
        return None

    active.sort(
        key=lambda x: x.get("created_at", ""),
        reverse=True,
    )

    return active[0]


def is_output_fresh(
    path: Path,
    before_signature: Optional[dict[str, Any]],
) -> bool:
    after_signature = output_signature(path)

    if after_signature is None:
        return False

    if before_signature is None:
        return True

    return (
        after_signature["mtime_ns"] != before_signature["mtime_ns"]
        or after_signature["size"] != before_signature["size"]
    )


def execute_module(
    run_id: str,
    module: dict[str, Any],
) -> None:

    key = module["key"]

    update_module(
        run_id,
        key,
        status="running",
        started_at=now_iso(),
        finished_at=None,
        duration_seconds=None,
        error=None,
    )

    append_log(
        run_id,
        key,
        f"Starting {module['label']}",
    )

    append_log(
        run_id,
        key,
        f"Script: {relative_path(module['script'])}",
    )

    append_log(
        run_id,
        key,
        f"Expected output: {relative_path(module['output'])}",
    )

    before = output_signature(module["output"])

    start_time = time.perf_counter()

    command = [
        python_executable(),
        str(module["script"]),
    ]

    append_log(
        run_id,
        key,
        "Executing pipeline script...",
    )

    try:
        process = subprocess.Popen(
            command,
            cwd=str(BASE_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )

        assert process.stdout is not None

        for line in process.stdout:
            line = line.rstrip()

            if line:
                append_log(run_id, key, line)

        return_code = process.wait()

        duration = round(
            time.perf_counter() - start_time,
            3,
        )

        if return_code != 0:
            error_message = (
                f"{module['label']} exited with code {return_code}"
            )

            append_log(
                run_id,
                key,
                error_message,
            )

            update_module(
                run_id,
                key,
                status="failed",
                finished_at=now_iso(),
                duration_seconds=duration,
                error=error_message,
            )

            raise RuntimeError(error_message)

        if not module["output"].exists():
            error_message = (
                f"{module['label']} completed but expected output "
                f"was not created: {relative_path(module['output'])}"
            )

            append_log(
                run_id,
                key,
                error_message,
            )

            update_module(
                run_id,
                key,
                status="failed",
                finished_at=now_iso(),
                duration_seconds=duration,
                error=error_message,
            )

            raise RuntimeError(error_message)

        if not is_output_fresh(module["output"], before):
            error_message = (
                f"{module['label']} completed but the output file "
                f"was not refreshed."
            )

            append_log(
                run_id,
                key,
                error_message,
            )

            update_module(
                run_id,
                key,
                status="failed",
                finished_at=now_iso(),
                duration_seconds=duration,
                error=error_message,
            )

            raise RuntimeError(error_message)

        rows = count_csv_rows(module["output"])

        append_log(
            run_id,
            key,
            f"Output rows: {rows}",
        )

        append_log(
            run_id,
            key,
            f"{module['label']} completed successfully.",
        )

        update_module(
            run_id,
            key,
            status="completed",
            finished_at=now_iso(),
            duration_seconds=duration,
            error=None,
        )

    except Exception as exc:
        duration = round(
            time.perf_counter() - start_time,
            3,
        )

        update_module(
            run_id,
            key,
            status="failed",
            finished_at=now_iso(),
            duration_seconds=duration,
            error=str(exc),
        )

        raise


def update_module(
    run_id: str,
    module_key: str,
    **updates: Any,
) -> None:

    runs = load_runs()

    for run in runs:
        if run.get("run_id") != run_id:
            continue

        module = run.get("pipeline", {}).get(module_key)

        if module is None:
            return

        module.update(updates)

        save_runs(runs)
        return


def run_pipeline(run_id: str) -> None:

    try:
        update_run(
            run_id,
            status="running",
            started_at=now_iso(),
            error=None,
        )

        append_log(
            run_id,
            "pipeline",
            "Screening pipeline started.",
        )

        append_log(
            run_id,
            "pipeline",
            "Execution order: Module A -> Module B -> Module C",
        )

        for module in PIPELINE:
            run = get_run(run_id)

            if run is None:
                raise RuntimeError(
                    f"Run disappeared while executing: {run_id}"
                )

            # Mark following modules as queued when reached.
            update_module(
                run_id,
                module["key"],
                status="queued",
            )

            execute_module(
                run_id,
                module,
            )

        finished_at = now_iso()

        run = get_run(run_id)

        started_at = (
            datetime.fromisoformat(
                run["started_at"]
            )
            if run and run.get("started_at")
            else None
        )

        finished_dt = datetime.fromisoformat(finished_at)

        duration = None

        if started_at:
            duration = round(
                (
                    finished_dt - started_at
                ).total_seconds(),
                3,
            )

        summary = build_summary()

        update_run(
            run_id,
            status="completed",
            finished_at=finished_at,
            total_duration_seconds=duration,
            component_count=summary.get("component_count"),
            summary=summary,
            artifacts=build_artifacts(),
            error=None,
        )

        append_log(
            run_id,
            "pipeline",
            "Screening pipeline completed successfully.",
        )

    except Exception as exc:

        finished_at = now_iso()

        run = get_run(run_id)

        started_at = (
            datetime.fromisoformat(
                run["started_at"]
            )
            if run and run.get("started_at")
            else None
        )

        duration = None

        if started_at:
            duration = round(
                (
                    datetime.fromisoformat(finished_at)
                    - started_at
                ).total_seconds(),
                3,
            )

        update_run(
            run_id,
            status="failed",
            finished_at=finished_at,
            total_duration_seconds=duration,
            summary=build_summary(),
            artifacts=build_artifacts(),
            error=str(exc),
        )

        append_log(
            run_id,
            "pipeline",
            f"Pipeline failed: {exc}",
        )

    finally:
        # The lock only protects starting a second run.
        if RUN_LOCK.locked():
            try:
                RUN_LOCK.release()
            except RuntimeError:
                pass


# ============================================================
# ROUTES
# ============================================================

@router.get("/")
def list_runs(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
):
    runs = load_runs()

    runs.sort(
        key=lambda x: x.get("created_at", ""),
        reverse=True,
    )

    total = len(runs)

    start = (page - 1) * limit
    end = start + limit

    return {
        "page": page,
        "limit": limit,
        "pages": max(1, (total + limit - 1) // limit),
        "total": total,
        "runs": runs[start:end],
    }


@router.get("/status/current")
def current_status():
    run = current_run()

    return {
        "active": run is not None,
        "run": run,
    }


@router.post("/")
def create_run(payload: ScreeningRunCreate):

    active = current_run()

    if active:
        raise HTTPException(
            status_code=409,
            detail=(
                "A screening run is already queued or running."
            ),
        )

    run_id = (
        datetime.now().strftime("%Y%m%d-%H%M%S")
        + "-"
        + uuid.uuid4().hex[:6]
    )

    pipeline_states = build_module_states()

    requested_scope = "All lots / full dataset"

    if payload.lot_id:
        raise HTTPException(
            status_code=400,
            detail=(
                "The current screening pipeline processes the full "
                "dataset and does not support per-lot execution."
            ),
        )

    run = {
        "run_id": run_id,
        "status": "not_started",
        "scope": requested_scope,
        "lot_id": None,
        "notes": payload.notes,
        "created_at": now_iso(),
        "started_at": None,
        "finished_at": None,
        "total_duration_seconds": None,
        "component_count": None,
        "pipeline": pipeline_states,
        "artifacts": [],
        "summary": {},
        "error": None,
    }

    runs = load_runs()
    runs.append(run)
    save_runs(runs)

    return run


@router.post("/{run_id}/start")
def start_run(
    run_id: str,
    background_tasks: BackgroundTasks,
):

    if not RUN_LOCK.acquire(blocking=False):
        raise HTTPException(
            status_code=409,
            detail="Another screening run is already executing.",
        )

    run = get_run(run_id)

    if run is None:
        RUN_LOCK.release()

        raise HTTPException(
            status_code=404,
            detail="Screening run not found.",
        )

    if run.get("status") not in {"not_started", "failed"}:
        RUN_LOCK.release()

        raise HTTPException(
            status_code=400,
            detail=(
                f"Run cannot be started from status "
                f"'{run.get('status')}'."
            ),
        )

    update_run(
        run_id,
        status="queued",
        error=None,
    )

    append_log(
        run_id,
        "pipeline",
        "Run queued for execution.",
    )

    background_tasks.add_task(
        run_pipeline,
        run_id,
    )

    return get_run(run_id)


@router.get("/{run_id}")
def get_run_details(run_id: str):

    run = get_run(run_id)

    if run is None:
        raise HTTPException(
            status_code=404,
            detail="Screening run not found.",
        )

    # Refresh artifact metadata for visibility.
    run["artifacts"] = build_artifacts()

    if run.get("status") in {"completed", "failed"}:
        run["summary"] = build_summary()

    return run


@router.post("/{run_id}/refresh")
def refresh_run(run_id: str):

    run = get_run(run_id)

    if run is None:
        raise HTTPException(
            status_code=404,
            detail="Screening run not found.",
        )

    run["artifacts"] = build_artifacts()

    if run.get("status") in {"completed", "failed"}:
        run["summary"] = build_summary()

    save_runs(
        [
            run if item.get("run_id") == run_id else item
            for item in load_runs()
        ]
    )

    return run


@router.get("/{run_id}/logs/{module_name}")
def get_module_logs(
    run_id: str,
    module_name: str,
):

    run = get_run(run_id)

    if run is None:
        raise HTTPException(
            status_code=404,
            detail="Screening run not found.",
        )

    allowed = {
        "pipeline",
        "module_a",
        "module_b",
        "module_c",
    }

    if module_name not in allowed:
        raise HTTPException(
            status_code=400,
            detail="Unknown module log.",
        )

    log_file = LOGS_DIR / f"{run_id}_{module_name}.log"

    if not log_file.exists():

        return {
            "run_id": run_id,
            "module": module_name,
            "exists": False,
            "content": "",
        }

    content = log_file.read_text(
        encoding="utf-8",
        errors="replace",
    )

    return {
        "run_id": run_id,
        "module": module_name,
        "exists": True,
        "content": content,
    }