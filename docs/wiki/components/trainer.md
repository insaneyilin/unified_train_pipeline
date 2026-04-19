# 训练器组件（Trainer）

**位置**: `train/trainer.py`

## 职责

`Trainer` 是训练流程总调度器，负责从配置构建运行时对象并执行优化循环。

## 接口

**导出内容**:
- `class Trainer` - 通用配置驱动训练器（支持可选 DDP）

**公开 API**:
```python
class Trainer:
    def __init__(self, config: DictConfig)
    def train(self) -> None
```

## 实现说明

**关键逻辑**:
- 初始化阶段选择 device（cuda/mps/cpu）并配置 `GradScaler`
- 训练阶段支持 loss 多来源回退逻辑（loss module / `_loss_dict` / `total_loss`)
- 分布式模式自动设置 rank/world 与 DDP 包装

**状态管理**:
- `self.global_step` - 全局步数
- `self.rank/self.world_size` - 分布式上下文

## 使用示例

```python
from unified_train_pipeline.core import DictConfig
from unified_train_pipeline.train import Trainer

cfg = DictConfig("configs/mnist_mlp.yaml")
trainer = Trainer(cfg)
trainer.train()
```

## 依赖关系

**依赖**:
- [UnifiedModel](unified-model.md) - 被 registry 构建后作为 `self.model`
- [DictConfig](dict-config.md) - 承载运行时配置
- `hooks/hook_runner.py` - 执行 hook 链

**被调用方**:
- `scripts/train.py` - CLI 入口直接调用

## 错误处理

- 不支持 optimizer 名称时抛出异常。
- 缺失损失输出时抛出异常，防止静默失败。

## 测试

**测试文件**: `scripts/smoke_test.py`

**测试覆盖**:
- [x] 主路径场景
- [x] 多配置任务运行
- [x] DDP smoke 场景
- [ ] 细粒度单元测试

## 相关组件

- [UnifiedModel](unified-model.md)
- [DictConfig](dict-config.md)
