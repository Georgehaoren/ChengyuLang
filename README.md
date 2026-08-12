# 成语语（ChengyuLang）

[English](README_en.md)

> 空格一断，语义突变。

成语语是一门以 Python 为宿主的实验性中文 DSL / 趣味编程语言。成语连写时
调用正常逻辑；把同一个成语拆成单字 Token 时，则触发一段黑色幽默式彩蛋。

```python
结果 = 色令智昏(3 > 1)  # 正常语义：not bool(3 > 1)
列(结果)

色 令 智 昏            # 彩蛋语义：打印提示并让“智已昏”
```

这不是把字符串直接替换成危险伪代码的实现。项目将词库元数据、翻译规则和
Python 运行时分离：JSON 负责描述，显式注册的 Python 函数负责行为。

## 当前能力

- 52 条内置成语：原始蓝图实际列出 51 条，另加入了 `不知所云`。
- 彩蛋优先：`色 令 智 昏` 先于 `色令智昏(...)` 处理。
- 文言结构：`之于`、`若`、`如是`、`否则`、`列`，以及可选块尾标记 `云云`。
- Token 感知：不会改写字符串或 `#` 注释，嵌套括号无需正则硬解析。
- JSON 词库：支持校验、覆盖、别名和自定义扩展。
- 模块化运行时：52 条内置词条都有可执行实现和测试。
- 控制台编译器：可将 `.cy` 确定性编译为可直接运行的 `.py` 文件。
- 结构化过程：提供成语命中、文言结构、编译阶段、诊断及 JSON 输出。
- 零运行时依赖：只使用 Python 标准库。

## 快速开始

需要 Python 3.10 或更高版本。

```bash
git clone <your-repository-url>
cd ChengyuLang

# 一键创建 .venv 并安装当前项目（macOS / Linux）
chmod +x setup_venv.sh
./setup_venv.sh
source .venv/bin/activate

# 无需安装即可演示
python chengyu_lang.py

# 或以模块方式运行
python -m chengyulang demo
python -m chengyulang check examples/demo.cy
python -m chengyulang compile examples/demo.cy
python examples/demo.py
python -m chengyulang run examples/demo.cy --show-python
```

如需安装命令行入口：

```bash
python -m pip install -e .
chengyulang run examples/demo.cy
```

`setup_venv.sh` 默认创建或复用仓库中的 `.venv`，以 editable 模式安装当前源码，
并执行版本检查和示例源码检查。也可以指定其他路径或 Python：

```bash
./setup_venv.sh /path/to/venv
CHENGYULANG_PYTHON=python3.12 ./setup_venv.sh
```

脚本需要 Python 3.10+；不会删除或重建已经存在的虚拟环境。若处于离线环境且
venv 中已准备好 `pip>=21.3`、`setuptools>=68` 和 `wheel`，可使用
`CHENGYULANG_OFFLINE=1` 禁止下载构建工具。

## 语法示例

`examples/demo.cy`：

```python
结果 = 色令智昏(3 > 1)
列("结果：", 结果)

数 之于 [1, 2, 3]:
    若 数 > 1:
        列(数)

列("随机乱码：", 不知所云(12))
```

翻译结果等价于：

```python
结果 = __chengyu_functions__["色令智昏"](3 > 1)
print("结果：", 结果)

for 数 in [1, 2, 3]:
    if 数 > 1:
        print(数)

print("随机乱码：", __chengyu_functions__["不知所云"](12))
```

`不知所云(长度)` 会返回由“锟斤拷、烫、屯、※、�”等字符组成的随机乱码；
`不 知 所 云` 则直接触发“云亦不知所云”的彩蛋。

## 命令行

| 命令 | 用途 |
| --- | --- |
| `chengyulang demo` | 运行内置演示 |
| `chengyulang check FILE` | 检查源码但不写文件 |
| `chengyulang compile FILE` | 生成可直接运行的同名 `.py` 文件 |
| `chengyulang compile FILE -o OUT.py` | 指定编译产物路径 |
| `chengyulang compile FILE --stdout` | 将完整 Python 产物输出至标准输出 |
| `chengyulang compile FILE --json` | 输出机器可读的阶段、命中和诊断信息 |
| `chengyulang run FILE` | 翻译并执行可信源码 |
| `chengyulang translate FILE` | 仅输出不含运行时引导的内部译文 |
| `chengyulang catalog` | 校验并列出词库 |
| `--catalog extra.json` | 在内置词库上扩展或覆盖 JSON 词条 |

默认拒绝覆盖已有文件；确认覆盖时使用 `--force`。用 `-` 代替文件名可从标准输入
读取，此时 `compile` 需要同时指定 `--stdout`、`--output` 或 `--check`。

编译过程不会执行用户代码。生成的 `.py` 文件包含确定性的运行时引导和词库快照，
仍需在已经安装 ChengyuLang 的 Python 环境中运行：

```bash
chengyulang compile examples/demo.cy --show-stages
python examples/demo.py
```

## 项目结构

```text
chengyulang/
├── data/idioms.json       # 52 条词库元数据
├── catalog.py             # JSON 加载、校验与合并
├── translator.py          # Token 感知翻译器
├── compiler.py            # AST 检查、代码生成与原子写入
├── diagnostics.py         # 结构化诊断与控制台渲染
├── bootstrap.py           # 可复现的运行时引导代码
├── runtime.py             # 安全实现与插件注册表
├── executor.py            # 受信源码执行器
└── cli.py                 # check / compile / translate / run / catalog
examples/                  # .cy、JSON 扩展与 Python 插件示例
tests/                     # 标准库 unittest 测试
chengyu_lang.py            # 兼容最初单文件设想的入口
```

更完整的取舍见 [设计说明](docs/DESIGN.md)。

## 扩展词库

### 1. 只用 JSON：复用已有行为

JSON 适合增加别名、修改文案，或将新成语指向一个已有运行时：

```json
{
  "version": 1,
  "idioms": {
    "云里雾里": {
      "category": "自定义别名",
      "py": "复用不知所云的随机乱码实现",
      "egg": "print('☁️ 雾又浓了三分。')",
      "runtime": "不知所云"
    }
  }
}
```

```bash
chengyulang run your_program.cy --catalog examples/custom_idioms.json
```

词库结构定义在
[`chengyulang/data/idioms.schema.json`](chengyulang/data/idioms.schema.json)。

### 2. Python 注册：增加全新行为

JSON 不执行任意代码。需要新行为时，显式注册一个可信 Python 函数：

```python
from chengyulang import 执行, 注册成语

注册成语(
    "一鼓作气",
    lambda 数字: 数字 + 1,
    py="数字 + 1",
    egg="鼓.响(); 气.盛()",
)

执行('列(一鼓作气(41))')
```

完整示例见 [`examples/plugin_demo.py`](examples/plugin_demo.py)。为兼容最初构想，
也可以直接调用 `成语词典.update(...)`；新增可执行行为仍建议使用 `注册成语()`。

```bash
python -m examples.plugin_demo
```

## 安全边界

成语语不是安全沙箱。`.cy` 源码最终会经 `compile()` 和 `exec()` 作为 Python
执行，因此只能运行自己编写或已经审查的源码。

`check` 和 `compile` 只进行翻译、AST 验证及文件生成，不会执行源码；`run` 及
生成后的 `.py` 文件则拥有当前 Python 进程的权限。

内置的高风险脑洞已经降为无副作用实现：

- `开天辟地` 不会创建 `/`，只返回 `mkdir` 模拟计划；
- `后羿射日` 不会发送进程信号，只返回 `kill` 模拟计划；
- `嫦娥奔月` 不会部署，只返回部署模拟计划；
- `对牛弹琴` 最长只等待 1 秒；
- `夸父追日` 强制设置迭代上限；
- `暗度陈仓` 只能导入标准库白名单中的模块。

详见 [SECURITY.md](SECURITY.md)。

## 测试

```bash
python -m unittest discover -s tests -v
python -m compileall -q chengyulang chengyu_lang.py
```

## 项目定位

这是一个偏 esolang、DSL 和中文分词幽默的实验项目，而不是生产语言。适合：

- 演示编译前端、Token 化和 DSL 设计；
- 做中文语义双关与编程梗；
- 继续扩展 AST、REPL、编辑器高亮或插件机制。


## AI 辅助创作声明

本项目的核心创意、产品方向、语言机制与主要技术决策由项目作者提出并主导。
开发过程中使用了生成式 AI 辅助头脑风暴、方案整理、部分代码实现、测试设计及
中英文文档编写。所有 AI 辅助生成的内容均由项目作者进行人工审阅、修改与测试；
项目作者对最终发布内容、技术取舍及潜在问题承担责任。

如提交由生成式 AI 实质性辅助完成的代码或文档，欢迎贡献者在 Pull Request 中
如实说明使用范围，并自行完成必要的审阅、测试及许可证兼容性检查。

## License

[MIT](LICENSE)
