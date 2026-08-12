"""Load and validate ChengyuLang idiom catalogs from JSON."""

from __future__ import annotations

import json
from copy import deepcopy
from importlib import resources
from pathlib import Path
from typing import Any, Mapping, TypeAlias

成语条目: TypeAlias = dict[str, Any]
成语词库: TypeAlias = dict[str, 成语条目]

_必需字段 = ("category", "py", "egg", "runtime")


class 词库错误(ValueError):
    """Raised when a JSON idiom catalog does not match the expected shape."""


def _读取_json(路径: str | Path | None = None) -> Mapping[str, Any]:
    if 路径 is None:
        数据文件 = resources.files("chengyulang.data").joinpath("idioms.json")
        with 数据文件.open("r", encoding="utf-8") as 文件:
            return json.load(文件)

    with Path(路径).expanduser().open("r", encoding="utf-8") as 文件:
        return json.load(文件)


def _提取词条(原始数据: Mapping[str, Any]) -> Mapping[str, Any]:
    """Accept the bundled envelope or a direct ``{idiom: entry}`` mapping."""

    词条 = 原始数据.get("idioms", 原始数据)
    if not isinstance(词条, Mapping) or not 词条:
        raise 词库错误("词库必须包含非空的 idioms 对象。")
    return 词条


def _校验词条(名称: object, 条目: object) -> 成语条目:
    if not isinstance(名称, str) or not 名称.strip():
        raise 词库错误("成语名称必须是非空字符串。")
    if any(字符.isspace() for 字符 in 名称):
        raise 词库错误(f"成语名称不可含空白字符：{名称!r}")
    if not isinstance(条目, Mapping):
        raise 词库错误(f"{名称} 的词条必须是 JSON 对象。")

    缺失字段 = [字段 for 字段 in _必需字段 if 字段 not in 条目]
    if 缺失字段:
        缺失 = "、".join(缺失字段)
        raise 词库错误(f"{名称} 缺少必需字段：{缺失}")

    for 字段 in _必需字段:
        if not isinstance(条目[字段], str) or not 条目[字段].strip():
            raise 词库错误(f"{名称}.{字段} 必须是非空字符串。")

    return deepcopy(dict(条目))


def 校验词库(词条: Mapping[str, Any]) -> 成语词库:
    """Validate and copy an idiom mapping."""

    if not isinstance(词条, Mapping) or not 词条:
        raise 词库错误("词库必须是非空映射。")
    return {名称: _校验词条(名称, 条目) for 名称, 条目 in 词条.items()}


def 词库加载(
    路径: str | Path | None = None,
    扩展: Mapping[str, Mapping[str, Any]] | None = None,
) -> 成语词库:
    """Load a catalog and optionally merge an in-memory extension mapping."""

    原始数据 = _读取_json(路径)
    词典 = 校验词库(_提取词条(原始数据))
    if 扩展:
        词典.update(校验词库(扩展))
    return 词典


def 合并词库(*词库: Mapping[str, Mapping[str, Any]]) -> 成语词库:
    """Merge validated catalogs from left to right."""

    合并结果: 成语词库 = {}
    for 当前词库 in 词库:
        合并结果.update(校验词库(当前词库))
    if not 合并结果:
        raise 词库错误("至少需要提供一个非空词库。")
    return 合并结果


# A mutable default snapshot keeps the original ``成语词典.update(...)`` idea.
# ``词库加载()`` still returns a fresh copy when isolation is preferred.
成语词典: 成语词库 = 词库加载()

# English aliases for users who prefer conventional Python identifiers.
CatalogError = 词库错误
load_catalog = 词库加载
validate_catalog = 校验词库
merge_catalogs = 合并词库

