# API tokens

Create and revoke tokens in **User profile → API Tokens** (`/users/self/apitokens/`).
Copy the token after creation; it is shown only once. Authenticate requests with
`Authorization: Bearer <token>` or configure it as reptor's `REPTOR_TOKEN`.

## Restrict a token to projects (Pro)

In **Create API Token**, select one or more projects in **Restrict to projects**.
Leave the selection empty to create an unrestricted token with your normal API access.
Only projects accessible without elevated admin mode can be selected.

Restricted tokens default to **Read only**, which permits reading project content,
checking reports, and exporting projects, notes, and PDFs. Disable **Read only** to
also create, edit, and delete project content such as findings, notes, and files.
Restricted tokens additionally have read access to the **global finding-template library**.

The expiration date defaults to one calendar month for restricted tokens. You can
choose another date or clear the field for no expiration. Unrestricted tokens keep
their existing expiration defaults. A token remains valid through its expiration date (UTC).

Restricted tokens act as their creator and cannot exceed the creator's current
permissions. Losing access to a selected project removes the token's access to that
project. Other selected projects remain accessible. Deleting all selected projects
never makes a token unrestricted. Finished-project and guest-user restrictions apply.

Every API action must be explicitly allowed for restricted tokens. Project settings,
membership and sharing management, project creation/deletion/archiving, design edits,
template edits, personal notes, AI/plugin APIs, and token management are not allowed.
Restricted tokens cannot enable administrator permissions. They stop working without
a Professional license, but remain listed and can be revoked through the existing
token-management views.

The token list shows selected projects and access level. Administrators and User
Managers retain their existing ability to inspect and revoke tokens through user
management. Change a token's permissions or expiry by revoking it and creating a replacement.

## reptor MCP

Configure reptor with a selected project and the token. For read-only tokens, start
MCP with `reptor mcp --read-only` to hide its write tools. The API enforces the token's
permissions regardless of this client option.

Project findings, sections, notes, their schemas, and template search/retrieval are
supported. Note updates use PUT and are available with read/write tokens.
Personal-note mode is not supported by restricted tokens. The current MCP server
uses one configured project per instance; a token may authorize several projects.

## REST API creation

Use an authenticated, recently reauthenticated browser session to POST to
`/api/v1/pentestusers/self/apitokens/`:

```json
{
  "name": "Reporting assistant",
  "projects": ["41c09e60-44f1-453b-98f3-3f1875fe90fe"],
  "read_only": true,
  "expire_date": null
}
```

Omitting `expire_date` gives a restricted token the one-month default; explicit
`null` disables expiration. Omitting `projects` or passing `[]` creates an
unrestricted token. `read_only: true` requires at least one project. The response
includes `is_project_restricted`, project IDs, visible project names, and the secret.
Subsequent list/retrieve responses never include the secret.
