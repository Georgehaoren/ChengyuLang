from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from chengyulang import 成语词典, 已注册实现, 词库加载, 词库错误


class CatalogTests(unittest.TestCase):
    def test_bundled_catalog_has_52_entries(self) -> None:
        self.assertEqual(len(成语词典), 52)
        self.assertIn("不知所云", 成语词典)

    def test_every_bundled_entry_has_runtime(self) -> None:
        已注册 = 已注册实现()
        for 名称, 条目 in 成语词典.items():
            with self.subTest(名称=名称):
                self.assertIn(条目["runtime"], 已注册)

    def test_direct_mapping_json_is_supported(self) -> None:
        数据 = {
            "一鼓作气": {
                "category": "测试",
                "py": "value + 1",
                "egg": "鼓.响()",
                "runtime": "一鼓作气",
            }
        }
        with tempfile.TemporaryDirectory() as 临时目录:
            路径 = Path(临时目录, "catalog.json")
            路径.write_text(json.dumps(数据, ensure_ascii=False), encoding="utf-8")
            self.assertEqual(list(词库加载(路径)), ["一鼓作气"])

    def test_invalid_entry_is_rejected(self) -> None:
        数据 = {"version": 1, "idioms": {"残缺不全": {"py": "None"}}}
        with tempfile.TemporaryDirectory() as 临时目录:
            路径 = Path(临时目录, "bad.json")
            路径.write_text(json.dumps(数据, ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(词库错误):
                词库加载(路径)


if __name__ == "__main__":
    unittest.main()

