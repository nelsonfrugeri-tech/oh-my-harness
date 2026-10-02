---
name: site-expose
description: "Temporarily expose a finished local HTML report through an authenticated HTTPS tunnel. Use only after fresh authorization for the exact artifact; verify access controls and exact teardown ownership."
---

# Site Expose

Generation never authorizes publication. Resolve the sites root with
`python3 "<skill-dir>/../kb-write/scripts/kb/adapters/paths.py" OMH_SITES_ROOT`.
Exit 3 (`missing path: <VAR>`) and exit 2 (an invalid configuration) both stop the step without a
default; follow the round trip in [machine paths](../kb-write/references/machine-paths.md). Resolve the
final file inside that root, hash exact
bytes, and scan for secrets, personal data, internal hosts, and non-public content. Matches block
until removed or accepted specifically. Resolve the abstract `tunnel` capability; configured does not mean authorized,
reachable, or healthy. Never install/authenticate implicitly.

After artifact/provider are final, show path, hash, scan, provider, and visibility implications.
Obtain fresh explicit authorization. Prior approval or a different hash is insufficient.

Create mode-0700 temporary runtime state. Generate one-run credentials kept only in environment/chat,
never files, history, config, or logs. Use [scripts/auth_server.py](scripts/auth_server.py) for a loopback authenticated origin
when needed and pin approved hash. Record origin/tunnel PIDs, executable/start identity, port, hash,
provider, and URL. PID alone is insufficient; never kill by name/broad match.

| Endpoint | Anonymous | Authenticated |
| --- | ---: | ---: |
| Loopback origin | 401 | 200 |
| Public HTTPS URL | 401 | 200 |

Require a public URL beginning with `https://` and verify approved content without auth bypass. Anonymous public success requires terminating
verified owned processes and withholding credentials. Disclose URL/credentials only after passing,
with expiry, limitations, and teardown instruction.

For teardown, confirm each process matches ownership record, TERM, wait boundedly, and KILL only that
verified process if needed. Remove runtime state after exit and confirm public URL is unreachable.
If impossible, report teardown incomplete. Never affect another site, server, or tunnel.
