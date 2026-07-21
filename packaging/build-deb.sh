#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
    echo "Usage: $0 PATH_TO_BINARY [VERSION]" >&2
    exit 2
fi

binary_path=$(realpath "$1")
package_version=${2:-0.1.0}
if [[ ! -x "$binary_path" ]]; then
    echo "Binary does not exist or is not executable: $binary_path" >&2
    exit 2
fi
if ! command -v dpkg-deb >/dev/null; then
    echo "dpkg-deb is not installed." >&2
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
install -Dm644 "$project_dir/README.md" \
    "$stage_dir/usr/share/doc/printqueue/README.md"

mkdir -p "$stage_dir/DEBIAN" "$project_dir/dist"
sed \
    -e "s/@VERSION@/$package_version/g" \
    -e "s/@ARCH@/$architecture/g" \
    "$script_dir/control.in" > "$stage_dir/DEBIAN/control"

output="$project_dir/dist/printqueue_${package_version}_${architecture}.deb"
dpkg-deb --root-owner-group --build "$stage_dir" "$output"
echo "Created: $output"

dolphin_stage=$(mktemp -d -t printqueue-dolphin-deb-XXXXXX)
nautilus_stage=$(mktemp -d -t printqueue-nautilus-deb-XXXXXX)
cleanup_integrations() {
    if [[ "$dolphin_stage" == /tmp/printqueue-dolphin-deb-* ]]; then
        rm -rf -- "$dolphin_stage"
    fi
    if [[ "$nautilus_stage" == /tmp/printqueue-nautilus-deb-* ]]; then
        rm -rf -- "$nautilus_stage"
    fi
}
trap 'cleanup_integrations; cleanup' EXIT

install -Dm644 "$project_dir/resources/dolphin/printqueue-servicemenu.desktop" \
    "$dolphin_stage/usr/share/kio/servicemenus/printqueue-servicemenu.desktop"
mkdir -p "$dolphin_stage/DEBIAN"
sed -e "s/@VERSION@/$package_version/g" \
    "$script_dir/control.dolphin.in" > "$dolphin_stage/DEBIAN/control"
dolphin_output="$project_dir/dist/printqueue-dolphin_${package_version}_all.deb"
dpkg-deb --root-owner-group --build "$dolphin_stage" "$dolphin_output"
echo "Created: $dolphin_output"

install -Dm644 "$project_dir/resources/nautilus/printqueue.py" \
    "$nautilus_stage/usr/share/nautilus-python/extensions/printqueue.py"
mkdir -p "$nautilus_stage/DEBIAN"
sed -e "s/@VERSION@/$package_version/g" \
    "$script_dir/control.nautilus.in" > "$nautilus_stage/DEBIAN/control"
nautilus_output="$project_dir/dist/printqueue-nautilus_${package_version}_all.deb"
dpkg-deb --root-owner-group --build "$nautilus_stage" "$nautilus_output"
echo "Created: $nautilus_output"
