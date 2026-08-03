# Configuration

The repository's `.codex/config.toml` enables subagents, limits each session to
eight concurrent threads, and sets the default subagent reasoning effort. It is
project-scoped configuration: user and system policy may override or restrict
it, and a target project does not inherit this file merely by installing the
plugin.

Plugin installation guarantees the bundled skills. The 33 `.codex/agents/*.toml`
files are project-scoped development definitions; workflows must verify that
their named roles are available in the active target project/session. A user may
copy reviewed definitions into a target project's supported agent configuration
or provide equivalent roles, subject to local policy. Parliament does not claim
automatic agent installation. If `correctness-reviewer` or `security-reviewer`
is unavailable, a code-changing workflow ends `INCOMPLETE`.

Do not raise concurrency above the environment's safe limit. Batch larger
councils and keep write ownership serial unless disjoint worktrees are explicit.
