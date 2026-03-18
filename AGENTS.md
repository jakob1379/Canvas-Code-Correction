- in pytest fixtures do NOT use `autouse=true`, its a deadly sin bringing side-effects to all tests,
  unknowingly

## Best Practices

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
| Start a feature branch   | –         | `git switch -c feat/api-caching main`             |
