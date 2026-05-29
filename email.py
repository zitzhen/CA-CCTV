#!/usr/bin/env python3
"""
CA-CCTV email notifier.

This script is designed for GitHub Actions. Pass secrets/config through
environment variables, and pass the certificate summary through CLI args.

Required env vars:
  SMTP_HOST       SMTP server host, e.g. smtp.gmail.com
  SMTP_USER       SMTP login username
  SMTP_PASSWORD   SMTP password / app password / authorization code
  MAIL_TO         Recipient email address, comma-separated if multiple

Optional env vars:
  SMTP_PORT       SMTP server port. Default: 587
  SMTP_SECURITY   starttls, ssl, or none. Default: starttls
  MAIL_FROM       Sender address. Default: SMTP_USER
  MAIL_FROM_NAME  Sender display name. Default: CA-CCTV
  MAIL_SUBJECT    Subject prefix. Default: CA-CCTV Alert
  GITHUB_REPOSITORY, GITHUB_RUN_ID are used automatically when available.

Example:
  python email.py --count 2 --summary-file new_certs.txt
"""

from __future__ import annotations

import argparse
import os
import smtplib
import ssl
import sys
from email.message import EmailMessage
from email.utils import formataddr
from pathlib import Path


DEFAULT_SUBJECT_PREFIX = "CA-CCTV Alert"


def env_required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def env_optional(name: str, default: str = "") -> str:
    value = os.environ.get(name, "").strip()
    return value if value else default


def parse_recipients(raw: str) -> list[str]:
    recipients = [item.strip() for item in raw.split(",") if item.strip()]
    if not recipients:
        raise RuntimeError("MAIL_TO is empty")
    return recipients


def read_summary(args: argparse.Namespace) -> str:
    if args.summary_file:
        path = Path(args.summary_file)
        if not path.exists():
            raise FileNotFoundError(f"Summary file not found: {path}")
        return path.read_text(encoding="utf-8").strip()

    if args.summary:
        return args.summary.strip()

    stdin_data = sys.stdin.read().strip() if not sys.stdin.isatty() else ""
    if stdin_data:
        return stdin_data

    return "New certificate(s) were detected, but no summary was provided."


def github_run_url() -> str:
    repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
    run_id = os.environ.get("GITHUB_RUN_ID", "").strip()
    if repo and run_id:
        return f"https://github.com/{repo}/actions/runs/{run_id}"
    return ""


def build_body(summary: str, count: int | None) -> str:
    title = "CA-CCTV detected new certificate transparency record(s)."
    lines = [title, ""]

    if count is not None:
        lines.append(f"New certificate count: {count}")
        lines.append("")

    lines.append("Details:")
    lines.append(summary)

    run_url = github_run_url()
    if run_url:
        lines.append("")
        lines.append(f"GitHub Actions run: {run_url}")

    lines.append("")
    lines.append("--")
    lines.append("Sent by CA-CCTV")

    return "\n".join(lines)


def build_message(
    *,
    sender: str,
    sender_name: str,
    recipients: list[str],
    subject: str,
    body: str,
) -> EmailMessage:
    message = EmailMessage()
    message["From"] = formataddr((sender_name, sender))
    message["To"] = ", ".join(recipients)
    message["Subject"] = subject
    message.set_content(body)
    return message


def send_message(message: EmailMessage, recipients: list[str]) -> None:
    host = env_required("SMTP_HOST")
    user = env_required("SMTP_USER")
    password = env_required("SMTP_PASSWORD")
    port = int(env_optional("SMTP_PORT", "587"))
    security = env_optional("SMTP_SECURITY", "starttls").lower()

    if security not in {"starttls", "ssl", "none"}:
        raise RuntimeError("SMTP_SECURITY must be one of: starttls, ssl, none")

    context = ssl.create_default_context()

    if security == "ssl":
        with smtplib.SMTP_SSL(host, port, context=context, timeout=30) as server:
            server.login(user, password)
            server.send_message(message, to_addrs=recipients)
        return

    with smtplib.SMTP(host, port, timeout=30) as server:
        server.ehlo()
        if security == "starttls":
            server.starttls(context=context)
            server.ehlo()
        server.login(user, password)
        server.send_message(message, to_addrs=recipients)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send CA-CCTV email alert")
    parser.add_argument("--summary", help="Certificate summary text")
    parser.add_argument("--summary-file", help="Read certificate summary from file")
    parser.add_argument("--count", type=int, help="New certificate count")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the email content without sending it",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    recipients = parse_recipients(env_required("MAIL_TO"))
    sender = env_optional("MAIL_FROM", env_required("SMTP_USER"))
    sender_name = env_optional("MAIL_FROM_NAME", "CA-CCTV")
    subject_prefix = env_optional("MAIL_SUBJECT", DEFAULT_SUBJECT_PREFIX)

    summary = read_summary(args)
    count = args.count

    subject_count = f"{count} new cert(s)" if count is not None else "new cert(s) detected"
    subject = f"{subject_prefix}: {subject_count}"
    body = build_body(summary, count)

    message = build_message(
        sender=sender,
        sender_name=sender_name,
        recipients=recipients,
        subject=subject,
        body=body,
    )

    if args.dry_run:
        print(message)
        return 0

    send_message(message, recipients)
    print(f"✅ Email sent to {', '.join(recipients)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
