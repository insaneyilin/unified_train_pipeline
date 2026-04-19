# 总览

`unified_train_pipeline` 是一个配置驱动的深度学习模型训练框架。它通过统一的 `data_dict` 在数据加载、模型前向、损失计算与 hook 阶段之间传递状态，并通过 registry 机制实现 dataset/model/loss/evaluator/visualizer 的解耦构建，支持单机与 DDP 分布式训练。

## 架构

整体执行路径为：`scripts/train.py` 解析配置并触发 `tasks` 自动注册，然后创建 `Trainer` 完成数据集、模型、损失、evaluator、visualizer 与优化器构建，最后进入 epoch/batch 训练循环。模型层默认由 `UnifiedModel` 串联子模块，loss 可由独立模块计算或从模型输出读取；验证阶段通过 evaluator 产出结构化 `EvaluationResult`，再由 visualizer 和 report writer 消费；checkpoint 通过 `CheckpointIO` 抽象保存（当前实现为本地文件系统）。

## 关键系统

- **训练编排系统**: 训练主循环、设备管理、AMP、梯度裁剪、日志与 checkpoint（[文档](systems/training-orchestration.md)）
- **注册与插件加载系统**: 模块/数据集注册与任务自动导入机制（[文档](systems/registry-and-plugin-loading.md)）
- **任务实现系统**: MNIST、CIFAR10、COCO128 的数据集/模型/损失实现（[文档](systems/task-implementations.md)）

## 技术栈

**语言**: Python

**框架**: PyTorch, torchvision, PyYAML

**构建与运行工具**: Python 模块执行（`python -m`, `torchrun`）

**基础设施**: 本地文件系统 checkpoint，可选 `torch.distributed` 进程组

## 目录结构

```text
unified_train_pipeline/
├── core/        - 配置系统与基础模块抽象（DictConfig, BaseModule, UnifiedModel）
├── registry/    - dataset/model/evaluator/visualizer 构建注册器与自动导入工具
├── hooks/       - hook 协议和执行链
├── interfaces/  - checkpoint、预测格式、evaluator/visualizer 抽象接口
├── train/       - Trainer、训练 loop 工具、DDP 工具、验证报告写入
├── tasks/       - 各任务的 dataset/model/loss/evaluator/visualizer 插件实现
├── configs/     - 可运行 YAML 配置样例
└── scripts/     - 入口脚本（train、smoke_test）
```

## 快速开始

**入口文件**:
- 训练主入口: `scripts/train.py`
- Smoke test 入口: `scripts/smoke_test.py`
- 分布式入口: `torchrun --nproc_per_node=2 -m scripts.train --config <config> --distributed`

**关键配置**:
- 训练示例配置: `configs/*.yaml`
- 核心配置对象: `core/dict_config.py`

## 设计模式

- Registry + decorator 注册（`MODULE_REGISTER`, `DATASET_REGISTER`, `EVALUATOR_REGISTER`, `VISUALIZER_REGISTER`）
- 共享可变 `data_dict` 流水线
- 模板方法模式（`BaseModule.forward` + `_forward_impl`）
- 配置驱动组合（`UnifiedModel.submodules`）
- 评测结果标准化（`EvaluationResult`）与可视化/报告分层

## 相关文档

- [训练编排系统](systems/training-orchestration.md)
- [注册与插件加载系统](systems/registry-and-plugin-loading.md)
- [任务实现系统](systems/task-implementations.md)
- [单进程训练流程](traces/single-process-training-flow.md)
- [分布式训练流程](traces/distributed-training-flow.md)
