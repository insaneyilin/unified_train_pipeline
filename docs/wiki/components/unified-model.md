# 统一模型组件（UnifiedModel）

**位置**: `core/unified_model.py`

## 职责

`UnifiedModel` 将配置中的多个子模块组装成顺序执行流水线，在同一个 `data_dict` 上完成增量计算。

## 接口

**导出内容**:
- `class UnifiedModel(BaseModule)` - 统一模型容器

**公开 API**:
```python
class UnifiedModel(BaseModule):
    def __init__(self, module_config: DictConfig, global_config: DictConfig)
    def forward(self, data_dict: Dict[str, Any]) -> Dict[str, Any]
```

## 实现说明

**关键逻辑**:
- 从 `module_config.submodules` 动态构建 `torch.nn.ModuleDict`
- 遍历子模块顺序执行：`data_dict = submodule(data_dict)`
- 推理模式可向下游 `BaseModule` 子模块传播 `is_inference_mode`

**核心机制**:
- 本质为配置驱动的组合模式（composition over inheritance）

## 使用示例

```yaml
model:
  name: UnifiedModel
  submodules:
    backbone:
      name: MnistMlpBackbone
```

## 依赖关系

**依赖**:
- `registry/module_register.py` 的 `build_module`
- `core/base_module.py` 的 `BaseModule` 与 `DataContract`

**被调用方**:
- [Trainer](trainer.md) - 训练循环中执行前向

## 错误处理

- 若缺少 `submodules` 配置会触发断言失败。
- 子模块构建失败会通过 `build_module` 抛出可读错误。

## 测试

**测试文件**: `scripts/smoke_test.py`

**测试覆盖**:
- [x] 分类任务子模块组合
- [x] 检测任务子模块组合
- [ ] 复杂多子模块顺序覆盖

## 相关组件

- [Trainer](trainer.md)
- [DictConfig](dict-config.md)
