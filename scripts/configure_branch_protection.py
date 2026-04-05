#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys


def run(args, stdin_text=None):
  return subprocess.run(args, input=stdin_text, capture_output=True, text=True, check=False)


def main():
  parser = argparse.ArgumentParser(description="Configure GitHub branch protection profile.")
  parser.add_argument("repo", help="Repository in owner/repo format")
  parser.add_argument("--branch", default="main", help="Branch name (default: main)")
  parser.add_argument("--apply", action="store_true", help="Apply profile via gh api")
  parser.add_argument("--enforce-admins", action="store_true", help="Enable admin enforcement")
  args = parser.parse_args()
  repo = args.repo
  payload = {
      "required_status_checks": {
          "strict": True,
          "checks": [
              {"context": "CI / build-kernel-sim"},
              {"context": "Docs / markdown-lint"},
              {"context": "Clang Matrix / clang-build-and-test (c11)"},
              {"context": "Clang Matrix / clang-build-and-test (c17)"},
              {"context": "Clang Matrix / clang-sanitizers"},
              {"context": "Clang Matrix / trace-json-property-smoke"},
          ],
      },
      "enforce_admins": args.enforce_admins,
      "required_pull_request_reviews": {
          "dismiss_stale_reviews": True,
          "require_code_owner_reviews": True,
          "required_approving_review_count": 1,
      },
      "restrictions": None,
      "allow_force_pushes": False,
      "allow_deletions": False,
      "required_linear_history": True,
      "required_conversation_resolution": True,
  }
  print("Branch protection payload:")
  print(json.dumps(payload, indent=2))
  if not args.apply:
    print("")
    print("Dry-run complete. Re-run with --apply to enforce this profile.")
    return 0

  endpoint = f"repos/{repo}/branches/{args.branch}/protection"
  applied = run(["gh", "api", "--method", "PUT", endpoint, "--input", "-"],
                stdin_text=json.dumps(payload))
  if applied.returncode != 0:
    print("Failed to apply branch protection profile.")
    if applied.stderr.strip():
      print(applied.stderr.strip())
    return 2
  print("")
  print(f"Applied branch protection on {repo}:{args.branch}")
  verify = run(["gh", "api", endpoint])
  if verify.returncode == 0 and verify.stdout.strip():
    print("Verification snapshot:")
    print(verify.stdout.strip())
  else:
    print("Applied, but verification fetch failed.")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
