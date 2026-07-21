#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
    echo "Verwendung: $0 PFAD_ZUM_BINARY [VERSION]" >&2
    exit 2
fi

binary_path=$(realpath "$1")
package_version=${2:-0.1.0}
if [[ ! -x "$binary_path" ]]; then
    echo "Binary ist nicht vorhanden oder nicht ausführbar: $binary_path" >&2
    exit 2
fi
if ! command -v dpkg-deb >/dev/null; then
    echo "dpkg-deb ist nicht installiert." >&2
    exit 2
fi

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
project_dir=$(dirname "$script_dir")
architecture=$(dpkg --print-architecture)
stage_dir=$(mktemp -d -t printqueue-deb-XXXXXX)
cleanup() {
    if [[ "$stage_dir" == /tmp/printqueue-deb-* ]]; then
        rm -rf -- "$stage_dir"
    fi
}
trap cleanup EXIT

install -Dm755 "$binary_path" "$stage_dir/usr/bin/printqueue"
install -Dm644 "$project_dir/resources/org.printqueue.PrintQueue.desktop" \
    "$stage_dir/usr/share/applications/org.printqueue.PrintQueue.desktop"
install -Dm644 "$project_dir/resources/dolphin/printqueue-servicemenu.desktop" \
    "$stage_dir/usr/share/kio/servicemenus/printqueue-servicemenu.desktop"
install -Dm644 "$project_dir/README.md" \
    "$stage_dir/usr/share/doc/printqueue/README.md"

mkdir -p "$stage_dir/DEBIAN" "$project_dir/dist"
sed \
    -e "s/@VERSION@/$package_version/g" \
    -e "s/@ARCH@/$architecture/g" \
    "$script_dir/control.in" > "$stage_dir/DEBIAN/control"

output="$project_dir/dist/printqueue_${package_version}_${architecture}.deb"
dpkg-deb --root-owner-group --build "$stage_dir" "$output"
echo "Erzeugt: $output"

