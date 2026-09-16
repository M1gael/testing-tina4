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
//! `tina4 serve` in a tina4js project spawned `npx` by bare name from the commit
//! that added tina4js support, so serve never once started on Windows for that
//! project type. The Node.js arm eighteen lines above it had been converted when
//! `resolve_cmd` was introduced; this one was missed, and so were the three
//! sites that spawn whatever launcher `resolve_cli` returns.
//!
//! `cargo test` runs on ubuntu only and the failure cannot be reproduced on
//! Linux, where `execvp` searches `PATH` and a bare `npx` resolves fine. So this
//! gate is on the SHAPE of the code, not on the behaviour — it is the only
//! regression test the defect admits without a Windows host.

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
    "&venv_python",            // .venv/bin/python, built as a path
    "console::python_cmd()",   // "python" on Windows, which IS python.exe
    "&path",                   // came out of which::which
    "&tina4_path",             // came out of which::which
    "curl_path",               // came out of which::which
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

/// The reported defect, named. `tina4 serve` in a tina4js project is the one
/// spawn a user hits first, and it is the one that was missed.
#[test]
fn tina4js_serve_resolves_npx() {
    let arm = MAIN_RS
        .split("\"tina4js\" => {")
        .nth(1)
        .expect("the tina4js arm of the serve spawner");
    let spawn = arm
        .find("Command::new(")
        .map(|i| &arm[i..i + 60])
        .expect("the tina4js arm spawns something");
    assert!(
        spawn.contains("resolve_cmd(\"npx\")"),
        "tina4 serve spawns {spawn:?} for a tina4js project. It must go through \
         console::resolve_cmd, or serve cannot start vite on Windows."
    );
}

/// The two gates above are only worth anything if the scan actually finds the
/// spawns. A parser that silently returns nothing passes every assertion in this
/// file — so make it prove it is still reading the source.
#[test]
fn the_scan_still_finds_the_spawns() {
    let main = spawn_arguments(MAIN_RS);
    let manifest = spawn_arguments(MANIFEST_RS);

    assert!(
        main.len() >= 25,
        "only {} Command::new sites found in src/main.rs — the scan has stopped \
         reading the file, and both gates above are passing vacuously",
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
}
