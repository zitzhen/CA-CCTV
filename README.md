# CA-CCTV

> 📺 Watch Certificate Authorities like a CCTV camera.

CA-CCTV continuously monitors Certificate Transparency (CT) logs and alerts you whenever a new TLS certificate is issued for your domains.

Powered by GitHub Actions, crt.sh, and email notifications.

## Features

* 🔍 Monitor one or multiple domains
* 📜 Query public Certificate Transparency logs
* 🚨 Email notifications for newly issued certificates
* 💾 Persistent certificate state tracking
* ⚡ Zero-server deployment using GitHub Actions
* 🆓 Runs entirely on GitHub Free plans

---

## Why CA-CCTV?

Unexpected certificate issuance can indicate:

* Misconfigured automation
* Forgotten infrastructure
* Third-party service activity
* Compromised CA validation processes
* Unauthorized certificate issuance

CA-CCTV acts like a CCTV camera for Certificate Authorities, helping you notice certificate activity as soon as possible.

---

## Quick Start

### 1. Use this template

Click:

```text
Use this template
↓
Create a new repository
```

Create your own repository from this template.

---

### 2. Configure monitored domains

Edit `domains.txt`.

Example:

```text
# One domain per line

example.com
example.org
subdomain.example.net
```

Comments beginning with `#` and blank lines are ignored.

---

### 3. Configure repository secrets

Navigate to:

```text
Repository
→ Settings
→ Secrets and variables
→ Actions
```

Create the following repository secrets:

| Secret        | Description                  |
| ------------- | ---------------------------- |
| SMTP_HOST     | SMTP server hostname         |
| SMTP_PORT     | SMTP server port             |
| SMTP_USER     | SMTP username                |
| SMTP_PASSWORD | SMTP password / app password |
| MAIL_TO       | Notification recipient       |
| MAIL_FROM     | Sender address (optional)    |

Example:

```text
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@email.com
SMTP_PASSWORD=xxxxxxxxxxxxxxxx
MAIL_TO=you@example.com
MAIL_FROM=CA-CCTV <your@email.com>
```

> Most providers require an App Password instead of your normal account password.

---

### 4. Enable GitHub Actions

Navigate to:

```text
Repository
→ Actions
```

If GitHub asks for permission:

```text
Enable workflows
```

Make sure Actions are enabled for the repository.

---

### 5. Initialize state

Run the workflow manually once:

```text
Actions
→ CA-CCTV
→ Run workflow
→ init = true
```

This imports currently known certificates into the local state database.

No notification emails will be sent during initialization.

---

### 6. Done

CA-CCTV will automatically run on schedule.

Whenever a new certificate appears in CT logs, an email alert will be sent.

---

## How It Works

```text
GitHub Actions
        │
        ▼
     crt.sh
        │
        ▼
 Certificate Transparency Logs
        │
        ▼
 Compare With Previous State
        │
        ▼
 New Certificate Found?
        │
   ┌────┴────┐
   │         │
  No        Yes
   │         │
   ▼         ▼
 Finish   Send Email
```

---

## Project Structure

```text
.
├── domains.txt
├── ct_watch.py
├── email.py
├── .ct-state/
│   └── *.json
└── .github/
    └── workflows/
        └── ca-cctv.yml
```

---

## Limitations

* Relies on public CT log visibility.
* Detection speed depends on CT log publication and crt.sh indexing.
* Email delivery depends on your SMTP provider.

---

## License

Apache License 2.0 

---

Made with ☕, Python and too much curiosity.
