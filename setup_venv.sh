#!/usr/bin/env bash

# Create a local virtual environment and install ChengyuLang from this checkout.
# Usage: ./setup_venv.sh [VENV_PATH]

set -Eeuo pipefail

readonly SCRIPT_DIR="$(
    CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1
    pwd -P
)"

if (( $# > 1 )); then
    printf 'Usage: %s [VENV_PATH]\n' "${0##*/}" >&2
    exit 2
fi
if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    cat <<EOF
Usage: ${0##*/} [VENV_PATH]

Create or reuse a Python virtual environment and install ChengyuLang from
this repository in editable mode. VENV_PATH defaults to .venv.

Environment variables:
  CHENGYULANG_PYTHON   Python 3.10+ executable to use
  CHENGYULANG_VENV     Default venv path when VENV_PATH is omitted
  CHENGYULANG_OFFLINE  Set to 1 to prohibit build-tool downloads
EOF
    exit 0
fi

readonly VENV_DIR="${1:-${CHENGYULANG_VENV:-${SCRIPT_DIR}/.venv}}"
readonly MIN_PYTHON_MAJOR=3
readonly MIN_PYTHON_MINOR=10

info() {
    printf '==> %s\n' "$*"
}

fail() {
    printf 'Error: %s\n' "$*" >&2
    exit 1
}

find_python() {
    local candidate

    if [[ -n "${CHENGYULANG_PYTHON:-}" ]]; then
        command -v "${CHENGYULANG_PYTHON}" >/dev/null 2>&1 || \
            fail "CHENGYULANG_PYTHON is not executable: ${CHENGYULANG_PYTHON}"
        printf '%s\n' "${CHENGYULANG_PYTHON}"
        return
    fi

    for candidate in python3.13 python3.12 python3.11 python3.10 python3 python; do
        if command -v "${candidate}" >/dev/null 2>&1 && \
            "${candidate}" -c \
                'import sys; raise SystemExit(sys.version_info < (3, 10))'
        then
            printf '%s\n' "${candidate}"
            return
        fi
    done

    fail "Python ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}+ was not found."
}

readonly BASE_PYTHON="$(find_python)"

"${BASE_PYTHON}" - "${MIN_PYTHON_MAJOR}" "${MIN_PYTHON_MINOR}" <<'PY'
import sys

required = (int(sys.argv[1]), int(sys.argv[2]))
if sys.version_info < required:
    current = ".".join(map(str, sys.version_info[:3]))
    print(
        f"Error: Python {required[0]}.{required[1]}+ is required; "
        f"found {current}.",
        file=sys.stderr,
    )
    raise SystemExit(1)
PY

if [[ -e "${VENV_DIR}" && ! -f "${VENV_DIR}/pyvenv.cfg" ]]; then
    fail "Target exists but is not a Python virtual environment: ${VENV_DIR}"
fi

if [[ ! -f "${VENV_DIR}/pyvenv.cfg" ]]; then
    info "Creating virtual environment: ${VENV_DIR}"
    "${BASE_PYTHON}" -m venv "${VENV_DIR}"
else
    info "Reusing virtual environment: ${VENV_DIR}"
fi

if [[ -x "${VENV_DIR}/bin/python" ]]; then
    readonly VENV_PYTHON="${VENV_DIR}/bin/python"
    readonly VENV_CHENGYULANG="${VENV_DIR}/bin/chengyulang"
    readonly ACTIVATE_PATH="${VENV_DIR}/bin/activate"
elif [[ -x "${VENV_DIR}/Scripts/python.exe" ]]; then
    readonly VENV_PYTHON="${VENV_DIR}/Scripts/python.exe"
    readonly VENV_CHENGYULANG="${VENV_DIR}/Scripts/chengyulang.exe"
    readonly ACTIVATE_PATH="${VENV_DIR}/Scripts/activate"
else
    fail "The virtual environment has no usable Python executable: ${VENV_DIR}"
fi

build_tools_ready() {
    "${VENV_PYTHON}" - <<'PY'
import re
from importlib.metadata import PackageNotFoundError, version


def version_tuple(package):
    try:
        value = version(package)
    except PackageNotFoundError:
        return (0, 0)
    numbers = [int(part) for part in re.findall(r"\d+", value)[:2]]
    return tuple((numbers + [0, 0])[:2])


requirements = {
    "pip": (21, 3),
    "setuptools": (68, 0),
    "wheel": (0, 1),
}
if any(version_tuple(name) < minimum for name, minimum in requirements.items()):
    raise SystemExit(1)
PY
}

readonly OFFLINE_MODE="${CHENGYULANG_OFFLINE:-${CHENGYULANG_SKIP_PIP_UPGRADE:-0}}"

if build_tools_ready; then
    info "Build tooling is ready"
elif [[ "${OFFLINE_MODE}" == "1" ]]; then
    "${VENV_PYTHON}" - <<'PY'
try:
    from importlib.metadata import version
    found = ", ".join(
        f"{name}={version(name)}" for name in ("pip", "setuptools", "wheel")
    )
except Exception:
    found = "one or more tools missing"
print(f"Detected: {found}")
PY
    fail "Offline mode requires pip>=21.3, setuptools>=68, and wheel."
else
    info "Installing or upgrading build tooling"
    PIP_DISABLE_PIP_VERSION_CHECK=1 "${VENV_PYTHON}" -m pip install --upgrade \
        "pip>=21.3" "setuptools>=68" wheel
fi

info "Installing ChengyuLang in editable mode"
PIP_ARGS=(--no-build-isolation --editable "${SCRIPT_DIR}")
if [[ "${OFFLINE_MODE}" == "1" ]]; then
    PIP_ARGS=(--no-index "${PIP_ARGS[@]}")
fi
PIP_DISABLE_PIP_VERSION_CHECK=1 \
    "${VENV_PYTHON}" -m pip install "${PIP_ARGS[@]}"

info "Verifying the installation"
"${VENV_PYTHON}" -m chengyulang --version
"${VENV_PYTHON}" -m chengyulang check \
    "${SCRIPT_DIR}/examples/demo.cy" --quiet

printf '\nChengyuLang is ready.\n'
printf 'Activate the environment with:\n  source "%s"\n' "${ACTIVATE_PATH}"
printf 'Or run it directly with:\n  "%s" demo\n' "${VENV_CHENGYULANG}"
