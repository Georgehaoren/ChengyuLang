"""ChengyuLang public API."""

from .catalog import (
    CatalogError,
    load_catalog,
    merge_catalogs,
    validate_catalog,
    合并词库,
    成语词典,
    校验词库,
    词库加载,
    词库错误,
)
from .executor import ExecutionResult, execute, 执行, 执行结果
from .runtime import (
    ChengyuEggError,
    ChengyuRuntimeError,
    call_idiom,
    register_idiom,
    registered_implementations,
    trigger_egg,
    成语彩蛋错误,
    成语运行时错误,
    已注册实现,
    注册成语,
    触发彩蛋,
    调用成语,
)
from .translator import TranslationError, translate, 翻译, 翻译错误

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "成语词典",
    "词库加载",
    "词库错误",
    "校验词库",
    "合并词库",
    "翻译",
    "翻译错误",
    "执行",
    "执行结果",
    "注册成语",
    "调用成语",
    "触发彩蛋",
    "已注册实现",
    "成语运行时错误",
    "成语彩蛋错误",
    "load_catalog",
    "CatalogError",
    "validate_catalog",
    "merge_catalogs",
    "translate",
    "TranslationError",
    "execute",
    "ExecutionResult",
    "register_idiom",
    "call_idiom",
    "trigger_egg",
    "registered_implementations",
    "ChengyuRuntimeError",
    "ChengyuEggError",
]

