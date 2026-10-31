# Agent guidance

This repository is at an initial stage. Inspect the current files and project
documentation before choosing tools or making changes; do not assume a language,
framework, or package manager.

- Keep changes focused on the requested task and preserve existing work.
- Follow established conventions and use the project's documented setup, build,
  and test commands once they exist.
- Add or update tests when appropriate, and run the checks relevant to changes.
- Document new setup requirements and commands as the project develops.
- Do not commit credentials or generated dependencies.

## Agent skills

### Issue tracker

Issues and specs live in GitHub Issues; use the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Use `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, and `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `GLOSSARY.md` and `docs/adr/`. See `docs/agents/domain.md`.
