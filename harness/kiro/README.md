# Kiro permissions

`permissions.yaml` is generated from the canonical policy in `core/policies/permissions.json`:
allow everything, ask before deleting files or artifacts or reading secrets, and deny a short list
of irreversible actions. Do not edit it by hand. Change the policy, then run from the repository
root:

```bash
python3 -m installers.policy.render --write
python3 -m installers.policy.render --check
```

No installer writes Kiro state; the copy below is manual.

## Install

Kiro reads user rules from `~/.kiro/settings/permissions.yaml`; they apply to every project. Rules
are combined across scopes and the most restrictive effect wins (`deny` > `ask` > `allow`).

1. Back up any existing file and read it before replacing it. Keep its `deny` rules; merge them into
   the new file instead of dropping them.

   ```bash
   mkdir -p ~/.kiro/settings
   [ -f ~/.kiro/settings/permissions.yaml ] && \
     cp ~/.kiro/settings/permissions.yaml ~/.kiro/settings/permissions.yaml.omh.bak
   cp harness/kiro/permissions.yaml ~/.kiro/settings/permissions.yaml
   ```

2. Remove `delete_file` from the agent you use (see the gaps below). In a custom agent profile, add:

   ```json
   { "excludedTools": ["delete_file"] }
   ```

3. In the IDE, use "Accept file changes" or "Approve for me"; ask rules still prompt in both. The
   CLI needs no `--trust-all-tools`.

Roll back by restoring `permissions.yaml.omh.bak`, or by deleting the copied file when none existed.

## Validate

Open a new session and run the six cases:

| # | Action | Expected |
| --- | --- | --- |
| 1 | Edit a normal file | No prompt |
| 2 | `ls`, `git status`, `npm test` | No prompt |
| 3 | `rm` a test file | Prompt |
| 4 | Read a `.env` file | Prompt |
| 5 | `cat ~/.aws/credentials` | Prompt (best effort) |
| 6 | Delete a file without naming `rm` | Prompt, through `rm`, `unlink`, or `find -delete` |

If a case misbehaves, stop and report it; do not loosen the policy to make it pass.

## Known gaps

- `delete_file` uses the `fs_write` capability, the same one as creating and editing files, so a
  path rule cannot single out deletion. Excluding the tool in a custom agent forces deletion
  through the shell, where the ask rules apply.
- Whether `~` expands to the home directory in `fs_read` patterns is not documented. Case 5 checks
  it; if it does not prompt, replace `~` with the absolute home path in the local copy.
- Shell rules match command text. `/bin/rm`, `bash -c`, and `python -c` invocations escape them.
- Reading a secret through the shell, such as `cat ~/.aws/credentials`, is gated only when Kiro
  applies `fs_read` rules to shell commands, which depends on its sandbox.
- Policy prefixes that contain a literal `*`, such as `rm -rf /*`, are not rendered because `*` is a
  wildcard in Kiro shell patterns; the broader `rm *` ask rule still prompts.
- Without an interactive client, Kiro treats every `ask` as `deny`.
- A plain `git push` while the default branch is checked out cannot be gated; protect the branch on
  the code host.

Run `python3 -m installers.policy.render --gaps kiro` for the list derived from the policy.

Reference: <https://kiro.dev/docs/permissions/> (inspected 2026-11-16).
