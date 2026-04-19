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
- `.claude/skills/deep-codebase-wiki/SKILL.md` is adapted from [deep-codebase-wiki on MCP Market](https://mcpmarket.com/zh/tools/skills/deep-codebase-wiki).
