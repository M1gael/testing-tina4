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

## Current Status
*   **Routing Chapter:** Successfully verified path parameter injection, typed parameters, and standard HTTP methods (GET, POST, PUT, PATCH, DELETE).
*   **Request & Response Chapter:** Partially verified; documented major discrepancies in file upload handling and `response.redirect()`.
*   **Input Validation Chapter:** Documentation incorrect/unavailable; `Validator` class and `response.error()` are missing from v3.2.0.
*   **Framework Versions Tested:** v3.2.0 (with hot-patching) and v3.9.2.
*   **Identified Issues:** 
    *   Discrepancies in `request.query` attribute names.
    *   Missing `@group` decorator support in latest versions.
    *   `request.files` is empty (files are in `request.body`).
    *   File metadata uses `file_name` instead of `filename`.
    *   Uploaded file content is Base64-encoded string instead of raw bytes.
    *   `response.redirect()` returns 404 instead of 302.
    *   `response.file()` requires absolute paths for successful resolution.
    *   Missing `tina4_python.validator` module and `Validator` class.
    *   Missing `response.error()` method for error envelopes.

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
