#!/usr/bin/env python3
"""
CA-CCTV / CT Watch

Read domains from domains.txt, query crt.sh Certificate Transparency records,
compare with local state, and print newly discovered certificates.

Typical GitHub Actions usage:
  python ct_watch.py

Useful options:
  python ct_watch.py --domains domains.txt --state-dir .ct-state
  python ct_watch.py liuxiaozhen.dev zitzhen.cn
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests


DEFAULT_DOMAINS_FILE = "domains.txt"
DEFAULT_STATE_DIR = ".ct-state"
DEFAULT_TIMEOUT = (10, 90)
DEFAULT_RETRIES = 3


@dataclass(frozen=True)
class NewCert:
    domain: str
    cert_id: str
    issuer_name: str
    not_before: str
    not_after: str
    name_value: str


def normalize_domain(domain: str) -> str:
    """Normalize user-provided domain strings from domains.txt / CLI."""
    domain = domain.strip().lower()

    # Allow users to paste URLs accidentally.
    domain = re.sub(r"^https?://", "", domain)
    domain = domain.split("/")[0]
    domain = domain.split(":")[0]
    domain = domain.strip(".")

    return domain


def load_domains(path: Path) -> list[str]:
    """Load domains from a text file, ignoring empty lines and comments."""
    if not path.exists():
        raise FileNotFoundError(
            f"Domains file not found: {path}\n"
            f"Create {path} and put one domain per line, for example:\n"
            "liuxiaozhen.dev\n"
            "zitzhen.cn\n"
        )

    domains: list[str] = []
    seen: set[str] = set()

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue

        # Support inline comments:
        # example.com  # my website
        line = line.split("#", 1)[0].strip()
        domain = normalize_domain(line)

        if not domain:
            continue

        if domain in seen:
            continue

        seen.add(domain)
        domains.append(domain)

    return domains


def load_seen(path: Path) -> set[str]:
    """Load known certificate IDs from a JSON state file."""
    if not path.exists():
        return set()

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print(f"[!] State file is broken, ignoring it: {path}", file=sys.stderr)
        return set()

    if isinstance(data, list):
        return {str(item) for item in data}

    if isinstance(data, dict) and isinstance(data.get("seen"), list):
        return {str(item) for item in data["seen"]}

    print(f"[!] State file format is unknown, ignoring it: {path}", file=sys.stderr)
    return set()


def save_seen(path: Path, seen: set[str]) -> None:
    """Save known certificate IDs to a JSON state file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(sorted(seen), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def state_path_for_domain(state_dir: Path, domain: str) -> Path:
    """Create a safe per-domain state path."""
    safe_name = re.sub(r"[^a-z0-9.-]+", "_", domain)
    return state_dir / f"{safe_name}.json"


def fetch_certs(domain: str, *, retries: int = DEFAULT_RETRIES) -> list[dict[str, Any]]:
    """Query crt.sh JSON API for a domain and its subdomains."""
    url = "https://crt.sh/"
    params = {
        "q": f"%.{domain}",
        "output": "json",
        "deduplicate": "Y",
    }
    headers = {
        "User-Agent": "CA-CCTV/1.0 (+https://github.com/Iamliuxiaozhen/CA-CCTV)"
    }

    last_error: Exception | None = None

    for attempt in range(1, retries + 1):
        try:
            print(f"[*] Query crt.sh for {domain} ({attempt}/{retries})...")
            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=DEFAULT_TIMEOUT,
            )
            response.raise_for_status()

            # crt.sh may occasionally return invalid/empty JSON when overloaded.
            data = response.json()
            if not isinstance(data, list):
                raise ValueError(f"unexpected crt.sh response type: {type(data).__name__}")

            return data

        except (requests.exceptions.RequestException, ValueError) as exc:
            last_error = exc
            print(f"[!] crt.sh query failed for {domain}: {exc}", file=sys.stderr)

            if attempt < retries:
                time.sleep(5 * attempt)

    raise RuntimeError(f"crt.sh query failed after {retries} retries for {domain}: {last_error}")


def cert_key(cert: dict[str, Any]) -> str | None:
    """
    Return a stable identifier for a certificate entry.

    crt.sh normally returns "id". Keep a fallback so weird entries do not
    silently disappear.
    """
    cert_id = cert.get("id")
    if cert_id is not None:
        return str(cert_id)

    fallback_parts = [
        str(cert.get("issuer_name", "")),
        str(cert.get("not_before", "")),
        str(cert.get("not_after", "")),
        str(cert.get("name_value", "")),
    ]
    fallback = "|".join(fallback_parts).strip("|")
    return fallback or None


def build_new_cert(domain: str, cert: dict[str, Any]) -> NewCert:
    return NewCert(
        domain=domain,
        cert_id=str(cert.get("id", "")),
        issuer_name=str(cert.get("issuer_name", "")),
        not_before=str(cert.get("not_before", "")),
        not_after=str(cert.get("not_after", "")),
        name_value=str(cert.get("name_value", "")),
    )


def scan_domain(domain: str, state_dir: Path, *, init: bool = False) -> list[NewCert]:
    """Scan one domain and return newly discovered certificates."""
    state_path = state_path_for_domain(state_dir, domain)
    seen = load_seen(state_path)

    certs = fetch_certs(domain)
    current_keys: set[str] = set()
    new_items: list[NewCert] = []

    for cert in certs:
        key = cert_key(cert)
        if not key:
            continue

        current_keys.add(key)

        if key not in seen:
            if not init:
                new_items.append(build_new_cert(domain, cert))
            seen.add(key)

    # Keep old IDs too. Some crt.sh results may temporarily disappear.
    save_seen(state_path, seen | current_keys)

    return new_items


def print_report(new_items: list[NewCert]) -> None:
    if not new_items:
        print("✅ 没发现新证书")
        return

    print(f"🚨 发现 {len(new_items)} 张新证书：\n")

    for cert in new_items:
        print("=" * 72)
        print(f"Domain:     {cert.domain}")
        print(f"ID:         {cert.cert_id}")
        print(f"Issuer:     {cert.issuer_name}")
        print(f"Not Before: {cert.not_before}")
        print(f"Not After:  {cert.not_after}")
        print("Names:")
        print(cert.name_value)
        print()


def write_github_output(new_items: list[NewCert]) -> None:
    """
    Expose result to GitHub Actions.

    Outputs:
      has_new: true/false
      count: number
      summary: markdown-ish plain text summary
    """
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        return

    has_new = "true" if new_items else "false"
    lines = []
    for cert in new_items:
        names = cert.name_value.replace("\r\n", "\n").replace("\r", "\n")
        lines.append(
            f"- `{cert.domain}` ID `{cert.cert_id}` | {cert.issuer_name} | "
            f"{cert.not_before} → {cert.not_after}\n"
            f"  Names: `{names}`"
        )

    summary = "\n".join(lines) if lines else "No new certificates."

    with open(output_path, "a", encoding="utf-8") as fh:
        fh.write(f"has_new={has_new}\n")
        fh.write(f"count={len(new_items)}\n")
        fh.write("summary<<EOF\n")
        fh.write(summary)
        fh.write("\nEOF\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CA-CCTV Certificate Transparency watcher")
    parser.add_argument(
        "domains",
        nargs="*",
        help="Domains to scan. If omitted, domains are read from domains.txt.",
    )
    parser.add_argument(
        "--domains-file",
        default=DEFAULT_DOMAINS_FILE,
        help=f"Domain list file. Default: {DEFAULT_DOMAINS_FILE}",
    )
    parser.add_argument(
        "--state-dir",
        default=DEFAULT_STATE_DIR,
        help=f"Directory used to store seen certificate IDs. Default: {DEFAULT_STATE_DIR}",
    )
    parser.add_argument(
        "--init",
        action="store_true",
        help="Initialize state without reporting existing certificates as new.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    cli_domains = [normalize_domain(domain) for domain in args.domains]
    cli_domains = [domain for domain in cli_domains if domain]

    if cli_domains:
        domains = list(dict.fromkeys(cli_domains))
    else:
        domains = load_domains(Path(args.domains_file))

    if not domains:
        print("[*] No domains to scan. Nothing to do.")
        write_github_output([])
        return 0

    print("Domains to be scanned:")
    for domain in domains:
        print(f"- {domain}")
    print()

    all_new_items: list[NewCert] = []
    state_dir = Path(args.state_dir)

    had_error = False

    for domain in domains:
        try:
            all_new_items.extend(scan_domain(domain, state_dir, init=args.init))
        except Exception as exc:
            had_error = True
            print(f"[!] Failed to scan {domain}: {exc}", file=sys.stderr)

    print()
    if args.init:
        print("✅ 初始化完成：已有证书已写入状态文件，本次不报警。")
    else:
        print_report(all_new_items)

    write_github_output(all_new_items)

    if had_error:
        return 1

    # Exit 0 even if new certs were found.
    # Let GitHub Actions continue to the email/notification step.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
