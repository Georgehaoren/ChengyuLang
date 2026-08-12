# ChengyuLang (成语语)

[简体中文](README.md)

> Change the spacing; change the meaning.

ChengyuLang is an experimental, Python-backed Chinese DSL. A connected idiom
invokes normal behavior, while the same idiom split into single-character
tokens triggers an Easter egg.

```python
结果 = 色令智昏(3 > 1)  # not bool(3 > 1)
列(结果)                 # print(结果)

色 令 智 昏             # Easter egg, then an intentional friendly error
```

The project currently ships 52 idioms. The original blueprint said 50 but
contained 51; `不知所云` was then added as the 52nd entry. Its connected form
returns random, printable mojibake-style text, while `不 知 所 云` triggers a
cloud-themed egg.

## Quick start

Python 3.10 or newer is required. There are no runtime dependencies.

```bash
chmod +x setup_venv.sh
./setup_venv.sh
source .venv/bin/activate

python chengyu_lang.py
python -m chengyulang demo
python -m chengyulang check examples/demo.cy
python -m chengyulang compile examples/demo.cy
python examples/demo.py
python -m chengyulang run examples/demo.cy --show-python
```

Install the CLI locally if desired:

```bash
python -m pip install -e .
chengyulang run examples/demo.cy
```

`setup_venv.sh` creates or reuses `.venv`, installs the checkout in editable
mode, and runs version and compiler checks. An alternate environment path or
Python executable can be selected explicitly:

```bash
./setup_venv.sh /path/to/venv
CHENGYULANG_PYTHON=python3.12 ./setup_venv.sh
```

Set `CHENGYULANG_OFFLINE=1` to prohibit build-tool downloads when the venv
already contains pip 21.3+, setuptools 68+, and wheel.

## Syntax

| ChengyuLang | Python |
| --- | --- |
| `项 之于 列表:` | `for 项 in 列表:` |
| `若 条件:` | `if 条件:` |
| `如是 条件:` | `elif 条件:` |
| `否则:` | `else:` |
| `列(值)` | `print(值)` |
| `成语(...)` | registered runtime call |
| `成 语 (...)` | Easter egg call |

Translation is token-aware: strings and comments remain untouched, and nested
parentheses do not need to be parsed with a fragile regular expression.

## Console compiler

The first-stage compiler produces deterministic Python source that can be run
directly in an environment where ChengyuLang is installed:

```bash
chengyulang check examples/demo.cy
chengyulang compile examples/demo.cy --show-stages
python examples/demo.py
```

Useful options include:

- `-o OUT.py` to select an output path;
- `--stdout` to emit complete generated Python;
- `--json` for machine-readable stages, matches, and diagnostics;
- `--catalog extra.json` to compile with a JSON extension;
- `--force` to explicitly overwrite an existing output.

`check` and `compile` never execute the input program. The legacy `translate`
command emits only the internal Python body and is intended for debugging.

## Modular design

- `data/idioms.json`: JSON metadata for all bundled idioms
- `catalog.py`: loading, validation, and merging
- `translator.py`: egg-first token translation
- `compiler.py`: AST validation, code generation, and atomic output writes
- `diagnostics.py`: structured diagnostics and console rendering
- `bootstrap.py`: reproducible generated runtime prelude
- `runtime.py`: safe implementations and plugin registration
- `executor.py`: compile/exec and localized errors
- `cli.py`: `check`, `compile`, `translate`, `run`, `catalog`, and `demo`

## Extending

Use a JSON extension to add aliases or reuse a registered runtime:

```bash
chengyulang run program.cy --catalog examples/custom_idioms.json
```

For new executable behavior, register trusted Python code explicitly:

```python
from chengyulang import 注册成语

注册成语(
    "一鼓作气",
    lambda value: value + 1,
    py="value + 1",
    egg="鼓.响(); 气.盛()",
)
```

See [`examples/plugin_demo.py`](examples/plugin_demo.py) and the bundled
[`idioms.schema.json`](chengyulang/data/idioms.schema.json).

```bash
python -m examples.plugin_demo
```

## Security

ChengyuLang is not a sandbox. Trusted `.cy` source is compiled and executed as
Python. Never run unreviewed source. Dangerous ideas from the original prompt,
including root-directory creation and process termination, are implemented as
dry-run plans and do not perform those actions. See [SECURITY.md](SECURITY.md).

## Test

```bash
python -m unittest discover -s tests -v
```

## AI-Assisted Creation Notice

The project's core concept, product direction, language mechanics, and major
technical decisions were proposed and directed by the project author.
Generative AI was used to assist with brainstorming, design organization,
parts of the implementation, test design, and Chinese/English documentation.
All AI-assisted material was reviewed, revised, and tested by the project
author, who remains responsible for the released content, technical decisions,
and potential issues.

Contributors are encouraged to disclose materially AI-assisted code or
documentation in their pull requests and remain responsible for reviewing,
testing, and checking the license compatibility of their contributions.

Licensed under the [MIT License](LICENSE).
