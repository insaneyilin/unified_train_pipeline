# 评测与可视化组件（Evaluator / Visualizer）

**位置**:
- `interfaces/evaluator.py`
- `interfaces/visualizer.py`
- `registry/evaluator_register.py`
- `registry/visualizer_register.py`
- `train/validation_report.py`

## 作用

该组件层用于把验证阶段的任务逻辑从 `Trainer` 中解耦：

- `Evaluator` 负责“如何计算评测结果”
- `Visualizer` 负责“如何展示评测结果”
- `ValidationReportWriter` 负责“如何持久化评测结果”

目标是让 `train/trainer.py` 保持调度器角色，避免写死某个任务（如 MNIST 分类）的指标和可视化细节。

## 核心接口

### `EvaluationResult`（`interfaces/evaluator.py`）

统一评测结果结构：

- `metrics: Dict[str, float]`  
  例如 `val/loss`, `val/accuracy`
- `breakdowns: Dict[str, Any]`  
  例如按类别拆分统计
- `artifacts: Dict[str, Any]`  
  例如混淆矩阵、样本可视化缓存
- `meta: Dict[str, Any]`  
  例如 `trigger`, `epoch`, `global_step`, `processed_val_batches`

### `Evaluator` 协议

- `reset(context)`  
  在一次 validate 开始时初始化状态
- `update(data_dict, context)`  
  每个验证 batch 更新统计
- `finalize(context, reduce_fn=None)`  
  输出 `EvaluationResult`；分布式场景可通过 `reduce_fn` 聚合多卡统计

### `Visualizer` 协议

- `log(result, context, writer)`  
  消费 `EvaluationResult`，写入 TensorBoard 或其他可视化后端

## 注册与构建

与 dataset/model/loss 一致，采用注册表模式：

- evaluator 注册：`@EVALUATOR_REGISTER.register_evaluator()`
- visualizer 注册：`@VISUALIZER_REGISTER.register_visualizer()`
- 构建入口：
  - `build_evaluator(name, module_config, global_config)`
  - `build_visualizer(name, module_config, global_config)`

## 在 Trainer 中的调用链

`Trainer._validate_once()` 只负责调度：

1. 遍历 `val_loader` 并做 forward
2. 调 `evaluator.update(...)`
3. 调 `evaluator.finalize(...)` 得到 `EvaluationResult`
4. （rank 0）调 `visualizer.log(...)`
5. （rank 0）调 `ValidationReportWriter.save(...)` 落盘 `val_metrics-<val-id>.json`

这样 `Trainer` 不需要知道“分类 accuracy 怎么算”或“检测 mAP 怎么画”。

## 当前默认实现（MNIST）

### Evaluator

`tasks/mnist/evaluators.py`:

- `MnistClassificationEvaluator`
  - 聚合 `val/loss`, `val/accuracy`
  - 统计 per-digit breakdown
  - 统计 confusion matrix
  - 维护可视化样本 reservoir

### Visualizer

`tasks/mnist/visualizers.py`:

- `MnistTensorBoardVisualizer`
  - 写基础标量：`val/loss`, `val/accuracy`
  - 写 per-digit 标量：`val/digit/*/accuracy`, `val/digit/*/count`
  - 写混淆矩阵图：`val/confusion_matrix/*`
  - 写样本 bucket：`val/random/*`, `val/digit/*`, `val/pred_*`

## 配置方式

以 `configs/mnist_mlp.yaml` 为例：

```yaml
validate:
  enabled: true
  val_interval_steps: 2
  val_interval_epochs: 1

evaluation:
  name: MnistClassificationEvaluator
  num_classes: 10

visualization:
  name: MnistTensorBoardVisualizer
```

说明：

- `validate.*` 负责“何时跑验证”
- `evaluation.name` 负责“用谁算指标”
- `visualization.name` 负责“用谁做可视化”

## 扩展新任务（如检测）最小模板

在 `tasks/<task>/` 下新增：

- `evaluators.py`
- `visualizers.py`

最小步骤：

1. 实现 `class XxxEvaluator(Evaluator)`
2. 实现 `class XxxVisualizer(Visualizer)`
3. 使用注册装饰器注册
4. 在配置中切换 `evaluation.name` 与 `visualization.name`

不需要修改 `train/trainer.py`。

## 设计约束与建议

- `EvaluationResult.metrics` 建议保持扁平、可直接写 scalar（键包含命名空间，如 `val/...`）
- 大对象（图像缓存、矩阵）放 `artifacts`，避免污染 `metrics`
- 任务特定语义放 `breakdowns`，保持 `Trainer` 无任务耦合
- 分布式聚合建议在 `Evaluator.finalize(..., reduce_fn=...)` 内统一完成
- 可视化中与后端耦合（如 TensorBoard tag 规则）应放在 `Visualizer`，不要回流到 `Trainer`
