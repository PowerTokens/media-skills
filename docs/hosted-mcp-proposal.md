# Proposal: hosted PowerTokens MCP server with built-in OAuth (for PT eng)

Goal: user adds one URL, the agent pops a browser login, done. No key, no Python.

    claude mcp add --transport http powertokens https://mcp.powertokens.ai/mcp   # then /mcp → sign in
    codex mcp add powertokens --url https://mcp.powertokens.ai/mcp && codex mcp login powertokens

Both clients already support this (Streamable HTTP + OAuth 2.1 with discovery, PKCE, DCR and/or CIMD).
The plugin can ship the URL in its `.mcp.json` / `mcp.json` so installing the plugin is enough.

## What PT eng needs to build
1. **Remote MCP server** at e.g. `https://mcp.powertokens.ai/mcp` (Streamable HTTP). Tools:
   `list_models`, `estimate_cost`, `generate_video` (returns task_id fast), `get_video_task`
   (status + result URL), `generate_image`, `generate_speech`, `get_balance`.
   Long jobs must be async (Claude Code idle timeout ~5 min for HTTP; Codex tool timeout 60 s default).
   Return result URLs (signed, time-limited) rather than file bytes.
2. **OAuth 2.1 authorization server** (or reuse the one planned for Video Studio path A):
   - `/.well-known/oauth-protected-resource` on the MCP host (RFC 9728) + 401 with `WWW-Authenticate`.
   - `/.well-known/oauth-authorization-server` (RFC 8414) with `issuer`, `authorization_endpoint`,
     `token_endpoint`, `code_challenge_methods_supported: ["S256"]`, `scopes_supported`,
     `authorization_response_iss_parameter_supported: true` (Codex stable callback).
   - Client registration: **DCR** (RFC 7591) and/or **CIMD** (`client_id_metadata_document_supported: true`,
     `token_endpoint_auth_methods_supported` incl. `none`). Without these, users must pass a client id by hand.
   - Accept loopback redirects with **any port** (RFC 8252 §7.3): `http://127.0.0.1:*/callback*` and
     `http://localhost:*/callback` (Claude Code uses localhost; Codex uses 127.0.0.1 + callback id path).
   - Refresh tokens (`offline_access`) so users don't re-login.
   - Sign-up inside the login page (new users land there first) + free trial credits.
3. **Token → billing**: access token maps to the user's account/credits; same quota + 402/insufficient errors.
4. Optional: list in Anthropic connector directory and OpenAI plugin directory (public listing requires
   a remote HTTPS MCP endpoint; OpenAI portal does not accept API-key auth).

## Needed for the local `pt_login.py` (path A, same as Video Studio desktop)
`authorize_url`, `token_url`, a public `client_id` for media-skills, scope string, loopback redirect
rule (any port), token lifetime/refresh, and a userinfo/credits endpoint. Fill these into
`OAUTH_DEFAULTS` in `tools/shared/pt_login.py`, run `tools/sync_scripts.py`, release v0.2.
