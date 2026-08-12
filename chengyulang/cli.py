"""Command-line interface for ChengyuLang."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence, TextIO

from .catalog import 合并词库, 词库加载
from .compiler import (
    编译文件,
    编译源码,
    编译结果,
    写入编译产物,
)
from .diagnostics import 编译诊断, 编译阶段, 渲染诊断
from .executor import 执行
from .translator import 翻译
from .version import __version__


def _读取源码(路径: str) -> str:
    if 路径 == "-":
        return sys.stdin.read()
    return Path(路径).read_text(encoding="utf-8-sig")


def _读取词库(路径: str | None):
    默认词库 = 词库加载()
    return 合并词库(默认词库, 词库加载(路径)) if 路径 else 默认词库


def _添加通用编译参数(解析器: argparse.ArgumentParser) -> None:
    解析器.add_argument(
        "source",
        help="源码文件；使用 - 从标准输入读取",
    )
    解析器.add_argument("--catalog", help="用于扩展或覆盖的 JSON 词库")
    解析器.add_argument(
        "--show-stages",
        action="store_true",
        help="显示读取、翻译、检查、生成和写入阶段",
    )
    解析器.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 输出结构化编译结果",
    )
    解析器.add_argument(
        "--quiet",
        action="store_true",
        help="成功时不显示摘要",
    )


def _演示() -> int:
    演示片段 = [
        ("连写逻辑", '结果 = 色令智昏(3 > 1)\n列(结果)'),
        ("遍历结构", '数 之于 [1, 2, 3]:\n    列(数)'),
        (
            "条件结构",
            '甲 = 5\n乙 = 3\n若 甲 > 乙:\n    列("大")\n否则:\n    列("小")',
        ),
        ("随机乱码", '列(不知所云(12))'),
        ("空格彩蛋（预期中断）", "色 令 智 昏"),
    ]
    for 标题, 源码 in 演示片段:
        print(f"\n=== {标题} ===")
        print(源码)
        执行(源码)
    return 0


def _构建解析器() -> argparse.ArgumentParser:
    解析器 = argparse.ArgumentParser(
        prog="chengyulang",
        description="成语语：空格一断，语义突变。",
    )
    解析器.add_argument("--version", action="version", version=__version__)
    子命令 = 解析器.add_subparsers(dest="command", required=True)

    编译命令 = 子命令.add_parser(
        "compile",
        help="将 .cy 编译为可直接运行的 Python 文件",
    )
    _添加通用编译参数(编译命令)
    输出组 = 编译命令.add_mutually_exclusive_group()
    输出组.add_argument("-o", "--output", help="指定输出 .py 文件")
    输出组.add_argument(
        "--stdout",
        action="store_true",
        help="将生成的 Python 输出至标准输出",
    )
    编译命令.add_argument(
        "--check",
        action="store_true",
        help="只检查，不写入文件（等同 check 子命令）",
    )
    编译命令.add_argument(
        "--force",
        action="store_true",
        help="覆盖已经存在的输出文件",
    )

    检查命令 = 子命令.add_parser(
        "check",
        help="检查源码但不生成文件",
    )
    _添加通用编译参数(检查命令)

    翻译命令 = 子命令.add_parser(
        "translate",
        help="输出供内部调试使用的 Python 译文",
    )
    翻译命令.add_argument(
        "source",
        help="源码文件；使用 - 从标准输入读取",
    )
    翻译命令.add_argument("-o", "--output", help="输出内部译文")
    翻译命令.add_argument("--catalog", help="用于扩展或覆盖的 JSON 词库")

    执行命令 = 子命令.add_parser(
        "run",
        help="翻译并执行可信的 .cy 源码",
    )
    执行命令.add_argument(
        "source",
        help="源码文件；使用 - 从标准输入读取",
    )
    执行命令.add_argument(
        "--show-python",
        action="store_true",
        help="先显示内部 Python 译文",
    )
    执行命令.add_argument("--catalog", help="用于扩展或覆盖的 JSON 词库")

    词库命令 = 子命令.add_parser("catalog", help="检查并列出 JSON 词库")
    词库命令.add_argument("--catalog", help="用于扩展或覆盖的 JSON 词库")

    子命令.add_parser("demo", help="运行内置演示")
    return 解析器


def _拒绝参数组合(结果: 编译结果, 消息: str) -> 编译结果:
    结果.诊断信息.append(
        编译诊断(
            代码="CY4000",
            级别="error",
            阶段="cli",
            消息=消息,
            文件名=结果.文件名,
        )
    )
    结果.阶段.append(编译阶段("命令行", "failed", 消息))
    return 结果


def _控制台编译(参数: argparse.Namespace, 词典) -> 编译结果:
    仅检查 = 参数.command == "check" or getattr(参数, "check", False)
    源码来自标准输入 = 参数.source == "-"

    if 源码来自标准输入:
        源码 = sys.stdin.read()
        结果 = 编译源码(源码, 文件名="<标准输入>", 词典=词典)
        结果.阶段.insert(0, 编译阶段("读取", "passed", "标准输入"))
        if 仅检查:
            结果.阶段.append(编译阶段("写入", "skipped", "仅检查模式"))
            return 结果
        if 参数.stdout:
            return 结果
        if 参数.output:
            return 写入编译产物(结果, 参数.output, 覆盖=参数.force)
        return _拒绝参数组合(
            结果,
            "从标准输入编译时必须指定 --stdout、--output 或 --check。",
        )

    if 仅检查 or getattr(参数, "stdout", False):
        return 编译文件(参数.source, 词典=词典, 仅检查=True)
    return 编译文件(
        参数.source,
        参数.output,
        词典=词典,
        覆盖=参数.force,
    )


def _打印编译阶段(结果: 编译结果, 文件: TextIO) -> None:
    状态图标 = {"passed": "✓", "failed": "✗", "skipped": "–"}
    for 索引, 阶段 in enumerate(结果.阶段, start=1):
        图标 = 状态图标[阶段.状态]
        进度 = f"[{索引}/{len(结果.阶段)}]"
        print(
            f"{进度} {图标} {阶段.名称}：{阶段.详情}",
            file=文件,
        )


def _打印编译结果(
    结果: 编译结果,
    *,
    显示阶段: bool,
    静默: bool,
    状态输出: TextIO = sys.stdout,
) -> None:
    if 显示阶段:
        _打印编译阶段(结果, 状态输出)
    for 诊断 in 结果.诊断信息:
        print(渲染诊断(诊断), file=sys.stderr)

    if 静默:
        return
    if 结果.成功:
        动作 = "检查通过"
        if 结果.已写入 and 结果.输出路径 is not None:
            动作 = f"编译完成：{结果.输出路径}"
        统计 = f"{结果.错误数} 个错误，{结果.警告数} 个警告"
        print(
            f"✅ {动作}：{统计}",
            file=状态输出,
        )
    else:
        统计 = f"{结果.错误数} 个错误，{结果.警告数} 个警告"
        print(
            f"编译失败：{统计}",
            file=sys.stderr,
        )


def _编译退出码(结果: 编译结果) -> int:
    if 结果.成功:
        return 0
    if any(诊断.代码 == "CY3000" for 诊断 in 结果.诊断信息):
        return 2
    return 1


def _运行编译命令(参数: argparse.Namespace) -> int:
    try:
        词典 = _读取词库(参数.catalog)
    except (OSError, ValueError) as 错误:
        if 参数.json:
            print(
                json.dumps(
                    {
                        "success": False,
                        "error_count": 1,
                        "diagnostics": [
                            {
                                "code": "CY3004",
                                "level": "error",
                                "stage": "catalog",
                                "message": str(错误),
                            }
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            print(f"💥 CY3004 无法加载词库：{错误}", file=sys.stderr)
        return 2

    if 参数.command == "compile":
        if 参数.json and 参数.stdout:
            空结果 = 编译结果(文件名=参数.source, 词条总数=len(词典))
            结果 = _拒绝参数组合(
                空结果,
                "--json 与 --stdout 不可同时使用。",
            )
        elif 参数.check and (参数.output or 参数.stdout):
            空结果 = 编译结果(文件名=参数.source, 词条总数=len(词典))
            结果 = _拒绝参数组合(
                空结果,
                "--check 不可与 --output 或 --stdout 同时使用。",
            )
        else:
            结果 = _控制台编译(参数, 词典)
    else:
        结果 = _控制台编译(参数, 词典)

    if 参数.json:
        print(json.dumps(结果.转为字典(), ensure_ascii=False, indent=2))
        return _编译退出码(结果)

    if 参数.command == "compile" and 参数.stdout and 结果.成功:
        print(
            结果.Python源码,
            end="" if 结果.Python源码.endswith("\n") else "\n",
        )
        if 参数.show_stages:
            _打印编译阶段(结果, sys.stderr)
        return 0

    _打印编译结果(
        结果,
        显示阶段=参数.show_stages,
        静默=参数.quiet,
    )
    return _编译退出码(结果)


def main(argv: Sequence[str] | None = None) -> int:
    参数 = _构建解析器().parse_args(argv)

    if 参数.command == "demo":
        return _演示()
    if 参数.command in {"compile", "check"}:
        try:
            return _运行编译命令(参数)
        except Exception as 错误:
            print(f"💥 CY9000 编译器内部错误：{错误}", file=sys.stderr)
            return 3

    try:
        词典 = _读取词库(getattr(参数, "catalog", None))
        if 参数.command == "catalog":
            print(f"词条总数：{len(词典)}")
            for 名称, 条目 in 词典.items():
                print(f"{名称}\t{条目['category']}\t{条目['py']}")
            return 0

        源码 = _读取源码(参数.source)
        if 参数.command == "translate":
            译文 = 翻译(源码, 词典)
            if 参数.output:
                Path(参数.output).write_text(译文, encoding="utf-8")
            else:
                print(译文, end="" if 译文.endswith("\n") else "\n")
            return 0

        结果 = 执行(源码, 词典=词典, 显示译文=参数.show_python)
        return 0 if 结果.成功 else 1
    except (OSError, ValueError, SyntaxError) as 错误:
        print(f"💥 无法处理：{错误}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
