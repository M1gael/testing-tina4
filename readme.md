# Tina4 Python Framework Evaluation

This project is dedicated to testing and evaluating different versions of the **Tina4 Python Framework**.

## Project Goal
The primary objective of this repository is to:
*   Implement various features and exercises from the official Tina4 documentation.
*   Identify discrepancies between documented behavior and actual framework functionality across different versions.
*   Validate official fixes and updates provided by the framework maintainers.
*   Document critical bugs and propose architectural improvements (e.g., signature-based dependency injection).

## Scope
This project focuses **solely on the Python version** of the Tina4 stack. 

## Current Status
*   **Routing Chapter:** Successfully verified path parameter injection, typed parameters, and standard HTTP methods (GET, POST, PUT, PATCH, DELETE).
*   **Framework Versions Tested:** v3.2.0 (with hot-patching) and v3.9.2.
*   **Identified Issues:** Discrepancies in `request.query` attribute names and missing `@group` decorator support in the latest versions.

## Directory Structure
*   `pypy/`: The main Python testing project.
*   `.agents/`: Automation workflows and agent-specific configurations.
*   `documentation/`: Local copies of the framework literature used for verification.
