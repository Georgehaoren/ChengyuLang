"""Register a brand-new idiom implementation from ordinary Python."""

from chengyulang import 执行, 注册成语


def 一鼓作气实现(数字: int) -> int:
    return 数字 + 1


注册成语(
    "一鼓作气",
    一鼓作气实现,
    py="数字 + 1",
    egg="鼓.响(); 气.盛()",
)

执行('列(一鼓作气(41))')

