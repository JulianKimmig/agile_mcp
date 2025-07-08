# Contributing to Agile MCP Server

We welcome contributions to the Agile MCP Server! By contributing, you help us improve and expand the capabilities of this project.

## How to Contribute

1.  **Fork the repository** on GitHub.
2.  **Clone your forked repository** to your local machine.
3.  **Create a new branch** for your feature or bug fix:
    ```bash
    git checkout -b feature/your-feature-name
    # or
    git checkout -b bugfix/your-bug-fix-name
    ```
4.  **Make your changes** and ensure they adhere to the coding standards.
5.  **Add tests** for new functionality or bug fixes.
6.  **Ensure all tests pass** and code coverage remains high.
7.  **Commit your changes** with a clear and concise commit message.
8.  **Push your branch** to your forked repository.
9.  **Open a Pull Request** to the `develop` branch of the main repository.

## Coding Standards

We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) for Python code style. We use `ruff` for linting and `black` for formatting. Please ensure your code passes these checks before submitting a pull request.

To automatically format and lint your code, you can use the following commands:

```bash
uv run ruff format src/ tests/
uv run ruff check src/ tests/
```

## Pull Request Procedures

When submitting a pull request, please ensure:

-   The PR title is descriptive and follows the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification (e.g., `feat: Add new feature`, `fix: Resolve bug`).
-   The PR description clearly explains the changes, the problem it solves, and any relevant context.
-   All new and existing tests pass.
-   Code coverage is maintained or improved.
-   Your branch is up-to-date with the `develop` branch of the main repository.

## Development Process

Our development process is based on agile methodologies, with work organized into sprints and user stories. We use GitHub for version control and pull requests for code review.

### Local Development Setup

1.  **Install dependencies** including development tools:
    ```bash
    uv sync
    ```
2.  **Install in editable mode** (optional, but recommended for running examples):
    ```bash
    uv pip install -e .
    ```

### Running Tests

To run the test suite and check code coverage:

```bash
uv run pytest
```

### Type Checking

To perform static type checking:

```bash
uv run mypy src/
```

Thank you for contributing to the Agile MCP Server!
