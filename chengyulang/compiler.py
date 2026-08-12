"""Console-oriented ChengyuLang-to-Python compilation pipeline."""

from __future__ import annotations

import ast
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .bootstrap import 生成Python源码
from .catalog import 成语词典, 成语词库, 校验词库
from .diagnostics import 编译诊断, 编译阶段
from .runtime import 已注册实现
from .translator import (
    成语命中,
    分析并翻译,
    结构命中,
    翻译错误,
)


@dataclass(slots=True)
class 编译结果:
    """Complete, serializable output of one compilation attempt."""

    文件名: str
    词条总数: int
    内部译文: str = ""
    Python源码: str = ""
    输出路径: Path | None = None
    已写入: bool = False
    成语命中列表: tuple[成语命中, ...] = ()
    结构命中列表: tuple[结构命中, ...] = ()
    诊断信息: list[编译诊断] = field(default_factory=list)
    阶段: list[编译阶段] = field(default_factory=list)

    @property
    def 成功(self) -> bool:
        return not any(诊断.级别 == "error" for 诊断 in self.诊断信息)

    @property
    def 错误数(self) -> int:
        return sum(诊断.级别 == "error" for 诊断 in self.诊断信息)

    @property
    def 警告数(self) -> int:
        return sum(诊断.级别 == "warning" for 诊断 in self.诊断信息)

    @property
    def success(self) -> bool:
        return self.成功

    @property
    def translated_source(self) -> str:
        return self.内部译文

    @property
    def python_source(self) -> str:
        return self.Python源码

    @property
    def diagnostics(self) -> list[编译诊断]:
        return self.诊断信息

    def 转为字典(self) -> dict[str, Any]:
        return {
            "success": self.成功,
            "source": self.文件名,
            "output": str(self.输出路径) if self.输出路径 else None,
            "written": self.已写入,
            "catalog_size": self.词条总数,
            "error_count": self.错误数,
            "warning_count": self.警告数,
            "stages": [阶段.转为字典() for 阶段 in self.阶段],
            "idiom_hits": [
                命中.转为字典() for 命中 in self.成语命中列表
            ],
            "structure_hits": [
                命中.转为字典() for 命中 in self.结构命中列表
            ],
            "diagnostics": [
                诊断.转为字典() for 诊断 in self.诊断信息
            ],
            "translated_source": self.内部译文,
            "python_source": self.Python源码,
        }

    def to_dict(self) -> dict[str, Any]:
        return self.转为字典()


def _源码行(源码: str, 行号: int | None) -> str | None:
    if 行号 is None:
        return None
    行 = 源码.splitlines()
    if 1 <= 行号 <= len(行):
        return 行[行号 - 1]
    return None


def _翻译错误位置(错误: BaseException) -> tuple[int | None, int | None]:
    行号 = getattr(错误, "lineno", None)
    列号 = getattr(错误, "offset", None)
    原因 = getattr(错误, "__cause__", None)
    if 行号 is None and 原因 is not None:
        if len(原因.args) > 1 and isinstance(原因.args[1], tuple):
            行号, 原始列号 = 原因.args[1][:2]
            列号 = int(原始列号) + 1
    return 行号, 列号


def _语法诊断(
    错误: SyntaxError,
    源码: str,
    文件名: str,
    *,
    代码: str = "CY1002",
) -> 编译诊断:
    行号 = 错误.lineno
    列号 = 错误.offset
    消息 = 错误.msg or str(错误)
    return 编译诊断(
        代码=代码,
        级别="error",
        阶段="syntax",
        消息=f"句法不通，请重新断句！{消息}",
        文件名=文件名,
        行号=行号,
        列号=列号,
        源码行=_源码行(源码, 行号),
    )


def 编译源码(
    源码: str,
    *,
    文件名: str = "<成语语>",
    词典: 成语词库 | None = None,
) -> 编译结果:
    """Compile source into deterministic, directly runnable Python text."""

    if not isinstance(源码, str):
        raise TypeError("源码必须是字符串。")
    当前词典 = 校验词库(成语词典 if 词典 is None else 词典)
    结果 = 编译结果(文件名=文件名, 词条总数=len(当前词典))

    try:
        翻译产物 = 分析并翻译(源码, 当前词典)
    except 翻译错误 as 错误:
        行号, 列号 = _翻译错误位置(错误)
        结果.诊断信息.append(
            编译诊断(
                代码="CY1001",
                级别="error",
                阶段="translation",
                消息=str(错误),
                文件名=文件名,
                行号=行号,
                列号=列号,
                源码行=_源码行(源码, 行号),
            )
        )
        结果.阶段.append(
            编译阶段("翻译", "failed", "无法完成 Token 翻译")
        )
        return 结果

    结果.内部译文 = 翻译产物.Python源码
    结果.成语命中列表 = 翻译产物.成语命中列表
    结果.结构命中列表 = 翻译产物.结构命中列表
    结果.阶段.append(
        编译阶段(
            "翻译",
            "passed",
            (
                f"识别 {len(结果.成语命中列表)} 处成语、"
                f"{len(结果.结构命中列表)} 处文言结构"
            ),
        )
    )

    已注册 = 已注册实现()
    缺失运行时: set[tuple[str, str, int, int]] = set()
    for 命中 in 结果.成语命中列表:
        if 命中.模式 != "connected" or 命中.运行时 in 已注册:
            continue
        标识 = (命中.文本, 命中.运行时, 命中.行号, 命中.列号)
        if 标识 in 缺失运行时:
            continue
        缺失运行时.add(标识)
        结果.诊断信息.append(
            编译诊断(
                代码="CY2001",
                级别="error",
                阶段="semantics",
                消息=(
                    f"成语“{命中.文本}”尚未注册运行时实现："
                    f"{命中.运行时}"
                ),
                文件名=文件名,
                行号=命中.行号,
                列号=命中.列号,
                源码行=_源码行(源码, 命中.行号),
            )
        )

    if 缺失运行时:
        结果.阶段.append(
            编译阶段(
                "语义检查",
                "failed",
                f"缺少 {len(缺失运行时)} 个运行时实现",
            )
        )
        return 结果
    结果.阶段.append(
        编译阶段("语义检查", "passed", "所有已使用成语均可调用")
    )

    try:
        ast.parse(结果.内部译文, filename=文件名, mode="exec")
    except SyntaxError as 错误:
        结果.诊断信息.append(_语法诊断(错误, 源码, 文件名))
        结果.阶段.append(
            编译阶段("句法检查", "failed", "Python AST 拒绝译文")
        )
        return 结果
    结果.阶段.append(
        编译阶段("句法检查", "passed", "Python AST 验证通过")
    )

    结果.Python源码 = 生成Python源码(
        源码,
        结果.内部译文,
        当前词典,
        文件名=文件名,
    )
    try:
        ast.parse(结果.Python源码, filename=文件名, mode="exec")
    except SyntaxError as 错误:
        结果.诊断信息.append(
            编译诊断(
                代码="CY9001",
                级别="error",
                阶段="codegen",
                消息=f"编译器生成了无效 Python：{错误.msg}",
                文件名=文件名,
                行号=错误.lineno,
                列号=错误.offset,
            )
        )
        结果.阶段.append(
            编译阶段("代码生成", "failed", "运行时引导无效")
        )
        return 结果

    结果.阶段.append(
        编译阶段("代码生成", "passed", "已生成可运行 Python 源码")
    )
    return 结果


def 默认输出路径(输入路径: str | Path) -> Path:
    """Choose ``name.py`` without ever resolving to the input itself."""

    输入 = Path(输入路径)
    if 输入.suffix.lower() == ".cy":
        return 输入.with_suffix(".py")
    return 输入.with_name(f"{输入.name}.py")


def 写入编译产物(
    结果: 编译结果,
    输出路径: str | Path,
    *,
    覆盖: bool = False,
    输入路径: str | Path | None = None,
) -> 编译结果:
    """Atomically write a successful compilation result."""

    目标 = Path(输出路径)
    结果.输出路径 = 目标
    if not 结果.成功:
        结果.阶段.append(
            编译阶段("写入", "skipped", "编译失败，未写入文件")
        )
        return 结果

    if 输入路径 is not None:
        try:
            if Path(输入路径).resolve() == 目标.resolve():
                结果.诊断信息.append(
                    编译诊断(
                        代码="CY3001",
                        级别="error",
                        阶段="output",
                        消息="输出文件不可与输入源码相同。",
                        文件名=str(输入路径),
                    )
                )
                结果.阶段.append(
                    编译阶段("写入", "failed", "拒绝覆盖输入源码")
                )
                return 结果
        except OSError:
            pass

    if 目标.exists() and not 覆盖:
        结果.诊断信息.append(
            编译诊断(
                代码="CY3002",
                级别="error",
                阶段="output",
                消息=(
                    f"输出文件已存在：{目标}；"
                    "请使用 --force 覆盖。"
                ),
                文件名=str(目标),
            )
        )
        结果.阶段.append(编译阶段("写入", "failed", "输出文件已存在"))
        return 结果

    临时路径: Path | None = None
    try:
        目标.parent.mkdir(parents=True, exist_ok=True)
        文件描述符, 临时文件名 = tempfile.mkstemp(
            prefix=f".{目标.name}.",
            suffix=".tmp",
            dir=目标.parent,
            text=True,
        )
        临时路径 = Path(临时文件名)
        with os.fdopen(文件描述符, "w", encoding="utf-8", newline="\n") as 文件:
            文件.write(结果.Python源码)
            文件.flush()
            os.fsync(文件.fileno())
        os.replace(临时路径, 目标)
    except OSError as 错误:
        结果.诊断信息.append(
            编译诊断(
                代码="CY3003",
                级别="error",
                阶段="output",
                消息=f"无法写入编译产物：{错误}",
                文件名=str(目标),
            )
        )
        结果.阶段.append(
            编译阶段("写入", "failed", "文件系统写入失败")
        )
        return 结果
    finally:
        if 临时路径 is not None and 临时路径.exists():
            try:
                临时路径.unlink()
            except OSError:
                pass

    结果.已写入 = True
    结果.阶段.append(编译阶段("写入", "passed", str(目标)))
    return 结果


def 编译文件(
    输入路径: str | Path,
    输出路径: str | Path | None = None,
    *,
    词典: 成语词库 | None = None,
    覆盖: bool = False,
    仅检查: bool = False,
) -> 编译结果:
    """Read, compile, and optionally write one UTF-8 ChengyuLang file."""

    输入 = Path(输入路径)
    当前词典 = 校验词库(成语词典 if 词典 is None else 词典)
    try:
        源码 = 输入.read_text(encoding="utf-8-sig")
    except OSError as 错误:
        return 编译结果(
            文件名=str(输入),
            词条总数=len(当前词典),
            诊断信息=[
                编译诊断(
                    代码="CY3000",
                    级别="error",
                    阶段="input",
                    消息=f"无法读取源码：{错误}",
                    文件名=str(输入),
                )
            ],
            阶段=[编译阶段("读取", "failed", "无法读取输入文件")],
        )

    源码 = 源码.replace("\r\n", "\n").replace("\r", "\n")
    结果 = 编译源码(源码, 文件名=str(输入), 词典=当前词典)
    结果.阶段.insert(0, 编译阶段("读取", "passed", str(输入)))
    if 仅检查:
        结果.阶段.append(编译阶段("写入", "skipped", "仅检查模式"))
        return 结果

    目标 = (
        Path(输出路径)
        if 输出路径 is not None
        else 默认输出路径(输入)
    )
    return 写入编译产物(结果, 目标, 覆盖=覆盖, 输入路径=输入)


# English aliases.
CompilationResult = 编译结果
compile_source = 编译源码
compile_file = 编译文件
write_compilation = 写入编译产物
default_output_path = 默认输出路径
