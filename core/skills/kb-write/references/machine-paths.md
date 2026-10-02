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

Stop the step. Never guess a path, read another bundle, or continue in a degraded mode.

- **A subagent** asks the user nothing and returns the resolver's stderr line verbatim.
- **The principal session**, including a session that runs a skill directly with no subagent:
  1. Show the user the line. For exit 2, also say where the bad value came from: the environment
     or the config file.
  2. Ask for the value. A suggestion is allowed only inside the question; write nothing until the
     user answers.
  3. Write the answer yourself, never through a subagent. In the file `--config-file` prints,
     create the `omh/` directory if absent, replace the variable's existing line or append
     `<VAR>=<value>`, keep every other line, and end with a newline. If the bad value comes from
     the environment, the environment wins over the file: ask the user to fix or unset it instead.
  4. Run the same step again.
