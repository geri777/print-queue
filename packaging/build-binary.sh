#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
project_dir=$(dirname "$script_dir")
python_path=${1:-"$project_dir/.venv/bin/python"}

if [[ ! -x "$python_path" ]]; then
    echo "Python was not found in the project virtual environment: $python_path" >&2
    echo "Create the virtual environment and install the project as described in README.md." >&2
    exit 2
fi

if ! command -v gcc >/dev/null; then
    echo "gcc is missing. Install it first: sudo apt install build-essential" >&2
    exit 2
fi

"$python_path" -m pip install "Nuitka>=4,<5" ordered-set zstandard patchelf
python_bin_dir=$(dirname "$python_path")
export PATH="$python_bin_dir:$PATH"
if ! command -v patchelf >/dev/null; then
    echo "patchelf is not available. Install it with: sudo apt install patchelf" >&2
    exit 2
fi

mkdir -p "$project_dir/build" "$project_dir/dist"
build_dir=$(mktemp -d -p "$project_dir/build" printqueue-nuitka-XXXXXX)
cleanup() {
    if [[ "$build_dir" == "$project_dir"/build/printqueue-nuitka-* ]]; then
        rm -rf -- "$build_dir"
    fi
}
trap cleanup EXIT

cd "$project_dir"
PYTHONPATH="$project_dir/src" "$python_path" -m nuitka \
    "$project_dir/src/printqueue/main.py" \
    --follow-imports \
    --enable-plugin=pyside6 \
    --onefile \
    --output-dir="$build_dir" \
    --output-filename=printqueue.bin \
    --noinclude-qt-translations \
    --include-qt-plugins=networkinformation,platforminputcontexts

built_binary="$build_dir/printqueue.bin"
if [[ ! -x "$built_binary" ]]; then
    echo "Nuitka finished, but the expected binary is missing: $built_binary" >&2
    exit 1
fi

install -Dm755 "$built_binary" "$project_dir/dist/printqueue.bin"
echo "Created: $project_dir/dist/printqueue.bin"
