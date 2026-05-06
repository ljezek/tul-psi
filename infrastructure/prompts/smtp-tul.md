# Email Delivery — Decision Record

## Chosen approach: SMTP relay via SMTP2Go

Email delivery uses **SMTP2Go** as a transactional relay with a verified custom sender
address (`tul-projects@jezci.net`).  The backend connects over SMTP with STARTTLS
(port 587) using an SMTP2Go account credential stored as an encrypted ACA secret.

### Why SMTP2Go over Azure Communication Services (ACS)?

ACS with an Azure-managed domain sent from `DoNotReply@<hash>.azurecomm.net`.  That
address cannot be customised, and the domain lacks sender-specific SPF/DKIM alignment,
which causes many mail servers — including University ones — to classify the messages
as spam.  SMTP2Go with a verified custom domain solves all three problems:

- **Custom sender** — recipients see `TUL Student Projects <tul-projects@jezci.net>`.
- **SPF alignment** — `jezci.net` SPF record includes SMTP2Go's sending IPs.
- **DKIM signing** — SMTP2Go signs each message with a key published on `jezci.net`.
- **DMARC policy** — `_dmarc.jezci.net` enforces quarantine and enables aggregate reporting.

### Why not raw SMTP to jezci.net hosting?

Shared-hosting outbound SMTP is typically IP-reputation-tainted and queue-managed
poorly for transactional OTP delivery.  SMTP2Go is purpose-built for transactional
mail with a strong sending reputation and a generous free tier (1 000 emails/month).

### Why not the personal `lukas.jezek@tul.cz` address?

TUL's SMTP server requires a personal account password.  Storing that credential in
Azure would create a disproportionate credential-theft risk.  A dedicated
`tul-projects@jezci.net` address carries no risk beyond this project.

## Required DNS records on jezci.net

These records must be added before the first production deployment.  Exact values
(especially the DKIM key) are generated in the SMTP2Go sender-domain dashboard.

| Type | Name | Value |
|------|------|-------|
| TXT  | `jezci.net` | `v=spf1 include:mail.smtp2go.com ~all` |
| TXT  | `mail._domainkey.jezci.net` | DKIM public key from SMTP2Go dashboard |
| TXT  | `_dmarc.jezci.net` | `v=DMARC1; p=quarantine; rua=mailto:postmaster@jezci.net` |

## ACA wiring

`compute.bicep` stores the SMTP password as an ACA secret (`smtp-password`) and
exposes it to the container via `secretRef`.  All other SMTP settings are plain env
vars since they are not sensitive.

```
SMTP_HOST         →  plain env var   (mail.smtp2go.com)
SMTP_PORT         →  plain env var   (587)
SMTP_USERNAME     →  plain env var   (SMTP2Go SMTP username)
SMTP_PASSWORD     →  secretRef: smtp-password  (encrypted ACA secret)
SMTP_FROM_ADDRESS →  plain env var   (tul-projects@jezci.net)
```

## Python implementation

```python
import aiosmtplib
from email.message import EmailMessage as MIMEMessage

mime_message = MIMEMessage()
mime_message["From"] = f"TUL Student Projects <{settings.smtp_from_address}>"
mime_message["To"] = recipient
mime_message["Subject"] = subject
mime_message.set_content(body)

await aiosmtplib.send(
    mime_message,
    hostname=settings.smtp_host,
    port=settings.smtp_port,          # 587
    username=settings.smtp_username,
    password=settings.smtp_password,
    start_tls=True,
)
```
