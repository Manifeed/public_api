from __future__ import annotations


def render_crawler_rss_install_script() -> str:
    return _SCRIPT


_SCRIPT = '''#!/usr/bin/env sh
# Installs crawler_rss from https://github.com/Manifeed/workers/releases (latest).
set -eu
MANIFEEG_GITHUB_REPO="${MANIFEEG_GITHUB_REPO:-Manifeed/workers}"
UA="Manifeed-curl-install/1.0"
case "$(uname -s)" in
	Linux) mf_os=linux ;;
	Darwin) mf_os=macos ;;
	MSYS*|MINGW*|CYGWIN*) mf_os=windows ;;
	*) echo "Unsupported operating system: $(uname -s)" >&2; exit 1 ;;
esac
mf_arch="$(uname -m)"
case "$mf_arch" in
	x86_64|amd64) mf_arch=x86_64 ;;
	aarch64|arm64) mf_arch=aarch64 ;;
	armv7l|armv6l|arm) mf_arch=arm ;;
	*) echo "Unsupported CPU architecture: $mf_arch" >&2; exit 1 ;;
esac
mf_target="$mf_os-$mf_arch"
if ! command -v python3 >/dev/null 2>&1; then
	echo "python3 is required to resolve the GitHub release metadata." >&2
	exit 1
fi
RELEASE_JSON="$(curl -fsSL -H "User-Agent: $UA" "https://api.github.com/repos/$MANIFEEG_GITHUB_REPO/releases/latest")" || exit 1
_PAIR="$(printf '%s' "$RELEASE_JSON" | python3 -c "
import json, sys
j = json.load(sys.stdin)
t = j['tag_name'].lstrip('v')
tgt = sys.argv[1]
want = 'crawler_rss_bundle-' + t + '-' + tgt + '.tar.gz'
url = ''
sha = ''
for a in j.get('assets', []):
    n = a.get('name', '')
    if n == want:
        url = a.get('browser_download_url', '')
    if n == want + '.sha256':
        sha = a.get('browser_download_url', '')
if not url or not sha:
    sys.stderr.write('No matching bundle for ' + tgt + ' on this release.\\n')
    sys.exit(2)
print(url)
print(sha)
" "$mf_target")" || exit 1
ARCHIVE_URL="$(printf '%s\\n' "$_PAIR" | sed -n '1p')"
SHA_URL="$(printf '%s\\n' "$_PAIR" | sed -n '2p')"
TMPROOT="$(mktemp -d)"
trap 'rm -rf "$TMPROOT"' EXIT INT HUP
curl -fsSL -H "User-Agent: $UA" "$ARCHIVE_URL" -o "$TMPROOT/bundle.tar.gz"
curl -fsSL -H "User-Agent: $UA" "$SHA_URL" -o "$TMPROOT/bundle.sha256"
expected="$(awk 'NR==1{print tolower($1)}' "$TMPROOT/bundle.sha256")"
actual="$(openssl dgst -sha256 "$TMPROOT/bundle.tar.gz" | awk '{print tolower($2)}')"
if [ "$expected" != "$actual" ]; then
	echo "SHA-256 verification failed for the downloaded bundle." >&2
	exit 1
fi
if [ "$mf_os" = "linux" ]; then
	INSTALL_ROOT="${XDG_DATA_HOME:-$HOME/.local/share}/manifeed/crawler_rss"
	LINK_DIR="${XDG_BIN_HOME:-$HOME/.local/bin}"
elif [ "$mf_os" = "macos" ]; then
	INSTALL_ROOT="$HOME/Library/Application Support/Manifeed/crawler_rss"
	LINK_DIR="$HOME/Library/Application Support/Manifeed/bin"
else
	INSTALL_ROOT="${LOCALAPPDATA:-$HOME/AppData/Local}/Manifeed/crawler_rss"
	LINK_DIR="$INSTALL_ROOT/bin"
fi
STAGING="$INSTALL_ROOT/staging.$$"
rm -rf "$STAGING"
mkdir -p "$STAGING" "$INSTALL_ROOT" "$LINK_DIR"
tar -xzf "$TMPROOT/bundle.tar.gz" -C "$STAGING"
bundle_dir=""
for d in "$STAGING"/crawler_rss_bundle-*; do
	if [ -d "$d" ]; then
		bundle_dir="$d"
		break
	fi
done
if [ -z "$bundle_dir" ]; then
	echo "Unexpected archive layout." >&2
	exit 1
fi
rm -rf "$INSTALL_ROOT/current"
mv "$bundle_dir" "$INSTALL_ROOT/current"
if [ "$mf_os" = "windows" ]; then
	CLI="$INSTALL_ROOT/current/bin/crawler_rss.exe"
	cp "$CLI" "$LINK_DIR/crawler_rss.exe" 2>/dev/null || true
else
	CLI="$INSTALL_ROOT/current/bin/crawler_rss"
	chmod 0755 "$CLI" 2>/dev/null || true
	ln -sf "$CLI" "$LINK_DIR/crawler_rss" 2>/dev/null || cp "$CLI" "$LINK_DIR/crawler_rss"
fi
echo "Installed crawler_rss to $CLI"
echo "Next steps:"
echo "  1) ensure $LINK_DIR is on your PATH"
echo "  2) crawler_rss set --api-key \\"mk_...\\" --concurrency 10"
echo "  3) crawler_rss"
'''
