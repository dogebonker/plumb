#!/usr/bin/env bash
# LAY-01: every layout checker pinned in kit/layouts/tools.yaml enforces a layer rule. No model.
# For each checker: confirm its pins appear in its tools.yaml entry, install them into a fresh temp dir, copy
# <checker>/fixture there, run the tool's `command` from tools.yaml on the clean tree, add <checker>/planted (new files
# across the forbidden boundary), and run it again. Expect: clean exits 0, planted exits non-zero, the planted output
# carries the rule's signature (absent from the clean output) and names every planted file.
# cargo-modules is not tested: it checks module cycles, not layer direction.
# Nothing is installed globally (package-manager caches aside) and the repository is not modified. Build trees are
# deleted on exit; logs stay in the temp dir.
# Exit: 0 all ok, 1 a check failed, 2 nothing failed but a stack was skipped (LAY01_ALLOW_SKIP=1 makes that 0).
set -u

HERE=$(cd "$(dirname "$0")" && pwd)
TOOLS="$HERE/../../kit/layouts/tools.yaml"
WORK=$(mktemp -d "${TMPDIR:-/tmp}/lay01.XXXXXX")
trap 'rm -rf "$WORK"/*/tree' EXIT
START=$(date +%s)
FAILED=0
SKIPPED=0
SUMMARY=()

echo "LAY-01 logs: $WORK"

# The lines of <stack>.<tool> in tools.yaml.
entry_of() {
  awk -v stack="$1:" -v tool="$2:" '
    /^[^ #]/ { in_stack = ($1 == stack); in_tool = 0 }
    in_stack && /^  [^ #]/ { in_tool = ($1 == tool) }
    in_stack && in_tool
  ' "$TOOLS"
}

# Its `command:`, trailing comment removed.
command_of() { entry_of "$1" "$2" | sed -n 's/^    command: *//p' | sed 's/ \{1,\}#.*$//'; }

tail_of() { echo "    --- tail of $1"; tail -n 15 "$1" | sed 's/^/    | /'; }

# Pins per checker, each of which must appear in the checker's tools.yaml entry.
PINS_dependency_cruiser="dependency-cruiser@18.4.0 typescript@6.0.3"
PINS_eslint_plugin_boundaries="eslint-plugin-boundaries@7.2.0 eslint@10.11.0 @typescript-eslint/parser@8.71.0 eslint-import-resolver-typescript@4.4.5 typescript@6.0.3"
PINS_eslint_plugin_import_x="eslint-plugin-import-x@4.17.1 eslint@10.11.0 @typescript-eslint/parser@8.71.0 eslint-import-resolver-typescript@4.4.5 typescript@6.0.3"
PINS_steiger="steiger@0.7.0 @feature-sliced/steiger-plugin@0.8.0"
PINS_import_linter="import-linter==2.15"
PINS_tach="tach==0.35.1"
PINS_go_compiler=""
PINS_go_arch_lint="github.com/fe3dback/go-arch-lint@v1.19.0"
PINS_cargo=""

# Install functions run inside the copied fixture, with the pins as arguments.
npm_dev() { npm install --no-audit --no-fund --save-dev --save-exact "$@"; }
py_dev() {
  if command -v uv >/dev/null; then
    uv venv -q --python 3.12 .venv && uv pip install --python .venv/bin/python "$@"
  else
    python3 -m venv .venv && .venv/bin/pip install -q "$@"
  fi
}
install_dependency_cruiser()       { npm_dev "$@"; }
install_eslint_plugin_boundaries() { npm_dev "$@"; }
install_eslint_plugin_import_x()   { npm_dev "$@"; }
install_steiger()                  { npm_dev "$@"; }
# import-linter's root package must be importable, so the project itself is installed, as `uv sync` would.
install_import_linter()            { py_dev "$@" -e .; }
install_tach()                     { py_dev "$@"; }
install_go_compiler()              { :; }
install_go_arch_lint()             { go get -tool "$1"; }
install_cargo()                    { :; }

# check <dir under checkers/> <stack> <tool in tools.yaml> <rule signature> [module name the output may use instead
# of the path, for a single planted file]
check() {
  local name=$1 stack=$2 tool=$3 sig=$4 alt=${5:-}
  local id=${name//-/_} dir="$WORK/$name/tree" log="$WORK/$name" t0 cmd entry pins pin file rc_clean rc_planted
  local names=yes signature=yes verdict=ok
  t0=$(date +%s)
  mkdir -p "$log"
  export GOTOOLCHAIN=local CARGO_TARGET_DIR="$dir/target"

  entry=$(entry_of "$stack" "$tool")
  cmd=$(command_of "$stack" "$tool")
  if [ -z "$cmd" ]; then
    SUMMARY+=("$name: FAIL no command for $stack.$tool in tools.yaml"); FAILED=1; return
  fi
  pins="PINS_$id"
  for pin in ${!pins}; do
    if ! grep -qF -- "$pin" <<<"$entry"; then
      SUMMARY+=("$name: FAIL pin $pin is not in tools.yaml $stack.$tool"); FAILED=1; return
    fi
  done

  cp -R "$HERE/$name/fixture" "$dir"
  # shellcheck disable=SC2086 # pins are space-separated words
  if ! (cd "$dir" && "install_$id" ${!pins}) >"$log/install.log" 2>&1; then
    SUMMARY+=("$name: FAIL install ($(($(date +%s) - t0))s)"); FAILED=1
    tail_of "$log/install.log"; return
  fi

  (cd "$dir" && PATH="$dir/.venv/bin:$PATH" eval "$cmd") >"$log/clean.log" 2>&1; rc_clean=$?
  cp -R "$HERE/$name/planted/." "$dir/"
  (cd "$dir" && PATH="$dir/.venv/bin:$PATH" eval "$cmd") >"$log/planted.log" 2>&1; rc_planted=$?

  while IFS= read -r file; do
    grep -qF -- "$file" "$log/planted.log" && continue
    if [ -n "$alt" ] && grep -qF -- "$alt" "$log/planted.log"; then names="yes, as $alt"; else names=no; fi
  done < <(cd "$HERE/$name/planted" && find . -type f | sed 's|^\./||')
  if ! grep -qF -- "$sig" "$log/planted.log" || grep -qF -- "$sig" "$log/clean.log"; then signature=no; fi

  [ "$rc_clean" -eq 0 ] || { verdict=FAIL; tail_of "$log/clean.log"; }
  if [ "$rc_planted" -eq 0 ] || [ "$names" = no ] || [ "$signature" = no ]; then
    verdict=FAIL; tail_of "$log/planted.log"
  fi
  [ "$verdict" = ok ] || FAILED=1
  SUMMARY+=("$name: $verdict clean=exit $rc_clean, planted=exit $rc_planted, signature '$sig': $signature, names planted files: $names ($(($(date +%s) - t0))s) [$cmd]")
}

skip() { SUMMARY+=("$1: SKIP $2"); SKIPPED=$((SKIPPED + 1)); }

if command -v node >/dev/null && command -v npm >/dev/null; then
  check dependency-cruiser typescript dependency-cruiser domain-not-to-adapters
  check eslint-plugin-boundaries typescript eslint-plugin-boundaries boundaries/dependencies
  check eslint-plugin-import-x typescript eslint-plugin-import-x import-x/no-restricted-paths
  check steiger typescript steiger fsd/forbidden-imports
else
  for c in dependency-cruiser eslint-plugin-boundaries eslint-plugin-import-x steiger; do skip "$c" "node/npm not found"; done
fi

if command -v uv >/dev/null || command -v python3 >/dev/null; then
  check import-linter python import-linter "is not allowed to import" shop.domain.leak
  check tach python tach "cannot depend on"
else
  skip import-linter "python3/uv not found"; skip tach "python3/uv not found"
fi

if command -v go >/dev/null; then
  check go-compiler go compiler "use of internal package"
  check go-arch-lint go go-arch-lint "shouldn't depend on"
else
  skip go-compiler "go not found"; skip go-arch-lint "go not found"
fi

if command -v cargo >/dev/null; then
  check cargo rust cargo E0432
else
  skip cargo "cargo not found"
fi

echo
printf '%s\n' "${SUMMARY[@]}"
echo "node $(node --version 2>/dev/null || echo 'not found'), total $(($(date +%s) - START))s, logs in $WORK"
[ "$FAILED" -eq 0 ] || exit 1
if [ "$SKIPPED" -gt 0 ] && [ "${LAY01_ALLOW_SKIP:-0}" != 1 ]; then
  echo "$SKIPPED checker(s) skipped; set LAY01_ALLOW_SKIP=1 to accept"; exit 2
fi
exit 0
