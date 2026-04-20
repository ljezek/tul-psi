# Email Delivery — Decision Record

## Chosen approach: Azure Communication Services (ACS) Email

Email delivery uses **Azure Communication Services Email** with an auto-provisioned
Azure-managed domain. The app authenticates via the ACS **connection string** (an
API key, not a personal credential), stored as an encrypted ACA secret and injected
into the container as `ACS_CONNECTION_STRING`.

Emails are sent from `DoNotReply@<hash>.azurecomm.net` (the address provisioned by
ACS when the `AzureManagedDomain` resource is created).

### Why not SMTP with `lukas.jezek@tul.cz`?

TUL's SMTP server (`smtp.tul.cz:587`) requires password authentication. Storing a
personal TUL account password in any Azure resource (env var, ACA secret, Key Vault)
creates a credential-theft risk that is disproportionate for a student project. If
the credential leaked, an attacker would have full access to the TUL email account.

### Why not a Logic App HTTP trigger?

A Consumption Logic App with an SMTP connector would allow sending from
`lukas.jezek@tul.cz`, but adds an extra cloud resource, an extra HTTP hop, and a
trigger URL (acting as a secret) that needs protecting. The marginal benefit of the
personal sender address does not justify the added complexity.

### Why not Managed Identity for ACS?

Azure does have an RBAC role for ACS email sending, but the role name / GUID is not
stable across documentation sources, and the `azure-communication-email` SDK's
`TokenCredential` path requires additional verification. The connection string
approach is well-documented, the key is rotatable at any time via the Azure Portal,
and it never appears as a plain environment variable (stored as an ACA secret, which
is encrypted at rest and not visible in the portal env-vars tab).

## Escalation path

If a `@tul.cz` sender address becomes a requirement in the future:

1. Create a **Consumption Logic App** with an SMTP connector pointing at `smtp.tul.cz`.
2. Store the TUL password in the Logic App connection (encrypted within the Logic App,
   not accessible to the backend directly).
3. Expose an HTTP trigger endpoint; the backend calls it with the email payload.
4. Store only the trigger URL (a SAS token, rotatable) as an ACA secret.

This keeps personal credentials inside the Logic App connection, isolated from the
backend container.

## Bicep resources

| Resource | Name pattern | Notes |
|----------|-------------|-------|
| `Microsoft.Communication/emailServices` | `acs-email-spc-{env}` | Parent email service |
| `Microsoft.Communication/emailServices/domains` | `AzureManagedDomain` | Auto-provisioned domain |
| `Microsoft.Communication/communicationServices` | `acs-spc-{env}` | Communication service; connection string sourced here |

## ACA wiring

`compute.bicep` stores the connection string as an ACA secret (`acs-connection-string`)
and exposes it to the container via `secretRef`. The from-address is a plain env var
since it is not sensitive.

```
ACS_CONNECTION_STRING  →  secretRef: acs-connection-string  (encrypted ACA secret)
ACS_FROM_ADDRESS       →  plain env var
```

## Python SDK

```python
from azure.communication.email import EmailClient

client = EmailClient.from_connection_string(settings.acs_connection_string)
poller = client.begin_send({
    "senderAddress": settings.acs_from_address,
    "recipients": {"to": [{"address": recipient}]},
    "content": {"subject": subject, "plainText": body},
})
poller.result()  # blocks until ACS accepts the message
```
