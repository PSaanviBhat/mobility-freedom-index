import json
import shutil
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROOT_DIR.parent
BACKEND_MODELS_DIR = REPO_ROOT / "backend" / "models"
NOTEBOOKS = [
    ROOT_DIR / "preprocessing.ipynb",
    ROOT_DIR / "model.ipynb",
    ROOT_DIR / "threshold-tuning.ipynb",
]
SYNC_ARTIFACTS = [
    "best_risk_model_pipeline.joblib",
    "threshold_config.joblib",
]


def _build_namespace() -> dict:
    namespace = {"__name__": "__main__"}
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        plt.show = lambda *args, **kwargs: None
        namespace["plt"] = plt
    except Exception:
        pass

    try:
        from IPython.display import display

        namespace["display"] = display
    except Exception:
        namespace["display"] = print

    return namespace


def run_notebook(path: Path) -> None:
    namespace = _build_namespace()
    data = json.loads(path.read_text(encoding="utf-8"))

    for index, cell in enumerate(data.get("cells", []), start=1):
        if cell.get("cell_type") != "code":
            continue
        source = "".join(cell.get("source", []))
        if not source.strip():
            continue
        compiled = compile(source, f"{path.name}::cell_{index}", "exec")
        exec(compiled, namespace)


def sync_backend_artifacts() -> None:
    artifacts_dir = ROOT_DIR / "artifacts"
    BACKEND_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    for artifact_name in SYNC_ARTIFACTS:
        source = artifacts_dir / artifact_name
        if source.exists():
            shutil.copy2(source, BACKEND_MODELS_DIR / artifact_name)


def main() -> None:
    original_cwd = Path.cwd()
    try:
        for notebook_path in NOTEBOOKS:
            print(f"Running {notebook_path.name}...")
            run_notebook(notebook_path)
        sync_backend_artifacts()
        print("Notebook pipeline completed successfully.")
    finally:
        import os

        os.chdir(original_cwd)


if __name__ == "__main__":
    import os

    os.chdir(ROOT_DIR)
    main()
