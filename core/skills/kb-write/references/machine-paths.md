# Machine paths

The repository names no machine path. Three variables locate everything outside it:
`OMH_KB_ROOT` (the Markdown bundle), `OMH_KB_RUNTIME` (identity, Qdrant volume, venv, locks), and
`OMH_SITES_ROOT` (generated sites). Resolve them only with the standard-library resolver of the
kb-write skill, `<kb-write-dir>/scripts/kb/adapters/paths.py`; never read the variables directly
and never substitute a default.

## Resolution

A value comes from the CLI flag (`kb.py --root`), else the process environment, else the config
file. Print the config file this machine uses with `python3 <kb-write-dir>/scripts/kb/adapters/paths.py --config-file`;
it is `${XDG_CONFIG_HOME:-$HOME/.config}/omh/config`, ignoring a relative `XDG_CONFIG_HOME`.

The file holds `KEY=value` lines and `#` comment lines; it is not shell syntax. The last non-empty
assignment of a variable wins. A value is literal: an absolute path, or `~/` followed by a path.
Quotes, `$`, an inline `#` comment, an `export` prefix, `/`, and the home directory itself are
invalid.

| Resolver exit | stderr | Meaning |
| --- | --- | --- |
| 0 | — | stdout holds the absolute path |
| 3 | `missing path: <VAR>` | no layer defines the variable |
| 2 | `invalid path: <VAR>`, `unreadable config: <file>`, `invalid line <n>: <file>`, `unknown path: <VAR>`, `unusable home: …` | the configuration exists but is broken |

`kb.py` reports the same two cases as status `MissingPath` (exit 5) and `InvalidPath` (exit 6), with
the resolver line on stderr. Each Bash call starts a fresh shell, so resolve a path in the same
command that uses it.

## Round trip on exit 2 or 3

Stop the step. Never guess a path, read another bundle, or continue in a degraded mode. The
resolver line tells which of three outcomes happened:

| Outcome | Resolver line | Source to report | What the user fixes |
| --- | --- | --- | --- |
| Missing value | `missing path: <VAR>` | none | the value, written into the config file |
| Invalid value | `invalid path: <VAR>`, `invalid line <n>: <file>`, `unreadable config: <file>` | the environment if `<VAR>` is set there, else the config file | the value or the line, in that source |
| Config file cannot be located | `unusable home: …` (then `--config-file` fails too) | `HOME` or `XDG_CONFIG_HOME` | the environment variable; nothing is written |

- **A subagent** asks the user nothing. It returns the resolver line verbatim, the outcome and
  source above, the config file `--config-file` prints when it prints one, and the handoff below
  for the principal session. The handoff travels with the result, so the round trip works even when
  the principal's global guidance does not describe it.
- **The principal session**, including a session that runs a skill directly with no subagent:
  1. Show the user the line and the source.
  2. Ask for the fix. A suggestion is allowed only inside the question; change nothing until the
     user answers.
  3. Apply the answer yourself, never through a subagent:
     - **Missing or invalid value in the config file:** in the file `--config-file` prints, create
       the `omh/` directory if absent, replace the variable's existing line or append
       `<VAR>=<value>`, keep every other line, and end with a newline.
     - **Invalid value from the environment:** the environment wins over the file, so ask the user
       to fix or unset it; do not append a line that would be ignored.
     - **Config file cannot be located:** ask the user to fix `HOME` or `XDG_CONFIG_HOME`, rerun
       `--config-file`, and only then handle the value. Never invent a destination.
  4. Run the same step again.
