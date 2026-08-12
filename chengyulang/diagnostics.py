"""Structured compiler diagnostics and console rendering helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypeAlias

诊断级别: TypeAlias = Literal["info", "warning", "error"]


@dataclass(frozen=True, slots=True)
class 编译诊断:
    """A stable, serializable diagnostic produced by the compiler."""

    代码: str
    级别: 诊断级别
    阶段: str
    消息: str
    文件名: str = "<成语语>"
    行号: int | None = None
    列号: int | None = None
    源码行: str | None = None

    def 转为字典(self) -> dict[str, object]:
        return {
            "code": self.代码,
            "level": self.级别,
            "stage": self.阶段,
            "message": self.消息,
            "filename": self.文件名,
            "line": self.行号,
            "column": self.列号,
            "source_line": self.源码行,
        }

    def render(self) -> str:
        return 渲染诊断(self)

    def to_dict(self) -> dict[str, object]:
        return self.转为字典()


@dataclass(frozen=True, slots=True)
class 编译阶段:
    """One inspectable step in a compilation pipeline."""

    名称: str
    状态: Literal["passed", "failed", "skipped"]
    详情: str

    def 转为字典(self) -> dict[str, str]:
        return {
            "name": self.名称,
            "status": self.状态,
            "detail": self.详情,
        }

    def to_dict(self) -> dict[str, str]:
        return self.转为字典()


def 渲染诊断(诊断: 编译诊断) -> str:
    """Render a readable diagnostic with an optional source caret."""

    图标 = {"info": "ℹ️", "warning": "⚠️", "error": "💥"}[诊断.级别]
    标题 = f"{图标} {诊断.代码} {诊断.消息}"
    if 诊断.行号 is None:
        return 标题

    位置 = f"{诊断.文件名}:{诊断.行号}"
    if 诊断.列号 is not None:
        位置 += f":{诊断.列号}"
    if 诊断.源码行 is None:
        return f"{标题}\n\n  {位置}"

    行号文本 = str(诊断.行号)
    前缀 = f"  {行号文本} │ "
    列号 = max(1, 诊断.列号 or 1)
    指针缩进 = " " * (len(行号文本) + 5 + 列号 - 1)
    return (
        f"{标题}\n\n"
        f"  {位置}\n\n"
        f"{前缀}{诊断.源码行}\n"
        f"{指针缩进}^"
    )


# English aliases.
Diagnostic = 编译诊断
CompilationStage = 编译阶段
render_diagnostic = 渲染诊断
