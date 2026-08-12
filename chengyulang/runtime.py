"""Safe, explicit runtime implementations for bundled idioms."""

from __future__ import annotations

import copy
import importlib
import inspect
import random
import threading
import time
from collections import deque
from collections.abc import Callable, Iterable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from functools import reduce
from itertools import islice
from pathlib import Path
from typing import Any, TypeVar

from .catalog import 成语词典, 成语词库

T = TypeVar("T")
成语函数 = Callable[..., Any]
_运行时实现: dict[str, 成语函数] = {}


class 成语运行时错误(RuntimeError):
    """Base exception raised by idiom runtime functions."""


class 成语彩蛋错误(成语运行时错误):
    """An intentional exception produced by an Easter egg."""


def 成语实现(名称: str) -> Callable[[成语函数], 成语函数]:
    """Register a Python callable as an idiom implementation."""

    def 装饰器(函数: 成语函数) -> 成语函数:
        _运行时实现[名称] = 函数
        return 函数

    return 装饰器


def 注册成语(
    名称: str,
    实现: 成语函数,
    *,
    py: str,
    egg: str,
    category: str = "自定义",
    词典: 成语词库 | None = None,
) -> None:
    """Register metadata and executable behavior without editing the engine."""

    if not 名称 or any(字符.isspace() for 字符 in 名称):
        raise ValueError("成语名称必须是无空格的非空字符串。")
    if not callable(实现):
        raise TypeError("实现必须是可调用对象。")

    目标词典 = 成语词典 if 词典 is None else 词典
    目标词典[名称] = {
        "category": category,
        "py": py,
        "egg": egg,
        "runtime": 名称,
    }
    _运行时实现[名称] = 实现


def 调用成语(
    名称: str,
    *参数: Any,
    _词典: 成语词库 | None = None,
    **关键字: Any,
) -> Any:
    """Dispatch a translated idiom call through the explicit registry."""

    词典 = 成语词典 if _词典 is None else _词典
    try:
        条目 = 词典[名称]
    except KeyError as 错误:
        raise 成语运行时错误(f"词库中不存在成语：{名称}") from 错误

    实现名称 = 条目.get("runtime", 名称)
    try:
        实现 = _运行时实现[实现名称]
    except KeyError as 错误:
        raise 成语运行时错误(
            f"成语“{名称}”尚未注册运行时实现：{实现名称}"
        ) from 错误
    return 实现(*参数, **关键字)


def 触发彩蛋(名称: str, *, _词典: 成语词库 | None = None) -> None:
    """Print an egg description and run a deliberately safe egg behavior."""

    词典 = 成语词典 if _词典 is None else _词典
    try:
        彩蛋 = 词典[名称]["egg"]
    except KeyError as 错误:
        raise 成语运行时错误(
            f"彩蛋词库中不存在成语：{名称}"
        ) from 错误

    print(f"🎉 彩蛋触发：{名称} → {彩蛋}")
    if 名称 == "色令智昏":
        raise 成语彩蛋错误("智已昏，程序中断")
    if 名称 == "掩耳盗铃":
        print("🔔 铃铛响了！")
    if 名称 == "不知所云":
        print("☁️ 云亦不知所云：锟斤拷烫烫烫……")


@成语实现("指鹿为马")
def _指鹿为马(对象: Any) -> bool:
    return bool(对象)


@成语实现("自相矛盾")
def _自相矛盾(消息: str = "逻辑冲突") -> None:
    raise 成语运行时错误(消息)


@成语实现("掩耳盗铃")
def _掩耳盗铃(
    动作: Callable[..., T] | T,
    *参数: Any,
    默认值: T | None = None,
    **关键字: Any,
) -> T | None:
    try:
        return 动作(*参数, **关键字) if callable(动作) else 动作
    except Exception:
        return 默认值


@成语实现("色令智昏")
def _色令智昏(条件: Any) -> bool:
    return not bool(条件)


@成语实现("偷梁换柱")
def _偷梁换柱(甲: T, 乙: T) -> tuple[T, T]:
    return 乙, 甲


@成语实现("三人成虎")
def _三人成虎(*三人: Any) -> Any:
    if len(三人) != 3:
        raise 成语运行时错误("三人成虎恰需三人。")
    return sum(三人)


@成语实现("水落石出")
def _水落石出(列表: Iterable[T]) -> T:
    try:
        return max(列表)
    except ValueError as 错误:
        raise 成语运行时错误(
            "水已落，石却不在空列表中。"
        ) from 错误


@成语实现("水到渠成")
def _水到渠成(初值: T, *处理步骤: Callable[[T], T]) -> T:
    return reduce(lambda 当前, 步骤: 步骤(当前), 处理步骤, 初值)


@成语实现("守株待兔")
def _守株待兔(事件: Any, 超时: float | None = None) -> Any:
    if hasattr(事件, "wait") and callable(事件.wait):
        return 事件.wait(timeout=超时)
    if inspect.isawaitable(事件):
        return 事件
    return 事件() if callable(事件) else 事件


@成语实现("缘木求鱼")
def _缘木求鱼(
    列表: Iterable[T],
    条件: Callable[[T], bool] | None = None,
) -> T | None:
    谓词 = 条件 or (lambda _: True)
    return next((项目 for 项目 in 列表 if 谓词(项目)), None)


@成语实现("刻舟求剑")
def _刻舟求剑(序列: Sequence[T], 索引: int = 0) -> T:
    return 序列[索引]


@成语实现("南辕北辙")
@成语实现("逆水行舟")
def _反向而行(列表: Iterable[T]) -> list[T]:
    return list(reversed(list(列表)))


@成语实现("顺水推舟")
def _顺水推舟(
    条件: Any,
    动作: Callable[..., T] | T,
    *参数: Any,
    **关键字: Any,
) -> T | None:
    if not 条件:
        return None
    return 动作(*参数, **关键字) if callable(动作) else 动作


@成语实现("买椟还珠")
def _买椟还珠(字典: Mapping[T, Any]) -> list[T]:
    return list(字典.keys())


@成语实现("九牛一毛")
def _九牛一毛(
    列表: Sequence[T],
    随机源: random.Random | None = None,
) -> T:
    if not 列表:
        raise 成语运行时错误("九牛皆无，自然无毛可取。")
    return (随机源 or random).choice(列表)


def _执行任务(任务: Callable[[], T] | T) -> T:
    return 任务() if callable(任务) else 任务


@成语实现("一石二鸟")
def _一石二鸟(任务一: Any, 任务二: Any) -> tuple[Any, Any]:
    with ThreadPoolExecutor(max_workers=2) as 线程池:
        结果 = list(线程池.map(_执行任务, (任务一, 任务二)))
    return 结果[0], 结果[1]


@成语实现("百发百中")
def _百发百中(条件列表: Iterable[Any]) -> bool:
    return all(条件列表)


@成语实现("千变万化")
def _千变万化(函数: Callable[[T], Any], 列表: Iterable[T]) -> list[Any]:
    return list(map(函数, 列表))


@成语实现("万无一失")
def _万无一失(
    动作: Callable[..., T],
    *参数: Any,
    默认值: T | None = None,
    **关键字: Any,
) -> T | None:
    try:
        return 动作(*参数, **关键字)
    except Exception:
        return 默认值


@成语实现("对牛弹琴")
def _对牛弹琴(秒数: float = 0.01) -> float:
    实际秒数 = min(max(float(秒数), 0.0), 1.0)
    time.sleep(实际秒数)
    return 实际秒数


@成语实现("狐假虎威")
def _狐假虎威(
    装饰器: Callable[[T], T],
    函数: T | None = None,
) -> Callable[[T], T] | T:
    return 装饰器 if 函数 is None else 装饰器(函数)


@成语实现("鹤立鸡群")
def _鹤立鸡群(列表: Iterable[T]) -> T:
    return max(列表)


@成语实现("虎头蛇尾")
def _虎头蛇尾(列表: Sequence[T]) -> list[T]:
    if not 列表:
        raise 成语运行时错误("空列表既无虎头，也无蛇尾。")
    return [列表[0], 列表[-1]]


@成语实现("画蛇添足")
def _画蛇添足(列表: list[T], 足: T | None = None) -> list[T | None]:
    列表.append(足)
    return 列表


@成语实现("鸡飞狗跳")
def _鸡飞狗跳(消息: str = "混乱") -> None:
    raise 成语运行时错误(消息)


@成语实现("开天辟地")
def _开天辟地(路径: str | Path = "/") -> dict[str, Any]:
    return {"动作": "mkdir", "路径": str(路径), "模拟": True}


@成语实现("盘古开天")
def _盘古开天(
    初始命名空间: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return dict(初始命名空间 or {})


@成语实现("嫦娥奔月")
def _嫦娥奔月(目标: str = "cloud") -> dict[str, Any]:
    return {"动作": "deploy", "目标": 目标, "模拟": True}


@成语实现("后羿射日")
def _后羿射日(pid: int, 信号: int = 9) -> dict[str, Any]:
    return {"动作": "kill", "pid": int(pid), "信号": int(信号), "模拟": True}


@成语实现("精卫填海")
def _精卫填海(数据: Any, 填充值: Any = 0) -> Any:
    if hasattr(数据, "fillna") and callable(数据.fillna):
        return 数据.fillna(填充值)
    if isinstance(数据, Mapping):
        return {
            键: 填充值 if 值 is None else 值
            for 键, 值 in 数据.items()
        }
    if isinstance(数据, (list, tuple)):
        新数据 = [填充值 if 值 is None else 值 for 值 in 数据]
        return type(数据)(新数据)
    return 填充值 if 数据 is None else 数据


@成语实现("愚公移山")
def _愚公移山(
    数据: Any,
    迁移器: Callable[[Any], T] | None = None,
) -> T | dict[str, Any]:
    if 迁移器 is not None:
        return 迁移器(数据)
    大小 = len(数据) if hasattr(数据, "__len__") else None
    return {"动作": "migrate", "项目数": 大小, "模拟": True}


@成语实现("风起云涌")
def _风起云涌(任务: Iterable[Any], 最大并发: int = 4) -> list[Any]:
    任务列表 = list(任务)
    if not 任务列表:
        return []
    工作者 = max(1, min(int(最大并发), len(任务列表), 32))
    with ThreadPoolExecutor(max_workers=工作者) as 线程池:
        return list(线程池.map(_执行任务, 任务列表))


@成语实现("风平浪静")
def _风平浪静() -> threading.Lock:
    return threading.Lock()


@成语实现("见风使舵")
def _见风使舵(条件: Any, 真策略: Any, 假策略: Any = None) -> Any:
    策略 = 真策略 if 条件 else 假策略
    return 策略() if callable(策略) else 策略


@成语实现("杯弓蛇影")
def _杯弓蛇影(对象: T | None) -> T:
    if 对象 is None:
        raise 成语运行时错误("杯中只有弓影，并无可引用之物。")
    return 对象


@成语实现("井底之蛙")
def _井底之蛙(
    局部作用域: Mapping[str, T] | None = None,
    名称: str | None = None,
    默认值: T | None = None,
) -> Mapping[str, T] | T | None:
    作用域 = dict(局部作用域 or {})
    return 作用域 if 名称 is None else 作用域.get(名称, 默认值)


@成语实现("东施效颦")
def _东施效颦(对象: T) -> T:
    return copy.copy(对象)


@成语实现("邯郸学步")
def _邯郸学步(父类: type, 类名: str = "子类") -> type:
    if not isinstance(父类, type):
        raise TypeError("邯郸学步需要一个父类。")
    return type(类名, (父类,), {})


@成语实现("夸父追日")
def _夸父追日(可迭代对象: Iterable[T], 上限: int = 1000) -> list[T]:
    安全上限 = max(0, min(int(上限), 100_000))
    return list(islice(可迭代对象, 安全上限))


@成语实现("亡羊补牢")
def _亡羊补牢(
    动作: Callable[..., T],
    补救: Callable[[Exception], T],
    *参数: Any,
    **关键字: Any,
) -> T:
    try:
        return 动作(*参数, **关键字)
    except Exception as 错误:
        return 补救(错误)


_安全模块 = {
    "collections",
    "functools",
    "itertools",
    "json",
    "math",
    "random",
    "re",
    "statistics",
}


@成语实现("暗度陈仓")
def _暗度陈仓(模块名: str) -> Any:
    if 模块名 not in _安全模块:
        raise 成语运行时错误(f"模块不在安全白名单中：{模块名}")
    return importlib.import_module(模块名)


@成语实现("七上八下")
def _七上八下(随机源: random.Random | None = None) -> int:
    return (随机源 or random).randint(0, 1)


@成语实现("五颜六色")
def _五颜六色(内容: T, 颜色: str = "彩色") -> dict[str, Any]:
    return {"内容": 内容, "颜色": 颜色}


@成语实现("三心二意")
def _三心二意(
    候选: Sequence[T],
    权重: Sequence[float] | None = None,
) -> T | float:
    if not 候选:
        raise 成语运行时错误("心意皆空，无从取舍。")
    if 权重 is None:
        return 候选[0]
    if len(候选) != len(权重):
        raise 成语运行时错误("候选与权重数量不一致。")

    总权重 = sum(权重)
    if 总权重 == 0:
        raise 成语运行时错误("权重之和不可为零。")
    if all(isinstance(项目, (int, float)) for 项目 in 候选):
        加权和 = sum(项目 * 比重 for 项目, 比重 in zip(候选, 权重))
        return 加权和 / 总权重
    最大索引 = max(range(len(权重)), key=权重.__getitem__)
    return 候选[最大索引]


@成语实现("四通八达")
def _四通八达(图: Mapping[T, Iterable[T]], 起点: T | None = None) -> bool:
    节点 = set(图)
    for 邻居 in 图.values():
        节点.update(邻居)
    if not 节点:
        return True

    开始 = next(iter(节点)) if 起点 is None else 起点
    已访问 = {开始}
    队列 = deque([开始])
    while 队列:
        当前 = 队列.popleft()
        for 邻居 in 图.get(当前, ()):
            if 邻居 not in 已访问:
                已访问.add(邻居)
                队列.append(邻居)
    return 已访问 == 节点


@成语实现("十全十美")
def _十全十美(测试结果: Iterable[Any]) -> bool:
    return all(测试结果)


@成语实现("单枪匹马")
def _单枪匹马(*参数: T) -> T:
    if not 参数:
        raise 成语运行时错误("单枪匹马也至少要带一个参数。")
    return 参数[0]


@成语实现("龙飞凤舞")
def _龙飞凤舞(动画帧: Iterable[T]) -> dict[str, Any]:
    return {"动画": list(动画帧), "状态": "ready"}


@成语实现("狼吞虎咽")
def _狼吞虎咽(文件或路径: Any, 编码: str = "utf-8") -> str:
    if hasattr(文件或路径, "read") and callable(文件或路径.read):
        return 文件或路径.read()
    return Path(文件或路径).read_text(encoding=编码)


@成语实现("细嚼慢咽")
def _细嚼慢咽(文件或路径: Any, 编码: str = "utf-8") -> list[str]:
    if hasattr(文件或路径, "readlines") and callable(文件或路径.readlines):
        return 文件或路径.readlines()
    with Path(文件或路径).open("r", encoding=编码) as 文件:
        return 文件.readlines()


@成语实现("不知所云")
def _不知所云(
    长度: int = 16,
    随机源: random.Random | None = None,
) -> str:
    安全长度 = max(0, min(int(长度), 4096))
    字符集 = "锟斤拷烫屯锘云雾※？#@�"
    return "".join((随机源 or random).choices(字符集, k=安全长度))


def 已注册实现() -> frozenset[str]:
    """Return runtime names, primarily for validation and tests."""

    return frozenset(_运行时实现)


# English aliases.
ChengyuRuntimeError = 成语运行时错误
ChengyuEggError = 成语彩蛋错误
register_idiom = 注册成语
call_idiom = 调用成语
trigger_egg = 触发彩蛋
registered_implementations = 已注册实现
