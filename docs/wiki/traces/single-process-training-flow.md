# 单进程训练流程

## 概览

该流程描述从执行 `python -m scripts.train --config ...` 到单进程完成训练循环的核心路径。

## 触发条件

用户在项目根目录执行单进程训练命令，传入任意有效 YAML 配置。

## 步骤

### 1. 解析并构建配置 (`scripts/train.py`)

脚本解析 `--config` 与 `--distributed`，使用 `DictConfig` 加载 YAML，并将 CLI 的分布式开关写回配置。

**关键操作**:
- 读取配置文件并实例化 `DictConfig`
- `unfreeze -> add -> freeze` 更新 `train.distributed`

**状态变化**:
- 生成运行时配置对象并传入 `Trainer`

### 2. 运行时初始化 (`train/trainer.py`)

`Trainer._setup_runtime()` 建立训练所需对象。

**关键操作**:
- 设置随机种子
- 构建 dataset/dataloader
- 构建 model/loss/optimizer
- 根据配置构建 evaluator/visualizer（可选）

### 3. 迭代训练循环 (`train/trainer.py`)

`Trainer.train()` 在 epoch/batch 循环中调用 `_train_one_batch()`。

**数据变换**:
```text
输入 batch
  ↓
normalize_batch_to_data_dict()
  ↓
model(data_dict)
  ↓
loss_dict -> total_loss
  ↓
optimizer.step()
```

### 4. 日志与检查点保存 (`train/trainer.py`)

按 `log_interval` 输出 loss，按 `save_interval` 保存 checkpoint。

### 5. 验证与报告 (`train/trainer.py`, `train/validation_report.py`)

当满足 `validate.val_interval_steps` 或 `validate.val_interval_epochs` 时，执行 `_validate_once()`：

1. 遍历 `val_loader`，前向得到 `data_dict`
2. 调用 evaluator `update(...)` 聚合任务指标
3. 调用 evaluator `finalize(...)` 产出 `EvaluationResult`
4. 调用 visualizer `log(...)` 写 TensorBoard（可选）
5. 调用 `ValidationReportWriter.save(...)` 写 `val_metrics-<val-id>.json`

## 时序图

```text
用户 -> scripts/train.py -> DictConfig -> Trainer
Trainer -> Registry: build dataset/model/loss
Trainer -> DataLoader: fetch batch
Trainer -> Model: forward(data_dict)
Trainer -> Loss: total_loss
Trainer -> Optimizer: step
Trainer -> Evaluator: update/finalize (validate interval)
Trainer -> Visualizer: log to TensorBoard
Trainer -> ValidationReportWriter: save report json
Trainer -> LocalCheckpointIO: save (interval)
```

## 成功路径

配置可解析、注册名称可构建、loss 可回传 `total_loss` 时，训练可稳定推进并按周期产生日志、验证结果与 checkpoint。

## 异常路径

### 异常场景 1

**触发条件**: `dataset.name` / `model.name` / `loss.name` 未注册

**处理过程**:
1. `build_dataset` / `build_module` 抛 `ValueError`
2. 训练流程终止并输出可用名称列表

**结果**: 启动失败，需修正配置名或注册逻辑

### 异常场景 2

**触发条件**: 前向结果未提供可用损失（无 loss module、无 `_loss_dict`、无 `total_loss`）

**处理过程**:
1. `_compute_loss` 抛 `ValueError`
2. 当前训练中断

**结果**: 需要补充 loss 配置或模型输出协议

## 相关流程

- [分布式训练流程](distributed-training-flow.md)

## 相关系统

- [训练编排系统](../systems/training-orchestration.md)
- [注册与插件加载系统](../systems/registry-and-plugin-loading.md)
