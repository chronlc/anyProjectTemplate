# Naming Scheme (case-sensitive)

This file is the authoritative registry for naming conventions used in the project.
Agents must consult and update this file before adding new public symbols.

Format:
- Type: category (module/class/function/variable/memory-key)
- Name: exact-case name
- Purpose: short description
- Owner: agent/human responsible

Examples:
- module: scripts.ai_tools.reader — feature model parser
- function: load_feature_model — parse the PROJECT_FEATURES.md into a dict
- memory-key: @anyProjectTemplate:feature_model:v1 — persisted feature model JSON

# Registry

- module: scripts.ai_tools.reader — feature model parser — owner: ai-agent
- module: scripts.ai_tools.generator — scaffold generator — owner: ai-agent
- module: scripts.ai_tools.mcp_sync — mcp sync helper — owner: ai-agent
- memory-key: @anyProjectTemplate:feature_model:v1 — stored feature model
- memory-key: @anyProjectTemplate:scaffold_marker — scaffold marker info

# Rules

- Names are case-sensitive. Always reference names exactly.
- Add new entries here before introducing public symbols into the repo.
- Keep memory keys namespaced under `@anyProjectTemplate:` to prevent collisions.

