---
name: eduyj-agent-loop
description: Use when working inside the EduYJ backend repo to continue the Ralph-like goal loop, choose the next milestone, validate links, and commit small Korean-convention changes.
---

# EduYJ Agent Loop

Start every session by reading:

1. `AGENTS.md`
2. `GOAL.md`
3. `docs/00-agent-navigation.md`
4. `docs/13-implementation-backlog.md`

Rules:

- Work on the `backend` branch/worktree.
- Keep commits small and use Korean messages like `docs : 내용` or `feat : 내용`.
- Preserve the 4-stage content decision: stage 4 is realtime.
- Do not reintroduce video generation.
- Update README and `docs/00-agent-navigation.md` when adding docs.

Loop:

```text
check git status
pick first unfinished backlog milestone
read linked specs
make scoped change
run validation
commit
update backlog if needed
```

Minimum validation:

```bash
git status --short --branch
rg -n "5[단]계|마지막[ ]실시간|마지막[ ]realtime|R[e]motion|f[f]mpeg" README.md AGENTS.md GOAL.md docs .agents
git diff --check
```
