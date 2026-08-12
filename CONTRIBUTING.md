# 参与贡献

欢迎新增成语、彩蛋、测试或翻译规则。请保持项目的两条边界：词库元数据放 JSON，
可执行行为通过显式 Python 注册表提供；危险脑洞必须以无副作用模拟为默认行为。

新增内置成语时：

1. 在 `chengyulang/data/idioms.json` 添加词条；
2. 在 `chengyulang/runtime.py` 使用 `@成语实现("成语")` 注册实现；
3. 为正常逻辑和彩蛋优先级添加测试；
4. 更新 README 中的词条数量和 `CHANGELOG.md`；
5. 运行以下检查：

```bash
python -m unittest discover -s tests -v
python -m compileall -q chengyulang chengyu_lang.py
ruff check .
```

Pull request 请简述：连写语义、空格彩蛋、安全边界，以及为何这个双关值得加入。

