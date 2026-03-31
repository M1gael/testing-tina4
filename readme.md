# Tina4 Python Framework Evaluation

This project is dedicated to testing and evaluating different versions of the **Tina4 Python Framework**.

## Project Goal
The primary objective of this repository is to:
*   Perform systematic evaluations of the Tina4 stack across multiple languages (**Python** and **Ruby**).
*   Documentation Verification: Implement framework features exactly as they are provided from the official documentation.
*   Discrepancy Identification: Identify and document cases where the framework's actual behavior deviates from the documentation provided.
*   Regression Testing: Validate fixes and monitor issues across framework updates.

## Protocol: Chapter-Based Evaluation
The repository contains a `documentation/` folder with complete guides. The ASSISTANT MUST:
1.  **Wait for Direction**: Do NOT start working on any documentation file until the USER explicitly specifies which chapter (e.g., "Work on Chapter 3").
2.  **Strict Sequencing**: Implement chapters only in the order requested by the USER. No exceptions.
3.  **Implementation Fidelity**: Implement the provided code example exactly as documented within the target language project directory (`pypy/` for Python, `ruru/` for Ruby).
4.  **No Proactive Fixes**: Do NOT implement proactive fixes for framework bugs; the goal is to verify if the documentation works as-is.
5.  **Issue Reporting**: Report all discrepancies, errors, or points of confusion to the USER for issue tracking in plain-text code blocks as defined in the `reporting` skill.

## Evaluation Progress
| Language | Chapter | Status | Key Issues Found |
| :--- | :--- | :--- | :--- |
| Ruby | 01 | Completed | Missing `webrick`, Ternary Operator bug, POST 401s |
| Ruby | 02 | Completed | Symbol keys fail, Group Prefixes ignored, Wildcards broken |
| Ruby | 03 | Pending | - |
| Python | 01-06 | In Progress | See `pypy/` logs |

## Project Structure
*   `pypy/`: The Python testing project and primary workspace.
*   `ruru/`: The upcoming Ruby testing project and workspace.
*   `.agents/`: Automation workflows, reporting skills, and agent-specific configurations.


## Standard Implementation Workflow
1.  **Isolation**: All test implementations occur within the current language's target project directory (e.g., `pypy/` or `ruru/`).

2.  **Organization**: Every documentation section should have a dedicated file in the appropriate routes/feature directory named after the feature (e.g., `chaining.py`).
3.  **Documentation Consistency**: 
    *   Implement exactly as documented first.
    *   Add lowercase, space-prefixed comments at the top of each file explaining the test case.
4.  **Verification**: 
    *   Test against the live `tina4 serve` process via CLI or browser.
    *   Continuously monitor `logs/tina4.log` for registration and execution errors.
5.  **Reporting**: Generate plain-text status reports as defined in the `reporting` skill.
6.  **Review**: Read the `reporting` skill before performing any `/commit` requested by the USER.

## Pending Tests (Blocked by Bugs)
The following functionality could not be thoroughly tested due to framework bugs blockading the testing process. We must return to these sections once the framework issues are patched.
*   **Chapter 5: Database (Migrations)**: The `tina4 migrate` command fails outright with an `ImportError` on `load_dotenv`.
*   **Chapter 5: Database (DatabaseResult Output)**: The `column_info()`, `to_list()`, and `to_paginate()` methods documented for the `DatabaseResult` class are entirely missing from the implementation (yielding `AttributeError`/missing execution logic).
*   **Chapter 5 & 6: Database/ORM (SQLite Lock & Schema Generation)**: The `Note.create_table()` operations (alongside all other schema-altering functions) deadlock with SQLite `Resource Busy` locks while `tina4 serve` maintains its state-locking mechanisms. ORM integration via HTTP endpoints cannot securely execute without crashing or hanging the terminal. Wait for framework pooling updates or explicit offline test setups.
