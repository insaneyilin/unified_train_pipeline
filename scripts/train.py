import argparse
import sys
from pathlib import Path

# Make imports work when running inside `unified_train_pipeline/` directly.
PROJECT_DIR = Path(__file__).resolve().parents[1]
PARENT_DIR = PROJECT_DIR.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

try:
    from unified_train_pipeline.core import DictConfig
    from unified_train_pipeline.train import Trainer
    # Import tasks for side-effect registration.
    from unified_train_pipeline import tasks  # noqa: F401
except ModuleNotFoundError:
    # Fallback for local execution: `python -m scripts.train`.
    from core import DictConfig
    from train import Trainer
    import tasks  # noqa: F401


def main():
    parser = argparse.ArgumentParser("Unified train pipeline runner")
    parser.add_argument("--config", type=str, required=True, help="YAML config path")
    parser.add_argument("--distributed",
                        action="store_true",
                        help="Enable distributed mode from CLI")
    args = parser.parse_args()

    config = DictConfig(args.config)
    config.unfreeze()
    config.add({"train": {"distributed": bool(args.distributed)}})
    config.freeze()

    trainer = Trainer(config)
    trainer.train()


if __name__ == "__main__":
    main()
