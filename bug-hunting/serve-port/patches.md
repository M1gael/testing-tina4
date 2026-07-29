# Tina4 CLI `serve` Port Positional Argument Issue

**Reporter Query:**
> "Morning, can we confirm that the following is working. Was playing with Tina4 v3 on the weekend and I was struggling with this.
> `tina4 serve 7150`"
> "it actually throws an error as it is trying to take on a project name."

---

## Empirical Verification & Reproduction

Command executed:
```bash
tina4 serve 7150
```

Actual output:
```text
✗ Project '7150' not found in the current folder or your projects folder ((none configured))
```

## Root Cause

`tina4 serve` CLI parser defines positional argument `[PROJECT]` and optional flag `-p, --port <PORT>`:

```text
Usage: tina4 serve [OPTIONS] [PROJECT]

Arguments:
  [PROJECT]  Optional project name — resolved against current folder, then configured projects folder

Options:
  -p, --port <PORT>  Port number
```

When running `tina4 serve 7150`, CLI parser treats `7150` as positional argument `[PROJECT]`. Since no directory named `7150` exists, CLI errors out.

## Resolution / Usage

Port must be specified using `-p` or `--port` flag:
```bash
tina4 serve -p 7150
# or
tina4 serve --port 7150
```

## Recommended CLI UX Enhancement

If numeric positional argument passed (e.g. `1024-65535`) and directory of that name does not exist, CLI parser could auto-detect integer as port or emit helpful hint:

> `Hint: '7150' parsed as project name. To specify port, use 'tina4 serve -p 7150'.`

---

## Draft Upstream Issue

**Title:** Docs Gap: `tina4 serve` options (`-p` / `--port`) and project launcher (`tina4 serve <project>`) not documented

**Body:**

### Problem

The official documentation does not teach:
1. Port configuration flags: `-p` or `--port` (e.g. `tina4 serve -p 7150`)
2. Project launching system: passing a project name positionally (e.g. `tina4 serve <projectname>`)

Because `tina4 serve` accepts positional arguments for project names, users attempting `tina4 serve 7150` receive:
```text
✗ Project '7150' not found in the current folder or your projects folder ((none configured))
```

### Requested Solution

Update `tina4 serve` documentation to cover:
- How to set custom ports using `-p` / `--port <PORT>`
- How the project launching system works when passing `tina4 serve <projectname>`
