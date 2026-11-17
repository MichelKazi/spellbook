# Skill ledger

This file records the fate of each skill from ai-dotfiles and the old home server setup.

## Kept, first party

| Skill | Group | Change |
|---|---|---|
| architecture-diagram | core | Removed work paths and work-only tools. Notes go where your instructions say. |
| collaborative-coding | core | None. |
| design | core | Routes to `frontend-design`, `sosumi`, and `slopbliterator`. |
| grindstone | core | The layer table now uses the current stack: spec template, AGENTS.md, hooks, reviewer prompt, and `/code-review`. |
| ui-research | core | Removed work paths. |
| build | routing | New. Opus plans, DeepSeek builds, GLM reviews. |
| session-handoff, load-session | personal | None. They need the brain MCP connector. |
| deck-input, deck-record, deck-screencap | personal | None. They need the Steam Deck fleet scripts. |
| karoo-ext | personal | None. |

## Replaced by a package

| Old skill | Now | Source |
|---|---|---|
| no-ai-slop | slopbliterator | MichelKazi/slopbliterator |
| root-cause-tracing | systematic-debugging | obra/superpowers |
| code-self-check | verification-before-completion | obra/superpowers |
| code-review-session, deep-review | requesting-code-review, receiving-code-review, and the built-in `/code-review` | obra/superpowers |
| create-pr | finishing-a-development-branch, plus the slop gate | obra/superpowers |
| mobile-app-design | frontend-design, plus the platform HIG through sosumi | anthropics/skills |
| drawio | drawio | jgraph/drawio-mcp |
| find-skills | find-skills | vercel-labs/skills |
| graphify, graphify-query | graphify | Graphify-Labs/graphify |
| sosumi | sosumi | NSHipster/sosumi.ai |
| supabase, supabase-postgres-best-practices | same names | supabase/agent-skills |
| use-railway | use-railway | railwayapp/railway-skills |
| peon-ping-* | same names | PeonPing/peon-ping |
| reverse-engineer-anything | reverse-engineer-anything, plus the rea MCP server | morluto/rea |

## Dropped

| Skill | Reason |
|---|---|
| audit-service-observability, create-feature-flag, cross-service-impact-analysis, deploy-canary, grafana-mcp, graphage-dashboard, honeycomb-mcp, incident-report, migration-checker, promql, repo-wiki, scala-test-writer, service-finder, staging-thrift-test, strava-code-search, sfb-board-hygiene, sfb-jira, sfb-refinement-prep, sfb-ticket-author, sfb-velocity | Old job. They depend on its services, tools, and templates. |
| ask-fable, fleet-orchestrate | They assume a work Mac that is locked to Bedrock. |
| synced | Claude.ai sync cache, not a skill. |

## Plugins from the home server

| Plugin | Fate |
|---|---|
| superpowers | Installed as skills, so Codex and opencode get it too. |
| caveman, ponytail | Dropped on request. |
| compound-engineering | Dropped. The superpowers skills and the `build` pipeline cover the same work. |
| speculate-autowrap, chuzom MCP, local LLM MCP servers | Dropped. Local experiments, replaced by the routing group. |
| pyright-lsp, rust-analyzer-lsp | Optional `lsp` group. Claude Code only. |
