from __future__ import annotations

import io
import random
import unittest
from contextlib import redirect_stdout

from chengyulang import 执行, 调用成语


class ExecutorTests(unittest.TestCase):
    def test_normal_program_executes(self) -> None:
        输出 = io.StringIO()
        with redirect_stdout(输出):
            结果 = 执行("值 = 色令智昏(False)\n列(值)")
        self.assertTrue(结果.成功)
        self.assertIs(结果.命名空间["值"], True)
        self.assertEqual(输出.getvalue(), "True\n")

    def test_egg_error_is_friendly(self) -> None:
        标准输出 = io.StringIO()
        错误输出 = io.StringIO()
        with redirect_stdout(标准输出):
            结果 = 执行("色 令 智 昏", 错误输出=错误输出)
        self.assertFalse(结果.成功)
        self.assertIn("🎉 彩蛋触发：色令智昏", 标准输出.getvalue())
        self.assertIn("💥 成语运行时出错：智已昏", 错误输出.getvalue())

    def test_syntax_error_is_localized(self) -> None:
        错误输出 = io.StringIO()
        结果 = 执行("若 True\n    列('漏了冒号')", 错误输出=错误输出)
        self.assertFalse(结果.成功)
        self.assertIn("句法不通，请重新断句", 错误输出.getvalue())

    def test_dangerous_original_ideas_are_dry_run(self) -> None:
        计划 = 调用成语("后羿射日", 1234)
        self.assertEqual(计划["pid"], 1234)
        self.assertIs(计划["模拟"], True)

    def test_gibberish_can_be_seeded(self) -> None:
        甲 = 调用成语("不知所云", 20, 随机源=random.Random(7))
        乙 = 调用成语("不知所云", 20, 随机源=random.Random(7))
        self.assertEqual(甲, 乙)
        self.assertEqual(len(甲), 20)


if __name__ == "__main__":
    unittest.main()

