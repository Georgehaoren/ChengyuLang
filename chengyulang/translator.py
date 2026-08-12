"""Token-aware translation from ChengyuLang source into valid Python."""

from __future__ import annotations

import io
import token
import tokenize
from copy import deepcopy
from dataclasses import dataclass
from typing import Iterable, Literal, TypeAlias

from .catalog import 成语词典, 成语词库


class 翻译错误(SyntaxError):
    """Raised when source cannot be tokenized for translation."""


成语模式: TypeAlias = Literal["connected", "spaced"]


@dataclass(frozen=True, slots=True)
class 成语命中:
    """A connected call or spaced Easter egg found in source."""

    文本: str
    模式: 成语模式
    运行时: str
    行号: int
    列号: int
    结束行号: int
    结束列号: int

    def 转为字典(self) -> dict[str, object]:
        return {
            "text": self.文本,
            "mode": self.模式,
            "runtime": self.运行时,
            "line": self.行号,
            "column": self.列号,
            "end_line": self.结束行号,
            "end_column": self.结束列号,
        }

    def to_dict(self) -> dict[str, object]:
        return self.转为字典()


@dataclass(frozen=True, slots=True)
class 结构命中:
    """A classical control-flow or output keyword found in source."""

    文本: str
    类型: str
    Python映射: str
    行号: int
    列号: int

    def 转为字典(self) -> dict[str, object]:
        return {
            "text": self.文本,
            "kind": self.类型,
            "python": self.Python映射,
            "line": self.行号,
            "column": self.列号,
        }

    def to_dict(self) -> dict[str, object]:
        return self.转为字典()


@dataclass(frozen=True, slots=True)
class 翻译结果:
    """Structured translation output for compilers and future WebUIs."""

    Python源码: str
    成语命中列表: tuple[成语命中, ...]
    结构命中列表: tuple[结构命中, ...]

    @property
    def python_source(self) -> str:
        return self.Python源码

    @property
    def idiom_hits(self) -> tuple[成语命中, ...]:
        return self.成语命中列表

    @property
    def structure_hits(self) -> tuple[结构命中, ...]:
        return self.结构命中列表

    def 转为字典(self) -> dict[str, object]:
        return {
            "python_source": self.Python源码,
            "idiom_hits": [命中.转为字典() for 命中 in self.成语命中列表],
            "structure_hits": [
                命中.转为字典() for 命中 in self.结构命中列表
            ],
        }

    def to_dict(self) -> dict[str, object]:
        return self.转为字典()


@dataclass(frozen=True, slots=True)
class _替换:
    起点: int
    终点: int
    文本: str


_忽略行结构的类型 = {
    token.ENCODING,
    token.INDENT,
    token.DEDENT,
    token.NEWLINE,
    token.NL,
    token.COMMENT,
    token.ENDMARKER,
}


def _分词(源码: str) -> list[tokenize.TokenInfo]:
    try:
        return list(tokenize.generate_tokens(io.StringIO(源码).readline))
    except (tokenize.TokenError, IndentationError) as 错误:
        raise 翻译错误(f"句法不通，请重新断句！{错误}") from 错误


def _行起点(源码: str) -> list[int]:
    起点 = [0]
    for 索引, 字符 in enumerate(源码):
        if 字符 == "\n":
            起点.append(索引 + 1)
    return 起点


def _绝对位置(
    位置: tuple[int, int],
    行起点: list[int],
    源码长度: int,
) -> int:
    行号, 列号 = 位置
    if 行号 - 1 >= len(行起点):
        return 源码长度
    return 行起点[行号 - 1] + 列号


def _词元范围(
    词元: tokenize.TokenInfo,
    行起点: list[int],
    源码长度: int,
) -> tuple[int, int]:
    return (
        _绝对位置(词元.start, 行起点, 源码长度),
        _绝对位置(词元.end, 行起点, 源码长度),
    )


def _应用替换(源码: str, 替换: Iterable[_替换]) -> str:
    已排序 = sorted(替换, key=lambda 项: (项.起点, 项.终点))
    上一终点 = -1
    for 当前 in 已排序:
        if 当前.起点 < 上一终点:
            raise 翻译错误("翻译器生成了互相重叠的替换。")
        上一终点 = 当前.终点

    结果 = 源码
    for 当前 in reversed(已排序):
        结果 = 结果[: 当前.起点] + 当前.文本 + 结果[当前.终点 :]
    return 结果


def _是独立彩蛋行(
    源码: str,
    首词元: tokenize.TokenInfo,
    尾词元: tokenize.TokenInfo,
) -> bool:
    行文本 = 源码.splitlines(keepends=True)[首词元.start[0] - 1]
    前文 = 行文本[: 首词元.start[1]]
    后文 = 行文本[尾词元.end[1] :].strip()
    return not 前文.strip() and (not 后文 or 后文.startswith("#"))


def _替换空格成语(
    源码: str,
    词典: 成语词库,
    命中列表: list[成语命中],
) -> str:
    """Replace ``色 令 智 昏`` sequences before connected idiom calls."""

    词元 = _分词(源码)
    行起点 = _行起点(源码)
    源码长度 = len(源码)
    成语列表 = sorted(词典, key=lambda 名称: (-len(名称), 名称))
    已占用: set[int] = set()
    替换: list[_替换] = []

    for 起始索引, 首词元 in enumerate(词元):
        if 起始索引 in 已占用 or 首词元.type != token.NAME:
            continue

        for 成语 in 成语列表:
            字符 = list(成语)
            末尾索引 = 起始索引 + len(字符)
            if 末尾索引 > len(词元):
                continue
            候选 = 词元[起始索引:末尾索引]
            if any(项目.type != token.NAME for 项目 in 候选):
                continue
            if [项目.string for 项目 in 候选] != 字符:
                continue
            if len({项目.start[0] for 项目 in 候选}) != 1:
                continue
            if any(索引 in 已占用 for 索引 in range(起始索引, 末尾索引)):
                continue

            合法空格 = True
            for 左侧, 右侧 in zip(候选, 候选[1:]):
                左终点 = _绝对位置(左侧.end, 行起点, 源码长度)
                右起点 = _绝对位置(右侧.start, 行起点, 源码长度)
                间隔 = 源码[左终点:右起点]
                if not 间隔 or any(字符 not in " \t" for 字符 in 间隔):
                    合法空格 = False
                    break
            if not 合法空格:
                continue

            起点, _ = _词元范围(候选[0], 行起点, 源码长度)
            _, 终点 = _词元范围(候选[-1], 行起点, 源码长度)
            文本 = f'__chengyu_egg__("{成语}")'
            if _是独立彩蛋行(源码, 候选[0], 候选[-1]):
                文本 += "  # 🥚"
            替换.append(_替换(起点, 终点, 文本))
            命中列表.append(
                成语命中(
                    文本=成语,
                    模式="spaced",
                    运行时=str(词典[成语]["runtime"]),
                    行号=候选[0].start[0],
                    列号=候选[0].start[1] + 1,
                    结束行号=候选[-1].end[0],
                    结束列号=候选[-1].end[1] + 1,
                )
            )
            已占用.update(range(起始索引, 末尾索引))
            break

    return _应用替换(源码, 替换)


def _替换连写调用(
    源码: str,
    词典: 成语词库,
    命中列表: list[成语命中],
) -> str:
    """Translate an idiom function name without parsing its parentheses."""

    词元 = _分词(源码)
    行起点 = _行起点(源码)
    源码长度 = len(源码)
    替换: list[_替换] = []

    for 索引, 当前 in enumerate(词元[:-1]):
        if 当前.type != token.NAME or 当前.string not in 词典:
            continue
        下一个 = 词元[索引 + 1]
        if 下一个.type != token.OP or 下一个.string != "(":
            continue
        起点, 终点 = _词元范围(当前, 行起点, 源码长度)
        文本 = f'__chengyu_functions__["{当前.string}"]'
        替换.append(_替换(起点, 终点, 文本))
        命中列表.append(
            成语命中(
                文本=当前.string,
                模式="connected",
                运行时=str(词典[当前.string]["runtime"]),
                行号=当前.start[0],
                列号=当前.start[1] + 1,
                结束行号=当前.end[0],
                结束列号=当前.end[1] + 1,
            )
        )

    return _应用替换(源码, 替换)


def _翻译文言结构(
    源码: str,
    命中列表: list[结构命中],
) -> str:
    词元 = _分词(源码)
    行起点 = _行起点(源码)
    源码长度 = len(源码)
    每行: dict[int, list[tokenize.TokenInfo]] = {}
    替换: list[_替换] = []

    for 当前 in 词元:
        if 当前.type not in _忽略行结构的类型:
            每行.setdefault(当前.start[0], []).append(当前)

    for 行词元 in 每行.values():
        首项 = 行词元[0]
        if 首项.type == token.NAME and 首项.string in {"若", "如是", "否则"}:
            对应 = {"若": "if", "如是": "elif", "否则": "else"}[首项.string]
            起点, 终点 = _词元范围(首项, 行起点, 源码长度)
            替换.append(_替换(起点, 终点, 对应))
            命中列表.append(
                结构命中(
                    文本=首项.string,
                    类型={"若": "IF", "如是": "ELIF", "否则": "ELSE"}[
                        首项.string
                    ],
                    Python映射=对应,
                    行号=首项.start[0],
                    列号=首项.start[1] + 1,
                )
            )
        elif len(行词元) == 1 and 首项.type == token.NAME:
            if 首项.string == "云云":
                起点, 终点 = _词元范围(首项, 行起点, 源码长度)
                替换.append(_替换(起点, 终点, "# 云云（块尾标记）"))
                命中列表.append(
                    结构命中(
                        文本="云云",
                        类型="END_MARKER",
                        Python映射="# comment",
                        行号=首项.start[0],
                        列号=首项.start[1] + 1,
                    )
                )
        elif (
            len(行词元) >= 2
            and 首项.type == token.NAME
            and 行词元[1].type == token.NAME
            and 行词元[1].string == "之于"
        ):
            变量起点, 变量终点 = _词元范围(首项, 行起点, 源码长度)
            虚词起点, 虚词终点 = _词元范围(
                行词元[1], 行起点, 源码长度
            )
            替换.append(
                _替换(变量起点, 变量终点, f"for {首项.string}")
            )
            替换.append(_替换(虚词起点, 虚词终点, "in"))
            命中列表.append(
                结构命中(
                    文本="之于",
                    类型="FOR_IN",
                    Python映射="for ... in ...",
                    行号=行词元[1].start[0],
                    列号=行词元[1].start[1] + 1,
                )
            )

    for 索引, 当前 in enumerate(词元[:-1]):
        if 当前.type != token.NAME or 当前.string != "列":
            continue
        下一个 = 词元[索引 + 1]
        if 下一个.type == token.OP and 下一个.string == "(":
            起点, 终点 = _词元范围(当前, 行起点, 源码长度)
            替换.append(_替换(起点, 终点, "print"))
            命中列表.append(
                结构命中(
                    文本="列",
                    类型="PRINT",
                    Python映射="print",
                    行号=当前.start[0],
                    列号=当前.start[1] + 1,
                )
            )

    return _应用替换(源码, 替换)


def 分析并翻译(
    源码: str,
    词典: 成语词库 | None = None,
) -> 翻译结果:
    """Translate source and retain structured matches for later stages."""

    if not isinstance(源码, str):
        raise TypeError("源码必须是字符串。")
    当前词典 = deepcopy(成语词典 if 词典 is None else 词典)
    成语命中列表: list[成语命中] = []
    结构命中列表: list[结构命中] = []
    结果 = _替换空格成语(源码, 当前词典, 成语命中列表)
    结果 = _替换连写调用(结果, 当前词典, 成语命中列表)
    结果 = _翻译文言结构(结果, 结构命中列表)
    成语命中列表.sort(key=lambda 项: (项.行号, 项.列号))
    结构命中列表.sort(key=lambda 项: (项.行号, 项.列号))
    return 翻译结果(
        Python源码=结果,
        成语命中列表=tuple(成语命中列表),
        结构命中列表=tuple(结构命中列表),
    )


def 翻译(源码: str, 词典: 成语词库 | None = None) -> str:
    """Translate source while preserving the original string-returning API."""

    return 分析并翻译(源码, 词典).Python源码


# English aliases.
TranslationError = 翻译错误
IdiomHit = 成语命中
StructureHit = 结构命中
TranslationResult = 翻译结果
analyze_and_translate = 分析并翻译
translate = 翻译
