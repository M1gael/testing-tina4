# Tina4 Python Framework Evaluation

This project is dedicated to testing and evaluating different versions of the **Tina4 Python Framework**.

## Project Goal
The primary objective of this repository is to:
*   Perform systematic evaluations of the Tina4 stack across multiple languages (starting with Python).
*   Documentation Verifcation: Implement framework features exactly as they are provided from the official documentation.
*   Discrepancy Identification: Identify and document cases where the framework's actual behavior (e.g., v3.2.0) deviates from the documentation provided.
*   Regression Testing: Validate fixes and monitor issues across framework updates.

## Protocol: Documentation Feeding
The USER will provide documentation sections incrementally. The ASSISTANT (or any automated agent) MUST:
1. Wait for each documentation snippet before proceeding.
2. Implement the provided code example as a standalone test within the appropriate language project directory.

## Project Structure
*   `pypy/`: The Python testing project and primary workspace.
*   `.agents/`: Automation workflows, reporting skills, and agent-specific configurations.

## Standard Implementation Workflow
1.  **Isolation**: All test implementations occur within the current language's project directory (currently `pypy/`).
2.  **Organization**: Every documentation section should have a dedicated file in the appropriate routes/feature directory named after the feature (e.g., `chaining.py`).
3.  **Documentation Consistency**: 
    *   Implement exactly as documented first.
    *   Add lowercase, space-prefixed comments at the top of each file explaining the test case.
4.  **Verification**: 
    *   Test against the live `tina4 serve` process via CLI or browser.
    *   Continuously monitor `logs/tina4.log` for registration and execution errors.
5.  **Reporting**: Generate plain-text status reports as defined in the `reporting` skill.
6.  **Review**: Read the `reporting` skill before performing any `/commit` requested by the USER.
