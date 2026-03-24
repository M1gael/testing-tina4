# TINA4 Testing
The goal is to create basic implementations using the frameworks to evaluate their ease of use, performance. And to then report any problems or improvement that can be made in evalframework.md under the relative language section.
There is a documentation directory containing everything needed about every language we are testing this framework on.

## General
- In chapter 1 "What is tina" a section refers to the database models as just models. Might be more usefull to refer to them more specifically.


## Python

**Installation**
- Following the installation guide in "Book 1: Chapter 1", the provided `curl` script fails to download the Rust-based CLI. 
  - Error: `Downloading tina4-linux-amd64...  curl: (22) The requested URL returned error: 404`
- The documentation should be updated to reflect the correct download location for the new CLI.
- Having a "very old" version of the Tina4 CLI already installed causes confusion, as it doesn't support the new `--version` flag or the expected directory-based initialization. 
- Installer Bug: The install.sh script has an architecture mapping mismatch. It maps x86_64 to amd64, but the release assets on GitHub use the x86_64 suffix. This causes a 404 error during the automated installation on standard Linux/Intel/AMD systems.

**Dev Server & Live Reloading**
- **Bug Report: Infinite Restart Loop (`tina4 serve`)**: The new Rust-based CLI `tina4 serve` has a catastrophic logic flaw in its filesystem watcher implementation. Upon running `tina4 serve`, the Rust binary assumes responsibility for watching `src/`, `migrations/`, and `.env` and restarting the child Python process. However, the Rust watcher mistakenly broadcasts a "file changed" event every exactly 5.0 seconds, regardless of whether any files were actually modified. This throws the development server into an inescapable restart loop, rendering `tina4 serve` fundamentally broken out of the box. Bypassing python caches via `PYTHONDONTWRITEBYTECODE=1` does not work because the bug exists in the compiled Rust CLI layer, not the Python framework.
