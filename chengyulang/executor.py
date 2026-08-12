"""Compile and execute translated ChengyuLang source."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any, TextIO

from .catalog import 成语词典, 成语词库
from .compiler import 编译源码
from .diagnostics import 渲染诊断
from .runtime import 构建运行环境


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

    当前词典 = 成语词典 if 词典 is None else 词典
    错误流 = sys.stderr if 错误输出 is None else 错误输出
    编译产物 = 编译源码(源码, 词典=当前词典)
    译文 = 编译产物.内部译文
    命名空间 = dict(初始命名空间 or {})
    函数表, 彩蛋函数 = 构建运行环境(当前词典)
    命名空间["__chengyu_functions__"] = 函数表
    命名空间["__chengyu_egg__"] = 彩蛋函数

    if not 编译产物.成功:
        for 诊断 in 编译产物.诊断信息:
            if 诊断.级别 == "error":
                print(渲染诊断(诊断), file=错误流)
        首个错误 = next(
            诊断 for 诊断 in 编译产物.诊断信息 if 诊断.级别 == "error"
        )
        异常 = SyntaxError(首个错误.消息)
        return 执行结果(False, 译文, _公开命名空间(命名空间), 异常)

    try:
        if 显示译文:
            print("—— Python 译文 ——")
            print(译文)
        字节码 = compile(译文, "<成语语>", "exec")
        exec(字节码, 命名空间)
    except Exception as 错误:
        print(f"💥 成语运行时出错：{错误}", file=错误流)
        return 执行结果(False, 译文, _公开命名空间(命名空间), 错误)

    return 执行结果(True, 译文, _公开命名空间(命名空间))


# English aliases.
ExecutionResult = 执行结果
execute = 执行
