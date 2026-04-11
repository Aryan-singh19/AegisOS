#!/usr/bin/env python3
import argparse
import json
import re
from dataclasses import dataclass
from typing import Any, Dict, Tuple


EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
IPV6_RE = re.compile(r"\b(?:[0-9a-fA-F]{1,4}:){2,7}[0-9a-fA-F]{1,4}\b")
TOKEN_RE = re.compile(r"\b(?:ghp_[A-Za-z0-9]{12,}|hf_[A-Za-z0-9]{12,}|sk-[A-Za-z0-9]{12,})\b")
JWT_RE = re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9._-]{8,}\.[A-Za-z0-9._-]{8,}\b")
CARD_RE = re.compile(r"\b(?:\d[ -]*?){13,19}\b")
PHONE_RE = re.compile(r"\b(?:\+?\d{1,3}[ -]?)?(?:\d{10,12})\b")

SENSITIVE_KEYS = {
    "password",
    "passwd",
    "secret",
    "token",
    "api_key",
    "apikey",
    "access_token",
    "refresh_token",
    "authorization",
    "auth",
    "cookie",
    "session",
    "email",
    "phone",
    "ip",
    "ipv4",
    "ipv6",
}


@dataclass
class RedactionStats:
  redacted_email: int = 0
  redacted_ip: int = 0
  redacted_token: int = 0
  redacted_jwt: int = 0
  redacted_card: int = 0
  redacted_phone: int = 0
  redacted_sensitive_key: int = 0

  def total(self) -> int:
    return (
        self.redacted_email
        + self.redacted_ip
        + self.redacted_token
        + self.redacted_jwt
        + self.redacted_card
        + self.redacted_phone
        + self.redacted_sensitive_key
    )

  def to_json(self) -> Dict[str, int]:
    return {
        "schema_version": 1,
        "redacted_email": self.redacted_email,
        "redacted_ip": self.redacted_ip,
        "redacted_token": self.redacted_token,
        "redacted_jwt": self.redacted_jwt,
        "redacted_card": self.redacted_card,
        "redacted_phone": self.redacted_phone,
        "redacted_sensitive_key": self.redacted_sensitive_key,
        "total_redactions": self.total(),
    }


def _sub_with_counter(pattern: re.Pattern, text: str, replacement: str) -> Tuple[str, int]:
  count = 0

  def repl(_: re.Match) -> str:
    nonlocal count
    count += 1
    return replacement

  return pattern.sub(repl, text), count


def redact_log_line(line: str, stats: RedactionStats | None = None) -> str:
  if stats is None:
    stats = RedactionStats()
  out = line
  out, c = _sub_with_counter(EMAIL_RE, out, "[REDACTED_EMAIL]")
  stats.redacted_email += c
  out, c = _sub_with_counter(IPV4_RE, out, "[REDACTED_IP]")
  stats.redacted_ip += c
  out, c = _sub_with_counter(IPV6_RE, out, "[REDACTED_IP]")
  stats.redacted_ip += c
  out, c = _sub_with_counter(TOKEN_RE, out, "[REDACTED_TOKEN]")
  stats.redacted_token += c
  out, c = _sub_with_counter(JWT_RE, out, "[REDACTED_JWT]")
  stats.redacted_jwt += c
  out, c = _sub_with_counter(CARD_RE, out, "[REDACTED_CARD]")
  stats.redacted_card += c
  out, c = _sub_with_counter(PHONE_RE, out, "[REDACTED_PHONE]")
  stats.redacted_phone += c
  return out


def _redact_obj(obj: Any, stats: RedactionStats) -> Any:
  if isinstance(obj, dict):
    redacted = {}
    for key, value in obj.items():
      key_l = str(key).lower()
      if key_l in SENSITIVE_KEYS:
        stats.redacted_sensitive_key += 1
        redacted[key] = "[REDACTED]"
      else:
        redacted[key] = _redact_obj(value, stats)
    return redacted
  if isinstance(obj, list):
    return [_redact_obj(x, stats) for x in obj]
  if isinstance(obj, str):
    return redact_log_line(obj, stats)
  return obj


def redact_metrics_payload(payload: Dict[str, Any]) -> Tuple[Dict[str, Any], RedactionStats]:
  stats = RedactionStats()
  redacted = _redact_obj(payload, stats)
  if not isinstance(redacted, dict):
    raise ValueError("metrics payload must remain an object")
  return redacted, stats


def redact_trace_payload(payload: Any) -> Tuple[Any, RedactionStats]:
  stats = RedactionStats()
  return _redact_obj(payload, stats), stats


def redact_telemetry_bundle(bundle: Dict[str, Any]) -> Dict[str, Any]:
  if not isinstance(bundle, dict):
    raise ValueError("bundle must be an object")
  logs = bundle.get("logs", [])
  metrics = bundle.get("metrics", {})
  traces = bundle.get("traces", [])
  if not isinstance(logs, list):
    raise ValueError("logs must be a list")
  if not isinstance(metrics, dict):
    raise ValueError("metrics must be an object")
  red_logs = []
  total_stats = RedactionStats()
  for line in logs:
    safe_line = redact_log_line(str(line), total_stats)
    red_logs.append(safe_line)
  red_metrics, ms = redact_metrics_payload(metrics)
  red_traces, ts = redact_trace_payload(traces)
  total_stats.redacted_email += ms.redacted_email + ts.redacted_email
  total_stats.redacted_ip += ms.redacted_ip + ts.redacted_ip
  total_stats.redacted_token += ms.redacted_token + ts.redacted_token
  total_stats.redacted_jwt += ms.redacted_jwt + ts.redacted_jwt
  total_stats.redacted_card += ms.redacted_card + ts.redacted_card
  total_stats.redacted_phone += ms.redacted_phone + ts.redacted_phone
  total_stats.redacted_sensitive_key += ms.redacted_sensitive_key + ts.redacted_sensitive_key
  return {
      "schema_version": 1,
      "logs": red_logs,
      "metrics": red_metrics,
      "traces": red_traces,
      "redaction_summary": total_stats.to_json(),
  }


def parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser(description="Redact sensitive fields from telemetry bundle JSON.")
  parser.add_argument("--input", required=True, help="Path to telemetry bundle JSON file")
  parser.add_argument("--output", required=True, help="Path to write redacted bundle JSON")
  return parser.parse_args()


def main() -> int:
  args = parse_args()
  with open(args.input, "r", encoding="utf-8") as f:
    bundle = json.load(f)
  redacted = redact_telemetry_bundle(bundle)
  with open(args.output, "w", encoding="utf-8", newline="\n") as f:
    json.dump(redacted, f, indent=2)
    f.write("\n")
  print(json.dumps(redacted["redaction_summary"], separators=(",", ":")))
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
