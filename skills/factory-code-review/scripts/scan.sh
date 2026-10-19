#!/usr/bin/env bash
# Adapted from bug-review: scanner output is leads, never a passing gate.
# Usage: [UNTRUSTED=1] scan.sh [base-ref]
set -o pipefail
set -f
root=$(git rev-parse --show-toplevel 2>/dev/null) || { echo 'gap: not a Git repository'; exit 0; }
cd "$root" || exit 0
base=${1:-}
if [ -z "$base" ]; then
  for candidate in origin/HEAD origin/main main master; do
    if git rev-parse --verify --end-of-options "$candidate^{commit}" >/dev/null 2>&1; then base=$candidate; break; fi
  done
fi
base_commit=$(git rev-parse --verify --end-of-options "$base^{commit}" 2>/dev/null) || {
  printf 'gap: cannot resolve base %q to a commit\n' "$base"; exit 0;
}
mb=$(git merge-base "$base_commit" HEAD 2>/dev/null) || {
  echo 'gap: no merge-base; fetch the required history before reviewing'; exit 0;
}
inventory=$(mktemp) || { echo 'gap: cannot create inventory'; exit 0; }
trap 'rm -f "$inventory"' EXIT
if ! git diff --name-only -z --diff-filter=ACMR "$mb" -- > "$inventory" ||
   ! git diff --cached --name-only -z --diff-filter=ACMR "$mb" -- >> "$inventory" ||
   ! git diff --name-only -z --diff-filter=ACMR HEAD -- >> "$inventory" ||
   ! git ls-files --others --exclude-standard -z >> "$inventory"; then
  echo 'gap: cannot inventory changes'; exit 0
fi
index_status=0
git diff --quiet -- || index_status=$?
if [ "$index_status" -eq 1 ]; then
  echo 'gap: index differs from working tree; staged bytes are not scanned. Review the index diff separately.'
elif [ "$index_status" -ne 0 ]; then
  echo 'gap: cannot compare index and working tree'; exit 0
fi
files=()
missing=0
while IFS= read -r -d '' file; do
  # Prefix every target, so names beginning with '-' cannot become tool options.
  file=./$file
  if [ -L "$file" ]; then
    printf 'gap: symlink target not scanned: %q\n' "$file"
    missing=1
    continue
  fi
  if [ ! -f "$file" ]; then
    printf 'gap: selected file missing from working tree: %q; staged bytes are not scanned\n' "$file"
    missing=1
    continue
  fi
  duplicate=0
  for seen in "${files[@]}"; do [ "$seen" != "$file" ] || duplicate=1; done
  [ "$duplicate" -eq 1 ] || files+=("$file")
done < "$inventory"
if [ ${#files[@]} -eq 0 ]; then
  [ "$missing" -eq 1 ] || echo 'scan: no changed files'
  exit 0
fi
printf '# Scanner leads: %s changed files; base %s\n' "${#files[@]}" "$mb"
echo 'Exit 0 means collection finished, not that checks passed. Confirm every lead against code.'

has() { command -v "$1" >/dev/null 2>&1; }
section() { printf '\n## %s\n' "$1"; }
run() {
  local status=0 label=$1
  shift
  "$@" 2>&1 || status=$?
  [ "$status" -eq 0 ] || printf 'lead/gap: %s exited %s (findings or tool failure; inspect output)\n' "$label" "$status"
  return 0
}
py=(); sh=(); wf=(); js=(); go_files=(); rs=()
for file in "${files[@]}"; do
  case "$file" in *.py) py+=("$file");; esac
  case "$file" in *.sh|*.bash) sh+=("$file");; esac
  case "$file" in ./.github/workflows/*.yml|./.github/workflows/*.yaml) wf+=("$file");; esac
  case "$file" in *.js|*.jsx|*.ts|*.tsx|*.mjs|*.cjs) js+=("$file");; esac
  case "$file" in *.go) go_files+=("$file");; esac
  case "$file" in *.rs) rs+=("$file");; esac
done
section gitleaks
if has gitleaks; then
  for file in "${files[@]}"; do run gitleaks gitleaks detect --no-git --no-banner --no-color --redact -v -s "$file"; done
else echo 'skipped: not installed'; fi
section semgrep
if has semgrep && semgrep --version >/dev/null 2>&1; then
  run semgrep semgrep scan --config p/default --metrics off --quiet "${files[@]}"
else echo 'skipped: not installed or broken (semgrep --version fails)'; fi
section ruff
if [ ${#py[@]} -eq 0 ]; then echo 'skipped: no Python changes'
elif has ruff; then
  if ruff --version >/dev/null 2>&1; then
    run ruff ruff check --no-fix --extend-select B,S,ASYNC,BLE --output-format concise "${py[@]}"
  else echo 'skipped: ruff not runnable here'; fi
else echo 'skipped: not installed'; fi
section shellcheck
if [ ${#sh[@]} -eq 0 ]; then echo 'skipped: no shell changes'
elif has shellcheck; then run shellcheck shellcheck -f gcc "${sh[@]}"
else echo 'skipped: not installed'; fi
section actionlint
if [ ${#wf[@]} -eq 0 ]; then echo 'skipped: no workflow changes'
elif has actionlint; then run actionlint actionlint "${wf[@]}"
else echo 'skipped: not installed'; fi
section eslint/biome
if [ ${#js[@]} -eq 0 ]; then echo 'skipped: no JS/TS changes'
elif [ -n "${UNTRUSTED:-}" ]; then echo 'skipped: UNTRUSTED set (runs repo JS)'
elif [ -x node_modules/.bin/biome ]; then run biome node_modules/.bin/biome lint "${js[@]}"
elif [ -x node_modules/.bin/eslint ]; then run eslint node_modules/.bin/eslint --format unix "${js[@]}"
else echo 'skipped: no local biome or eslint in node_modules'; fi
section golangci-lint
if [ ${#go_files[@]} -eq 0 ]; then echo 'skipped: no Go changes'
elif has golangci-lint; then
  modules=()
  for file in "${go_files[@]}"; do
    dir=${file%/*}
    while [ ! -f "$dir/go.mod" ] && [ "$dir" != . ]; do dir=${dir%/*}; done
    if [ ! -f "$dir/go.mod" ]; then printf 'skipped: no containing go.mod for %q\n' "$file"; continue; fi
    duplicate=0
    for seen in "${modules[@]}"; do [ "$seen" != "$dir" ] || duplicate=1; done
    [ "$duplicate" -eq 0 ] || continue
    modules+=("$dir")
    # Module-wide analysis supplies context; --new-from-rev limits reported issues.
    if [ -n "${UNTRUSTED:-}" ]; then
      (cd "$dir" && run golangci-lint golangci-lint run --allow-parallel-runners --no-config --new-from-rev="$mb" ./...)
    else
      (cd "$dir" && run golangci-lint golangci-lint run --allow-parallel-runners --new-from-rev="$mb" ./...)
    fi
  done
else echo 'skipped: not installed'; fi
section clippy
if [ ${#rs[@]} -eq 0 ]; then echo 'skipped: no Rust changes'
elif [ -n "${UNTRUSTED:-}" ]; then echo 'skipped: UNTRUSTED set (runs build.rs and proc macros)'
elif has cargo && [ -f Cargo.toml ]; then
  echo 'scope: root crate diagnostics (confirm each lead is introduced in the diff)'
  run clippy cargo clippy --quiet --message-format short
else echo 'skipped: no cargo or no root Cargo.toml'; fi
exit 0
