# 配置对象组件（DictConfig）

**位置**: `core/dict_config.py`

## 职责

`DictConfig` 提供轻量配置容器，支持 YAML 加载、嵌套合并和 freeze/unfreeze，作为全框架统一配置对象。

## 接口

**导出内容**:
- `class DictConfig(dict)` - 字典增强配置类

**公开 API**:
```python
class DictConfig(dict):
    def add(self, data=None, **kwargs) -> None
    def to_dict(self) -> dict
    def freeze(self) -> None
    def unfreeze(self) -> None
```

## 实现说明

**关键逻辑**:
- 当输入为 `.yaml` 路径时自动解析并加载为字典
- 嵌套字典自动包装为 `DictConfig`
- `freeze()` 后拒绝写入，防止运行时配置漂移

**状态管理**:
- `_freeze` 标志位控制可写状态

## 使用示例

```python
cfg = DictConfig("configs/mnist_mlp.yaml")
cfg.unfreeze()
cfg.add({"train": {"distributed": True}})
cfg.freeze()
```

## 依赖关系

**依赖**:
- `yaml.safe_load` 读取 YAML

**被调用方**:
- `scripts/train.py` - CLI 加载配置
- `train/trainer.py` - 读取训练参数
- `core/base_module.py` - 模块配置读取

## 错误处理

- Python 版本低于 3.7 时会在初始化时直接报错。
- 已有嵌套配置节点被非字典值覆盖时抛 `TypeError`。

## 测试

**测试文件**: `scripts/smoke_test.py`（间接覆盖）

**测试覆盖**:
- [x] YAML 加载路径
- [x] 嵌套配置读取
- [ ] 独立单测覆盖 freeze 边界条件

## 相关组件

- [Trainer](trainer.md)
- [UnifiedModel](unified-model.md)
