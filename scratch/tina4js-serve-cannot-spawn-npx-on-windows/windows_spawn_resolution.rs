//! Every program the CLI launches on the user's behalf must be looked up
//! before it is spawned.
//!
//! Windows' `CreateProcess` — which `std::process::Command` uses — appends only
//! `.exe` to a bare program name. It never consults `%PATHEXT%`. Node ships
//! `npx` as `npx.cmd` and there is no `npx.exe`, so `Command::new("npx")` fails
//! with `program not found` on a machine where typing `npx` at the prompt works
//! perfectly. `console::resolve_cmd` exists for exactly that: it goes through
//! `which`, which does read `%PATHEXT%`, and hands `Command::new` a full path.
//!
//! `tina4 serve` in a tina4js project hit this first and loudest; 3.8.88 fixed
//! that arm by driving the project's own Vite through `node`. But the same
//! mechanism sits under `resolve_cli`, which returns a LOGICAL launcher name —
//! `npx`, `bundle`, `tina4nodejs`, `tina4ruby`, `tina4php` — every one of which
//! Windows ships as a `.cmd`/`.bat` shim with no `.exe` beside it. Its three
//! consumers spawn that name directly, so `tina4 serve` on a php project, every
//! delegated subcommand, and the command-manifest query all fail the same way.
//!
//! The nodejs and ruby arms of `resolve_cli` make the contradiction explicit:
//! they gate on `which::which("npx").is_ok()` — a lookup that DOES read
//! `%PATHEXT%` and so finds `npx.cmd` — and then spawn the bare name by a call
//! that cannot launch it. The code proves the program exists by one rule and
//! launches it by another.
//!
//! `cargo test` runs on ubuntu only and the failure cannot be reproduced on
//! Linux, where `execvp` searches `PATH` and a bare `npx` resolves fine. So this
//! gate is on the SHAPE of the code, not on the behaviour — it is the only
//! regression test the defect admits without a Windows host. The behavioural
//! half (that wrapping is a no-op when lookup fails, which is what makes it safe
//! to apply everywhere) is locked in beside `resolve_cmd` itself.

const MAIN_RS: &str = include_str!("../src/main.rs");
const MANIFEST_RS: &str = include_str!("../src/manifest.rs");

/// Programs Windows ships as a `.cmd`/`.bat` wrapper with no `.exe` beside it.
/// Spawning any of these by bare name is the defect.
const NEEDS_LOOKUP: &[&str] = &[
    "npx", "npm", "yarn", "pnpm", "vite", "tsx", "bundle", "bundler", "gem", "composer",
];

/// `Command::new` arguments that are already a resolved path, so they need no
/// lookup. Anything not here and not passing through `resolve_cmd` is a new
/// spawn nobody has thought about on Windows — which is the point of the gate.
const ALREADY_RESOLVED: &[&str] = &[
    "&venv_python",          // .venv/bin/python, built as a path
    "console::python_cmd()", // "python" on Windows, which IS python.exe
    "&path",                 // came out of which::which
    "&tina4_path",           // came out of which::which
    "curl_path",             // came out of which::which
    "program",               // tina4js_serve_command already resolved it
];

/// Bare literals that are genuinely safe: a real `.exe` on Windows, or a
/// program only ever spawned down a non-Windows branch.
const SAFE_LITERALS: &[&str] = &[
    "taskkill",   // taskkill.exe
    "powershell", // powershell.exe
    "curl",       // curl.exe, shipped since Windows 10 1803
    "uv",         // uv.exe
    "ruby",       // ruby.exe
    "node",       // node.exe
    "python",     // python.exe
    "unzip",      // the non-Windows arm of an is_windows() branch
    "sh",         // ditto, plus test helpers
];

/// Pull the argument text out of every `Command::new(...)` in `src`.
/// Returns `(line_number, argument_text)`.
fn spawn_arguments(src: &str) -> Vec<(usize, String)> {
    const NEEDLE: &str = "Command::new(";
    let mut found = Vec::new();
    let mut at = 0;

    while let Some(hit) = src[at..].find(NEEDLE) {
        let open = at + hit + NEEDLE.len();
        let line = src[..open].lines().count();

        // Walk to the matching close paren, ignoring parens inside strings.
        let mut depth = 1usize;
        let mut in_string = false;
        let mut escaped = false;
        let mut end = open;
        for (i, c) in src[open..].char_indices() {
            if escaped {
                escaped = false;
                continue;
            }
            match c {
                '\\' if in_string => escaped = true,
                '"' => in_string = !in_string,
                '(' if !in_string => depth += 1,
                ')' if !in_string => {
                    depth -= 1;
                    if depth == 0 {
                        end = open + i;
                        break;
                    }
                }
                _ => {}
            }
        }
        found.push((line, src[open..end].trim().to_string()));
        at = end.max(open + 1);
    }

    found
}

/// A `"quoted"` argument yields the program name; anything else yields None.
fn as_literal(arg: &str) -> Option<&str> {
    arg.strip_prefix('"')?.strip_suffix('"')
}

/// Every `let (name, _) = resolve_cli(..)` binding, as `(line, name)`. The
/// launcher `resolve_cli` hands back is a logical name, never a path.
fn resolve_cli_bindings(src: &str) -> Vec<(usize, String)> {
    let mut found = Vec::new();
    for (n, line) in src.lines().enumerate() {
        let Some(head) = line.split_once("resolve_cli(").map(|(h, _)| h) else {
            continue;
        };
        if !head.contains("let (") {
            continue; // the definition itself, or a doc comment
        }
        let Some(binding) = head
            .split_once("let (")
            .and_then(|(_, t)| t.split(',').next())
            .map(|b| b.trim().trim_start_matches("mut ").trim())
        else {
            continue;
        };
        found.push((n + 1, binding.to_string()));
    }
    found
}

#[test]
fn no_pathext_dependent_program_is_spawned_by_bare_name() {
    for (file, src) in [("src/main.rs", MAIN_RS), ("src/manifest.rs", MANIFEST_RS)] {
        for (line, arg) in spawn_arguments(src) {
            if let Some(name) = as_literal(&arg) {
                assert!(
                    !NEEDS_LOOKUP.contains(&name),
                    "{file}:{line}: Command::new(\"{name}\") — on Windows {name} is \
                     {name}.cmd and CreateProcess only ever appends .exe, so this \
                     spawn fails with `program not found` on a machine where {name} \
                     works at the prompt. Use console::resolve_cmd(\"{name}\")."
                );
            }
        }
    }
}

#[test]
fn every_spawn_is_either_resolved_or_known_safe() {
    for (file, src) in [("src/main.rs", MAIN_RS), ("src/manifest.rs", MANIFEST_RS)] {
        for (line, arg) in spawn_arguments(src) {
            if arg.contains("resolve_cmd") {
                continue;
            }
            let ok = match as_literal(&arg) {
                Some(name) => SAFE_LITERALS.contains(&name),
                None => ALREADY_RESOLVED.contains(&arg.as_str()),
            };
            assert!(
                ok,
                "{file}:{line}: Command::new({arg}) neither goes through \
                 console::resolve_cmd nor is listed as already-resolved or \
                 Windows-safe. If it is a .exe or a non-Windows-only path, add it \
                 to the list with the reason; otherwise wrap it in resolve_cmd."
            );
        }
    }
}

/// The defect proper. `resolve_cli` returns a logical launcher name — `npx`,
/// `bundle`, `tina4nodejs`, `tina4ruby`, `tina4php` — and on Windows every one
/// of those is a `.cmd`/`.bat` shim. Whatever a consumer does with that name,
/// it must not hand it to `Command::new` unresolved.
#[test]
fn every_resolve_cli_consumer_resolves_before_spawning() {
    for (file, src) in [("src/main.rs", MAIN_RS), ("src/manifest.rs", MANIFEST_RS)] {
        for (bind_line, binding) in resolve_cli_bindings(src) {
            let spawns: Vec<_> = spawn_arguments(src)
                .into_iter()
                .filter(|(_, arg)| {
                    arg.split(|c: char| !(c.is_alphanumeric() || c == '_'))
                        .any(|word| word == binding)
                })
                .collect();

            assert!(
                !spawns.is_empty(),
                "{file}:{bind_line}: `{binding}` is bound from resolve_cli but this \
                 test can no longer find where it is spawned — the gate below is \
                 passing vacuously. Re-point it."
            );

            for (line, arg) in spawns {
                assert!(
                    arg.contains("resolve_cmd"),
                    "{file}:{line}: Command::new({arg}) spawns the launcher \
                     resolve_cli returned (bound at {file}:{bind_line}) without \
                     looking it up. resolve_cli hands back a logical name: for a \
                     nodejs project that is `npx`, for ruby `bundle`, for php \
                     `tina4php`. On Windows each of those is a .cmd/.bat shim that \
                     CreateProcess cannot launch, so this fails with `program not \
                     found`. Wrap it in console::resolve_cmd."
                );
            }
        }
    }
}

/// The gates above are only worth anything if the scans actually find things. A
/// parser that silently returns nothing passes every assertion in this file — so
/// make both of them prove they are still reading the source.
#[test]
fn the_scans_still_find_their_subjects() {
    let main = spawn_arguments(MAIN_RS);
    let manifest = spawn_arguments(MANIFEST_RS);

    assert!(
        main.len() >= 25,
        "only {} Command::new sites found in src/main.rs — the scan has stopped \
         reading the file, and the gates above are passing vacuously",
        main.len()
    );
    assert_eq!(
        manifest.len(),
        1,
        "src/manifest.rs spawn count changed: {manifest:?}"
    );
    assert!(
        main.iter().any(|(_, a)| a == "\"taskkill\""),
        "the scan no longer reads plain string-literal arguments"
    );
    assert!(
        main.iter().any(|(_, a)| a.contains("resolve_cmd")),
        "the scan no longer reads nested-call arguments"
    );

    let bindings = resolve_cli_bindings(MAIN_RS).len() + resolve_cli_bindings(MANIFEST_RS).len();
    assert!(
        bindings >= 3,
        "only {bindings} resolve_cli bindings found across src/main.rs and \
         src/manifest.rs — there were 3 when this gate was written, so the \
         binding scan has stopped matching and the consumer gate is vacuous"
    );
}
