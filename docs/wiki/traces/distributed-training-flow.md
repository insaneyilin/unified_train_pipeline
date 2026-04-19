# 分布式训练流程

## 概览

该流程描述通过 `torchrun` 启动多进程训练时，框架如何初始化 DDP、切分数据并执行同步训练。

## 触发条件

用户执行如下命令并传入 `--distributed`：

```bash
torchrun --nproc_per_node=2 -m scripts.train --config configs/mnist_mlp.yaml --distributed
```

## 步骤

### 1. 进程启动 (`torchrun` + `scripts/train.py`)

`torchrun` 为每个进程注入 rank/world 环境变量，`scripts/train.py` 将分布式开关写入配置并创建 `Trainer`。

### 2. DDP 初始化 (`train/distributed.py`)

在 `_setup_runtime()` 中调用 `init_distributed()` 初始化 process group，并根据 local rank 设置设备。

**关键操作**:
- 读取环境变量 `RANK`, `WORLD_SIZE`, `LOCAL_RANK`
- `torch.distributed.init_process_group(...)`

### 3. 采样器与模型包装 (`train/trainer.py`)

训练 loader 使用 `DistributedSampler`，模型包装为 `DistributedDataParallel`。

**状态变化**:
- 每个 rank 仅处理其 shard 数据
- 反向阶段自动进行梯度同步

### 4. 基于进程编号的副作用控制 (`train/trainer.py`)

日志和 checkpoint 保存仅在 rank 0 执行，epoch 结束调用 `synchronize()` 对齐进度。

## 时序图

```text
torchrun -> 各 rank 进程
各 rank -> Trainer._setup_runtime()
各 rank -> init_distributed()
各 rank -> DDP(model) + DistributedSampler
各 rank -> forward/backward/step
rank 0 -> logging + checkpoint
所有 rank -> synchronize() -> 下一轮 epoch
```

## 成功路径

所有进程成功初始化分布式环境后，训练可在多卡上并行执行，并维持参数一致更新。

## 异常路径

### 异常场景 1

**触发条件**: 分布式环境变量缺失或不一致

**处理过程**:
1. `init_distributed()` 初始化失败
2. 训练进程报错退出

**结果**: 需要修正启动方式（优先使用 `torchrun`）

### 异常场景 2

**触发条件**: 非 rank 0 误执行文件写入逻辑（定制代码引入）

**处理过程**:
1. 可能引发并发写入冲突
2. 应通过 rank 条件保护副作用逻辑

**结果**: checkpoint/log 文件可能损坏或重复

## 相关流程

- [单进程训练流程](single-process-training-flow.md)

## 相关系统

- [训练编排系统](../systems/training-orchestration.md)
