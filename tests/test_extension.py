from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout

from chengyulang import 执行, 注册成语, 词库加载


class ExtensionTests(unittest.TestCase):
    def test_python_registration_adds_metadata_and_behavior(self) -> None:
        词典 = 词库加载()
        注册成语(
            "一鼓作气",
            lambda 数字: 数字 + 1,
            py="数字 + 1",
            egg="鼓.响(); 气.盛()",
            词典=词典,
        )
        输出 = io.StringIO()
        with redirect_stdout(输出):
            结果 = 执行("列(一鼓作气(41))", 词典=词典)
        self.assertTrue(结果.成功)
        self.assertEqual(输出.getvalue(), "42\n")


if __name__ == "__main__":
    unittest.main()
