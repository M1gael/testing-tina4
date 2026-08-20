#!/usr/bin/env bash
# Shared helper: apply a candidate patch to a project's INSTALLED framework copy,
# and guarantee it is restored.
#
# Source it, then:
#   patch_apply <patch-file> <relative/path/inside/tina4_python>
#   patch_restore                      # also wired to your EXIT trap
#
# Two traps this exists to avoid, both hit for real on 2026-08-20:
#
#  * `git apply` SILENTLY SKIPS a patch whose target sits under a gitignored path.
#    site-packages lives in .venv/, which this repo ignores, so it printed nothing,
#    exited 0, and changed no bytes — producing a "the fix does not work" result
#    from a fix that was never applied. We stage in a temp tree outside any repo
#    and then hard-fail if the file did not actually change.
#
#  * A patched venv that outlives the question it answered turns every later run in
#    that project into a lie, and the output looks identical either way. Restore is
#    on an EXIT trap, and the caller is expected to verify it.

_PATCH_TARGET=""
_PATCH_BACKUP=""

patch_site_dir() {   # absolute path of the installed tina4_python package
  .venv/bin/python -c 'import tina4_python,os;print(os.path.dirname(tina4_python.__file__))'
}

patch_apply() {      # patch_apply <patch-file> <path-inside-tina4_python>
  local patch_file="$1" rel="$2" site stage
  site="$(patch_site_dir)"
  _PATCH_TARGET="${site}/${rel}"
  [ -f "$_PATCH_TARGET" ] || { echo "no such file: $_PATCH_TARGET"; return 1; }

  _PATCH_BACKUP="$(mktemp -t candidate-stock-XXXXXX)"
  cp "$_PATCH_TARGET" "$_PATCH_BACKUP"

  stage="$(mktemp -d)"
  mkdir -p "${stage}/tina4_python/$(dirname "$rel")"
  cp "$_PATCH_TARGET" "${stage}/tina4_python/${rel}"

  if ! ( cd "$stage" && git apply -p1 "$patch_file" ); then
    echo "candidate patch failed to apply"; rm -rf "$stage"; return 1
  fi
  if cmp -s "$_PATCH_TARGET" "${stage}/tina4_python/${rel}"; then
    echo "candidate patch applied but changed nothing — refusing to report a fixed run"
    rm -rf "$stage"; return 1
  fi

  cp "${stage}/tina4_python/${rel}" "$_PATCH_TARGET"
  rm -rf "$stage"
  find "$site" -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null
  return 0
}

patch_restore() {
  [ -n "$_PATCH_BACKUP" ] && [ -s "$_PATCH_BACKUP" ] || return 0
  cp "$_PATCH_BACKUP" "$_PATCH_TARGET"
  rm -f "$_PATCH_BACKUP"
  _PATCH_BACKUP=""
  find "$(patch_site_dir)" -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null
  echo "  venv restored from backup"
}

patch_verify_restored() {   # patch_verify_restored <expected-md5>
  local got
  got="$(md5sum "$_PATCH_TARGET" 2>/dev/null | cut -d' ' -f1)"
  if [ "$got" = "$1" ]; then echo "  restore verified (md5 $got)"; return 0; fi
  echo "  RESTORE FAILED — md5 $got, expected $1"; return 1
}
