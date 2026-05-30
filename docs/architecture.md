# Architecture

Tripwire is a CLI-first project consistency checker.

Version 1 should:

1. Load doctrine documents.
2. Load repository context.
3. Read git diff.
4. Generate structured findings.
5. Output findings to terminal.

The git diff is the primary object under review. Repository context and doctrine documents provide supporting context.

Tripwire is not a coding assistant, code generator, linter, formatter, test runner, CI gate, or autonomous refactoring tool.
