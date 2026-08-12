from __future__ import annotations

import unittest

from chengyulang import 翻译


class TranslatorTests(unittest.TestCase):
    def test_connected_call_uses_dispatch_table(self) -> None:
        译文 = 翻译("结果 = 色令智昏(函数(1, 2) > 0)")
        self.assertEqual(
            译文,
            '结果 = __chengyu_functions__["色令智昏"](函数(1, 2) > 0)',
        )

    def test_spaced_egg_has_priority(self) -> None:
        译文 = 翻译("色 令 智 昏")
        self.assertEqual(译文, '__chengyu_egg__("色令智昏")  # 🥚')

    def test_strings_and_comments_are_unchanged(self) -> None:
        源码 = (
            '# 色 令 智 昏\n文本 = "色 令 智 昏，列(甲)"\n'
            "列(文本)\n"
        )
        译文 = 翻译(源码)
        self.assertIn('# 色 令 智 昏', 译文)
        self.assertIn('"色 令 智 昏，列(甲)"', 译文)
        self.assertTrue(译文.endswith("print(文本)\n"))

    def test_control_flow_and_print(self) -> None:
        源码 = (
            "数 之于 [1, 2]:\n"
            "    若 数 > 1:\n"
            "        列(数)\n"
            "    如是 数 == 1:\n"
            "        列('一')\n"
            "    否则:\n"
            "        列('小')\n"
        )
        译文 = 翻译(源码)
        self.assertIn("for 数 in [1, 2]:", 译文)
        self.assertIn("if 数 > 1:", 译文)
        self.assertIn("elif 数 == 1:", 译文)
        self.assertIn("else:", 译文)
        self.assertIn("print(数)", 译文)
        compile(译文, "<test>", "exec")

    def test_optional_end_marker_becomes_comment(self) -> None:
        self.assertEqual(翻译("云云"), "# 云云（块尾标记）")


if __name__ == "__main__":
    unittest.main()
