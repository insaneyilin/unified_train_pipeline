"""Task plugins and auto-registration bootstrap."""

from unified_train_pipeline.registry.module_register import auto_import_modules

auto_import_modules(__name__, exclude_patterns=["_test", "__pycache__"])

