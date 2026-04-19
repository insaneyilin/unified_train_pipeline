# Unified Train Pipeline

## Structure

```text
unified_train_pipeline/
  docs/
  core/
  registry/
  hooks/
  train/
  interfaces/
  tasks/
  configs/
  scripts/
```

## Quick Start

### 1) Install dependencies

#### Option A: `requirements.txt` (recommended first)

```bash
python -m pip install -r requirements.txt
```

Pinned versions in this file are verified on macOS with:

- Python `3.10.12`
- torch `2.7.0`
- torchvision `0.22.0`

#### Option B: Poetry

Install Poetry first, then run:

```bash
poetry install
```

Run scripts with Poetry:

```bash
poetry run python -m scripts.train --config configs/mnist_mlp.yaml
poetry run python -m scripts.smoke_test
```

### 2) Enter working directory

```bash
cd unified_train_pipeline
```

### 3) Run single-process training

```bash
python -m scripts.train \
  --config configs/mnist_mlp.yaml
```

### 3.1) Start TensorBoard

```bash
tensorboard --logdir unified_train_pipeline_outputs/mnist_mlp/tb
```

Then open `http://localhost:6006` in your browser.

### 4) Run distributed training (example)

```bash
torchrun --nproc_per_node=2 -m scripts.train \
  --config configs/mnist_conv.yaml \
  --distributed
```

### 5) Run smoke test

```bash
python -m scripts.smoke_test
```

## Example Configs

- `configs/mnist_mlp.yaml`
- `configs/mnist_conv.yaml`
- `configs/cifar_resnet18.yaml`
- `configs/cifar_wideresnet.yaml`
- `configs/coco128_fasterrcnn.yaml`
- `configs/coco128_retinanet.yaml`

## Notes

- COCO128 dataset wrapper supports synthetic fallback if local COCO files are not found.
- Checkpoint backend defaults to local filesystem through `LocalCheckpointIO`.
- If you need real COCO annotations, install `pycocotools` manually in your environment.
- `configs/mnist_mlp.yaml` now includes validation and TensorBoard defaults:
  - `validate.val_interval_steps` and `validate.val_interval_epochs` can both be enabled.
  - `evaluation.name` selects the evaluator plugin (current default: `MnistClassificationEvaluator`).
  - `visualization.name` selects the visualizer plugin (current default: `MnistTensorBoardVisualizer`).
  - Validation writes `val/loss`, `val/accuracy`, per-digit breakdown, confusion matrix, and `val_metrics-<val-id>.json`.
  - TensorBoard writes `train/total_loss`, validation scalars, per-digit scalars, confusion matrix, and sampled validation images.
- To add a new task-level validation flow (for example detection), implement task-specific plugins in `tasks/<task>/evaluators.py` and `tasks/<task>/visualizers.py`, then switch names in config without changing `train/trainer.py`.
- `.claude/skills/deep-codebase-wiki/SKILL.md` is adapted from [deep-codebase-wiki on MCP Market](https://mcpmarket.com/zh/tools/skills/deep-codebase-wiki).
