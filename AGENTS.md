# How to Use Agents Effectively

**Try It Now (60 Seconds)**

Copy and paste this command into your Opencode session to explore the codebase:

```
@explorer Show me the structure of the `src/` directory and list all Python modules.
```

You’ll see a breakdown of the project’s source tree, with file paths and module
names. This is the fastest way to understand the codebase before making changes.

---

This guide explains how to work with the Opencode agent system to develop and
maintain the Canvas Code Correction project. Agents are specialized AI
assistants that help with different aspects of software engineering. By
delegating tasks to the right agent, you can work faster and more reliably.

## 1. Understanding the Agent Roles

Five agent roles are available, each with a distinct responsibility:

- **Explorer** – Discovers and maps the codebase. Use this agent to understand
  existing code, find relevant files, and identify patterns.
- **Librarian** – Researches documentation and external resources. Delegate to
  Librarian when you need up‑to‑date library references, API documentation, or
  best‑practice guides.
- **Oracle** – Answers specific technical questions based on the project’s
  knowledge base. Ask Oracle about design decisions, constraints, or why a
  particular approach was chosen.
- **Designer** – Creates plans and architectural solutions. Use Designer when
  you need a step‑by‑step implementation plan, a refactoring strategy, or a new
  feature design.
- **Fixer** – Executes code changes quickly and precisely. Fixer implements the
  plans created by Designer, following the provided context and task
  specification.

Each agent is invoked with a dedicated command (or annotation) that tells the
system which specialist should handle the request.

## 2. When to Delegate to Each Agent

Delegate based on the kind of work you need done:

| Agent         | When to Use                                                                                                                                                                            |
| ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Explorer**  | “Find all files that mention `Workspace`.”<br>“Show me the dependency graph of the `runner` module.”<br>“What’s the structure of the `tests/` directory?”                              |
| **Librarian** | “What’s the current API for `boto3` S3 operations?”<br>“Find examples of using `pytest` fixtures with async.”<br>“Get the documentation for Prefect 3.0 blocks.”                       |
| **Oracle**    | “Why does `Workspace` require a separate `cleanup` method?”<br>“What are the security constraints for the Canvas token?”<br>“What’s the expected behavior when S3 upload fails?”       |
| **Designer**  | “Design a retry mechanism for failed grader containers.”<br>“Plan the migration from `uv.lock` to `requirements.txt`.”<br>“Create a step‑by‑step refactoring of the `webhook` module.” |
| **Fixer**     | “Implement the retry logic designed by Designer.”<br>“Rename `get_cwd` to `get_current_working_directory` across the project.”<br>“Add type hints to the `auth` module.”               |

**Rule of thumb:** If you need **information**, use Explorer, Librarian, or
Oracle. If you need a **plan**, use Designer. If you need **code written**, use
Fixer.

## 3. Commit Conventions (Conventional Commits)

Every change to the repository must be committed with a conventional commit
message. This ensures the commit history is readable and can be used to generate
changelogs automatically.

### Format

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

- **feat** – a new feature
- **fix** – a bug fix
- **docs** – documentation changes
- **style** – code style changes (formatting, missing semicolons, etc.)
- **refactor** – code changes that neither fix a bug nor add a feature
- **test** – adding or correcting tests
- **chore** – maintenance tasks (dependency updates, tooling changes)

### Examples

```bash
$ git commit -m "feat(webhook): add retry logic for failed Canvas API calls"
$ git commit -m "fix(runner): handle Docker container timeout gracefully"
$ git commit -m "docs(cli): update --help text for configure-course"
$ git commit -m "test(workspace): add integration tests for RustFS mock"
```

### Scope

The scope should be the module or component affected (e.g., `webhook`, `runner`,
`cli`, `workspace`). If the change touches multiple modules, omit the scope.

## 4. Workflow Examples (with Commands)

### Example 1: Adding a New Feature

1. **Explore** the relevant part of the codebase:
   ```
   @explorer Find all files in the `webhook` module and show their dependencies.
   ```
2. **Research** the required external APIs:
   ```
   @librarian Get the latest Prefect webhook documentation and examples.
   ```
3. **Ask** about project‑specific constraints:
   ```
   @oracle What are the security requirements for storing webhook secrets?
   ```
4. **Design** the implementation:
   ```
   @designer Create a step‑by‑step plan for adding a webhook secret rotation feature.
   ```
5. **Implement** the changes:
   ```
   @fixer Execute the plan from Designer. Start by creating the new configuration block.
   ```
6. **Commit** the work:
   ```bash
   $ git add .
   $ git commit -m "feat(webhook): add secret rotation via Prefect blocks"
   ```

### Example 2: Fixing a Bug

1. **Identify** the root cause with Explorer:
   ```
   @explorer Show me the last 10 changes to the `Workspace.cleanup` method.
   ```
2. **Verify** the expected behavior with Oracle:
   ```
   @oracle What should `Workspace.cleanup` do when the working directory doesn’t exist?
   ```
3. **Implement** the fix with Fixer:
   ```
   @fixer Change `Workspace.cleanup` to ignore missing directories (log a warning, don’t raise).
   ```
4. **Test** the change and commit:
   ```bash
   $ pytest tests/test_workspace.py -xvs
   $ git add .
   $ git commit -m "fix(workspace): make cleanup idempotent for missing directories"
   ```

### Git Flow Commands

Use `git flow` to keep your work organized in feature branches:

```bash
# Start a new feature branch
$ git flow feat start webhook-secret-rotation

# Work on the feature, commit as you go
$ git add .
$ git commit -m "feat(webhook): add secret rotation via Prefect blocks"

# Finish the feature (merges into develop)
$ git flow feat finish webhook-secret-rotation
```

For bug fixes:

```bash
$ git flow bugfix start cleanup-idempotent
# … make changes …
$ git flow bugfix finish cleanup-idempotent
```

## 5. Best Practices

- **Delegate early, delegate often.** Don’t try to do everything yourself—use
  the agent that’s best suited for the task.
- **Provide clear context.** When you delegate, include file paths, line
  numbers, and any relevant research you already have.
- **Follow the Zen of Python.** Keep code simple, explicit, and readable.
  Complex is better than complicated; flat is better than nested.
- **Commit small, focused changes.** Each commit should do one thing and do it
  well. Group related edits together.
- **Run tests after every change.** Use the project’s test suite (`pytest`) and
  linting (`ruff check`) before committing.
- **Keep the knowledge base up to date.** If you discover new constraints or
  design decisions, add them to `.quint/` so Oracle can answer accurately next
  time.

---

**Quick Reference**

| Task                     | Agent     | Example Command                                   |
| ------------------------ | --------- | ------------------------------------------------- |
| Find code                | Explorer  | `@explorer Find all uses of S3Bucket`             |
| Look up documentation    | Librarian | `@librarian Get boto3 S3 upload examples`         |
| Ask why something exists | Oracle    | `@oracle Why is there a separate assets block?`   |
| Create a plan            | Designer  | `@designer Design a caching layer for Canvas API` |
| Write code               | Fixer     | `@fixer Implement the caching layer`              |
| Commit changes           | –         | `git commit -m "feat(api): add caching layer"`    |
| Start a feature branch   | –         | `git flow feat start api-caching`                 |
