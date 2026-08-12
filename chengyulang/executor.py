"""Compile and execute translated ChengyuLang source."""

from __future__ import annotations

import sys
from copy import deepcopy
from dataclasses import dataclass
from functools import partial
from typing import Any, TextIO

from .catalog import 成语词典, 成语词库
from .runtime import 调用成语, 触发彩蛋
from .translator import 翻译, 翻译错误


@dataclass(slots=True)
class 执行结果:
    """Structured result returned even when user code raises an exception."""

    成功: bool
    译文: str
    命名空间: dict[str, Any]
    异常: BaseException | None = None

    @property
    def success(self) -> bool:
        return self.成功

    @property
    def translated_source(self) -> str:
        return self.译文

    @property
    def namespace(self) -> dict[str, Any]:
        return self.命名空间

    @property
    def error(self) -> BaseException | None:
        return self.异常


def _成语函数表(词典: 成语词库) -> dict[str, Any]:
    return {
        名称: partial(调用成语, 名称, _词典=词典)
        for 名称 in 词典
    }


def _公开命名空间(命名空间: dict[str, Any]) -> dict[str, Any]:
    内部名称 = {"__chengyu_functions__", "__chengyu_egg__", "__builtins__"}
    return {键: 值 for 键, 值 in 命名空间.items() if 键 not in 内部名称}


def 执行(
    源码: str,
    *,
    词典: 成语词库 | None = None,
    初始命名空间: dict[str, Any] | None = None,
    显示译文: bool = False,
    错误输出: TextIO | None = None,
) -> 执行结果:
    """Translate and execute trusted ChengyuLang source with friendly errors."""

    当前词典 = deepcopy(成语词典 if 词典 is None else 词典)
    错误流 = sys.stderr if 错误输出 is None else 错误输出
    译文 = ""
    命名空间 = dict(初始命名空间 or {})
    命名空间["__chengyu_functions__"] = _成语函数表(当前词典)
    命名空间["__chengyu_egg__"] = partial(触发彩蛋, _词典=当前词典)

    try:
        译文 = 翻译(源码, 当前词典)
        if 显示译文:
            print("—— Python 译文 ——")
            print(译文)
        字节码 = compile(译文, "<成语语>", "exec")
        exec(字节码, 命名空间)
    except (翻译错误, SyntaxError) as 错误:
        行号 = getattr(错误, "lineno", None)
        位置 = f"（第 {行号} 行）" if 行号 else ""
        print(
            f"💥 句法不通，请重新断句！{位置}{错误}",
            file=错误流,
        )
        return 执行结果(False, 译文, _公开命名空间(命名空间), 错误)
    except Exception as 错误:
        print(f"💥 成语运行时出错：{错误}", file=错误流)
        return 执行结果(False, 译文, _公开命名空间(命名空间), 错误)

    return 执行结果(True, 译文, _公开命名空间(命名空间))


# English aliases.
ExecutionResult = 执行结果
execute = 执行

