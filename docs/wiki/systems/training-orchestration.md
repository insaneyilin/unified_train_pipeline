# 训练编排系统

## 作用

该系统负责端到端训练生命周期管理：运行环境初始化、数据加载、模型与损失构建、优化迭代、验证调度、日志输出、checkpoint 保存，以及可选分布式训练控制。

## 组成组件

### 训练器（`train/trainer.py`，类名 `Trainer`）

核心训练编排器，负责 `_setup_runtime()`、`_train_one_batch()`、`_validate_once()` 和 `train()` 主循环。

**关键方法**:
- `_setup_runtime()` - 初始化随机种子、分布式环境、loader/model/loss/evaluator/visualizer/optimizer
- `_train_one_batch()` - 执行单步前向、损失、反向、优化器更新、hook 调用
- `_validate_once()` - 验证循环调度：调用 evaluator 聚合结果，再交给 visualizer 与 report writer
- `train()` - 执行 epoch/batch 双层循环，处理日志、验证与 checkpoint 周期

### 训练循环工具（`train/loop.py`）

负责 batch 标准化和设备搬运，使上层逻辑统一操作 `data_dict`。

### 分布式工具（`train/distributed.py`）

提供 process group 初始化、rank/world 获取、同步与清理等能力。

### 验证报告写入（`train/validation_report.py`）

提供 `ValidationReportWriter`，将 `EvaluationResult` 写入 `val_metrics-<val-id>.json`。

## 数据流

```text
Config (DictConfig)
  ↓
Trainer._setup_runtime()
  ↓
DataLoader + Model + Loss + Evaluator + Visualizer + Optimizer
  ↓
Trainer.train() epoch/batch loop
  ↓
_train_one_batch()
  ↓
Forward -> Loss -> Backward -> Step
  ↓
Log/Checkpoint/Validate
```

训练数据以 `data_dict` 形式在 batch 处理中流动，hook 在 `before_iteration`、`after_forward`、`after_step` 三个阶段可插入自定义逻辑。验证阶段同样复用 `data_dict`，但指标定义和可视化由插件实现：
- evaluator 输出标准 `EvaluationResult`（`metrics/breakdowns/artifacts/meta`）
- visualizer 消费 `EvaluationResult` 写 TensorBoard
- report writer 持久化验证报告 JSON

## 文件位置

- 核心逻辑: `train/trainer.py`, `train/loop.py`, `train/distributed.py`
- 验证报告: `train/validation_report.py`
- Hook 执行链: `hooks/hook_runner.py`
- Checkpoint 后端: `interfaces/checkpoint_io.py`
- 验证接口: `interfaces/evaluator.py`, `interfaces/visualizer.py`

## 依赖关系

**内部依赖**:
- [注册与插件加载系统](registry-and-plugin-loading.md) - 通过 `build_dataset` 和 `build_module` 构建实例
- [任务实现系统](task-implementations.md) - 实际提供可构建的 dataset/model/loss 类型

**外部依赖**:
- `torch` - 训练、自动混合精度与 DDP
- `numpy` - 随机种子控制

## 配置

**配置文件**:
- `configs/*.yaml` - 每个任务的训练参数、模型与数据配置

关键字段：
- `train.max_epochs`, `train.max_steps`
- `train.amp`, `train.gradient_clip_norm`
- `train.distributed`, `train.num_workers`
- `train.log_interval`, `train.save_interval`, `train.output_dir`
- `validate.enabled`, `validate.val_interval_steps`, `validate.val_interval_epochs`, `validate.max_val_batches`
- `evaluation.name`（选择 evaluator 插件）
- `visualization.name`（选择 visualizer 插件）
- `tensorboard.*`（visualizer 读取的写入策略）

## 接口（API）

公开调用面以 `Trainer(config).train()` 为主。输入是 `DictConfig`，内部根据配置构建完整训练图。

验证阶段对外可扩展面：
- evaluator 需实现 `reset/update/finalize`
- visualizer 需实现 `log(result, context, writer)`

## 错误处理

- 当 loss 无法从 loss module / `_loss_dict` / `total_loss` 任一来源获得时抛出异常。
- 当 optimizer 类型不受支持时抛出 `ValueError`。
- 当 `validate.enabled=true` 但未配置 `evaluation.name` 时抛出异常。
- 分布式清理逻辑在 `finally` 中执行，降低异常后残留进程组风险。

## 性能特征

- 支持 AMP（CUDA）与可选梯度裁剪。
- DDP 配合 `DistributedSampler` 支持多卡吞吐扩展。
- checkpoint 仅 rank 0 写入，减少并发 I/O 冲突。
- 验证指标可通过 evaluator 在 `finalize` 阶段进行 DDP all-reduce 聚合。

## 测试

测试文件: `scripts/smoke_test.py`

覆盖范围: 覆盖 6 个配置与 1 个 DDP 样例（以 smoke 为主，非细粒度单测）

## 相关系统

- [注册与插件加载系统](registry-and-plugin-loading.md)
- [任务实现系统](task-implementations.md)

## 相关流程

- [单进程训练流程](../traces/single-process-training-flow.md)
- [分布式训练流程](../traces/distributed-training-flow.md)
