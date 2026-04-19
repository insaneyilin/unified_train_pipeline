# 任务实现系统

## 作用

该系统封装具体任务能力（MNIST、CIFAR10、COCO128），提供可注册的数据集、模型子模块与损失模块，是训练框架可落地运行的业务层。

## 组成组件

### MNIST 任务实现（`tasks/mnist/datasets.py`, `tasks/mnist/models.py`）

提供 `MnistDataset`、`MnistMlpBackbone`、`MnistConvBackbone`、`ClassificationCrossEntropyLoss`。

### CIFAR10 任务实现（`tasks/cifar10/datasets.py`, `tasks/cifar10/models.py`）

提供 `Cifar10Dataset`、`CifarResNetBackbone`、`CifarWideResNetBackbone`。

### COCO128 任务实现（`tasks/coco128/datasets.py`, `tasks/coco128/models.py`）

提供 `Coco128DetectionDataset`、`CocoFasterRCNNDetector`、`CocoRetinaNetDetector`、`DetectionLossFromDataDict`，并支持无真实数据时的 synthetic fallback。

## 数据流

```text
Dataset __getitem__/collate_fn
  ↓
包含任务字段的 data_dict
  ↓
任务 backbone/detector 更新 data_dict
  ↓
任务 loss 模块返回 total_loss
  ↓
Trainer 执行优化步骤
```

分类任务通常使用 `image/label/logits`，检测任务通常使用 `image/targets/detector_loss_dict/total_loss`。

## 文件位置

- MNIST: `tasks/mnist/`
- CIFAR10: `tasks/cifar10/`
- COCO128: `tasks/coco128/`
- 任务启动导入: `tasks/__init__.py`
- 示例配置: `configs/*.yaml`

## 依赖关系

**内部依赖**:
- [注册与插件加载系统](registry-and-plugin-loading.md) - 注册并对外可构建
- [训练编排系统](training-orchestration.md) - 被训练主循环调用

**外部依赖**:
- `torch`, `torchvision`, `PIL`

## 配置

关键配置映射：
- `configs/mnist_mlp.yaml` -> `MnistDataset + MnistMlpBackbone + ClassificationCrossEntropyLoss`
- `configs/mnist_conv.yaml` -> `MnistDataset + MnistConvBackbone + ClassificationCrossEntropyLoss`
- `configs/cifar_resnet18.yaml` -> `Cifar10Dataset + CifarResNetBackbone + ClassificationCrossEntropyLoss`
- `configs/cifar_wideresnet.yaml` -> `Cifar10Dataset + CifarWideResNetBackbone + ClassificationCrossEntropyLoss`
- `configs/coco128_fasterrcnn.yaml` -> `Coco128DetectionDataset + CocoFasterRCNNDetector + DetectionLossFromDataDict`
- `configs/coco128_retinanet.yaml` -> `Coco128DetectionDataset + CocoRetinaNetDetector + DetectionLossFromDataDict`

## 接口（API）

面向框架的接口统一为：
- dataset: `__getitem__` 返回 `Dict[str, Any]`
- model/loss: `forward(data_dict)` 返回更新后的 `data_dict` 或 loss 字典

## 错误处理

- 检测数据集中会过滤非法 bbox（宽高过小）。
- COCO 文件缺失时自动切换 synthetic 数据，提升 smoke 运行稳定性。

## 性能特征

- 检测任务模型（Faster R-CNN/RetinaNet）计算成本显著高于分类任务。
- synthetic fallback 可用于快速连通性验证，但不代表真实训练性能。

## 测试

测试文件: `scripts/smoke_test.py`

覆盖范围: 覆盖每个任务至少一个配置的可运行性

## 相关系统

- [训练编排系统](training-orchestration.md)
- [注册与插件加载系统](registry-and-plugin-loading.md)

## 相关流程

- [单进程训练流程](../traces/single-process-training-flow.md)
- [分布式训练流程](../traces/distributed-training-flow.md)
