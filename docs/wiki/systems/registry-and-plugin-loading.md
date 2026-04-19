# 注册与插件加载系统

## 作用

该系统负责把“配置中的名字”映射为“可实例化的 Python 类”，并通过任务包自动导入机制确保注册在训练开始前完成。当前注册范围包含 dataset、model/loss、evaluator、visualizer。

## 组成组件

### 模块注册器（`registry/module_register.py`，类名 `ModuleRegister`）

维护 `MODULE_REGISTER`，用于注册并构建 model/loss 相关模块。

**关键方法**:
- `register_module()` - decorator，按类名注册
- `build_module(name, ...)` - 按名字构建模块实例
- `auto_import_modules(package_name, ...)` - 自动导入子模块触发注册副作用

### 数据集注册器（`registry/dataset_register.py`，类名 `DatasetRegister`）

维护 `DATASET_REGISTER`，用于注册并构建 dataset。

### 评测注册器（`registry/evaluator_register.py`，类名 `EvaluatorRegister`）

维护 `EVALUATOR_REGISTER`，用于注册并构建 evaluator。

### 可视化注册器（`registry/visualizer_register.py`，类名 `VisualizerRegister`）

维护 `VISUALIZER_REGISTER`，用于注册并构建 visualizer。

### 任务启动注册 (`tasks/__init__.py`)

导入时调用 `auto_import_modules(__name__)`，递归加载子任务包，从而触发其中 decorator 注册。

## 数据流

```text
scripts/train.py 导入 tasks
  ↓
tasks 自动导入子模块
  ↓
decorator 将类注册进 registries
  ↓
Trainer 根据配置名调用 build_dataset/build_module/build_evaluator/build_visualizer
  ↓
实例化 dataset/model/loss/evaluator/visualizer 对象
```

## 文件位置

- 核心逻辑: `registry/module_register.py`, `registry/dataset_register.py`, `registry/evaluator_register.py`, `registry/visualizer_register.py`
- 启动导入: `tasks/__init__.py`, `tasks/*/__init__.py`
- 调用位置: `train/trainer.py`

## 依赖关系

**内部依赖**:
- [训练编排系统](training-orchestration.md) - 在 runtime 阶段消费注册能力
- [任务实现系统](task-implementations.md) - 提供被注册类

**外部依赖**:
- Python `importlib`, `pkgutil`, `warnings`

## 配置

无独立环境变量。配置依赖主要体现在：
- `dataset.name` 必须匹配某个已注册 dataset 类名
- `model.name` 与 `loss.name` 必须匹配某个已注册 module 类名
- `evaluation.name` 必须匹配某个已注册 evaluator 类名（当启用验证时）
- `visualization.name` 必须匹配某个已注册 visualizer 类名（配置可视化时）

## 接口（API）

- `build_module(name: str, *args, **kwargs)`
- `build_dataset(name: str, *args, **kwargs)`
- `build_evaluator(name: str, *args, **kwargs)`
- `build_visualizer(name: str, *args, **kwargs)`
- `auto_import_modules(package_name: str, package_path: str = None, exclude_patterns = None)`

## 错误处理

- 构建时若名字不存在，抛出 `ValueError` 并列出可用名字。
- 自动导入单个模块失败时记录 `ImportWarning`，避免整个流程立即中断。

## 性能特征

- 注册器查找是字典 O(1)。
- 自动导入发生在启动阶段，开销主要为模块扫描与导入。

## 测试

测试文件: `scripts/smoke_test.py`

覆盖范围: 间接覆盖注册是否完整（通过构建与训练是否可跑通体现）

## 相关系统

- [训练编排系统](training-orchestration.md)
- [任务实现系统](task-implementations.md)

## 相关流程

- [单进程训练流程](../traces/single-process-training-flow.md)
