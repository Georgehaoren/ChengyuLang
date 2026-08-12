"""Command-line interface for ChengyuLang."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from .catalog import 合并词库, 词库加载
from .executor import 执行
from .translator import 翻译


def _读取源码(路径: str) -> str:
    if 路径 == "-":
        return sys.stdin.read()
    return Path(路径).read_text(encoding="utf-8")


def _读取词库(路径: str | None):
    默认词库 = 词库加载()
    return 合并词库(默认词库, 词库加载(路径)) if 路径 else 默认词库


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
    子命令 = 解析器.add_subparsers(dest="command", required=True)

    翻译命令 = 子命令.add_parser(
        "translate",
        help="将 .cy 源码翻译为 Python",
    )
    翻译命令.add_argument(
        "source",
        help="源码文件；使用 - 从标准输入读取",
    )
    翻译命令.add_argument("-o", "--output", help="输出 .py 文件")
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
        help="先显示译文",
    )
    执行命令.add_argument("--catalog", help="用于扩展或覆盖的 JSON 词库")

    词库命令 = 子命令.add_parser("catalog", help="检查并列出 JSON 词库")
    词库命令.add_argument("--catalog", help="用于扩展或覆盖的 JSON 词库")

    子命令.add_parser("demo", help="运行内置演示")
    return 解析器


def main(argv: Sequence[str] | None = None) -> int:
    参数 = _构建解析器().parse_args(argv)

    if 参数.command == "demo":
        return _演示()

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
