# 🌉 Codewars MCP: Socratic Python Tutor

> **A local Model Context Protocol (MCP) agent that transforms GitHub Copilot into an active Python mentor.**

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/Architecture-Model_Context_Protocol-green)](https://modelcontextprotocol.io/)
[![GitHub Copilot](https://img.shields.io/badge/AI-GitHub_Copilot-purple?logo=githubcopilot)](https://github.com/features/copilot)
[![CodeWars](https://img.shields.io/badge/Data-CodeWars_API-red)](https://www.codewars.com/)

This repository implements a **Model Context Protocol (MCP)** server acting as a bridge between the CodeWars API and VS Code. Its goal is to provide a curated, offline-first environment where GitHub Copilot acts as a **Socratic Tutor**, guiding users through Python algorithms without revealing the solutions.

## 🤖 The Critical Role of GitHub Copilot

This project is **not a standalone tool**. It is an architectural extension designed specifically to enhance **GitHub Copilot**.

While this software handles the logic, file management, and kata retrieval, **Copilot acts as the pedagogical brain**. Through injected context instructions, Copilot shifts from being a "code autocomplete" tool to a "teaching assistant" that:
1.  Analyzes the algorithm requirements.
2.  Guides you using the **Socratic Method** (asking questions instead of giving answers).
3.  Refuses to write the final solution, ensuring you learn by doing.

> **⚠️ License Requirement:** To use this agent, you need an active GitHub Copilot subscription.
> * **Are you a student?** You can get GitHub Copilot **FOR FREE** via the [GitHub Student Developer Pack](https://education.github.com/pack).

## ✨ Key Features

* **📦 Static Knowledge Base:** Includes a pre-indexed local database (`katas_index.json`) with **1,350+ validated Python exercises**, ensuring instant access without API latency or scraping risks.
* **Lazy Loading Architecture:** Utilizes an "Index-First" approach. The agent scans the lightweight local index and only fetches heavy descriptions from the API on-demand.
* **Automated Environment:** Instantly generates:
    * Organized folders (e.g., `exercises/6kyu_python_valid_braces`).
    * `README.md` files with challenge instructions.
    * `solution.py` templates with PEP 8 compliant function names (Snake Case).
* **Privacy & Ethics:** Zero-dependency on third-party user data during runtime. The catalog is self-contained within the repository.

## 🚀 Installation & Usage (Coming Soon)

*Source code and the automated `setup.py` script will be pushed shortly.*

The standard workflow will be:
1.  Clone the repository.
2.  Run `python setup.py` to sync your local profile and configure the MCP server.
3.  Prompt Copilot in VS Code: *"I want to practice Python. Find an exercise for my level."*

## 🏆 Credits & Acknowledgments

This project integrates open-source technologies and educational platforms:

* **CodeWars:** For their incredible community and public API that powers the coding challenges.
* **Anthropic & Model Context Protocol (MCP):** For defining the open standard that connects AI models with local systems safely.
* **GitHub Copilot:** For providing the underlying intelligence and chat interface.
* **Open Source Community:** Special thanks to the contributors of the `mcp` and `requests` libraries.

---
*Developed for educational purposes. This project is not officially affiliated with CodeWars (Qualified.io).*
