from __future__ import annotations

import re
import unittest
from pathlib import Path


_ROOT = Path(__file__).resolve().parents[2]
_SHARED_START = b"<!-- shared-guidance:start -->"
_SHARED_END = b"<!-- shared-guidance:end -->"
_CLAUDE_DELTA_START = b"<!-- claude-delta:start -->"
_CLAUDE_DELTA_END = b"<!-- claude-delta:end -->"
_CODEX_DELTA_START = b"<!-- codex-delta:start -->"
_CODEX_DELTA_END = b"<!-- codex-delta:end -->"

_CLAUDE_PREAMBLE = """# CLAUDE.md

Regras vinculantes deste ambiente. Aplicam-se a toda sessão do harness e a todo subagent.

<!-- Ordem = importância. O primeiro bloco governa como você pensa; o segundo, como você
     opera; os demais são contratos e ambiente. Alvo de tamanho: < 200 linhas — detalhe
     operacional mora nas skills, que carregam sob demanda. Antes de adicionar uma linha,
     pergunte: "remover isto faria o Claude errar?" Se não, não entra. -->

---"""

_CODEX_PREAMBLE = """# AGENTS.md

Regras vinculantes deste ambiente. Aplicam-se a toda sessão do Codex e a todo subagent.

<!-- Mantenha este arquivo curto e focado nas regras que precisam valer em toda sessão. Detalhes
     operacionais pertencem às skills e carregam sob demanda. Antes de adicionar uma regra,
     pergunte se removê-la faria o Codex agir incorretamente. -->

---"""

_CLAUDE_DELTA_HEADINGS = (
    "## Delta do Claude Code",
    "### Bindings e primitivos do Claude Code",
    "### Destino de sincronização do Claude Code",
)
_CODEX_DELTA_HEADINGS = (
    "## Delta do Codex",
    "### Limite de confirmação humana",
    "### Bindings e primitivos do Codex",
    "### Transcripts do Codex",
    "### Destinos de instalação do Codex",
)

_EXPECTED_CLAUDE_DELTA = """
## Delta do Claude Code

### Bindings e primitivos do Claude Code

Esta tabela lista apenas os providers conectados nesta máquina, não o catálogo de capabilities
possíveis. Cada máquina acrescenta as suas linhas.

| Capability | Papel | Provider Claude Code nesta máquina |
| --- | --- | --- |
| `web` | Busca e fetch na web | `WebSearch`, `WebFetch` |
| `code-graph` | Query/path/explain sobre um knowledge graph de codebase | `mcp__graphify__*` |
| `session-memory` | Memória bruta de sessões passadas: recall por tema, digest, `blame` por arquivo | `deja` CLI / `mcp__deja__*` |
| `framework-docs` | Documentação viva de LangChain, LangGraph e Deep Agents, resolvida em runtime | `mcp__plugin_langchain-mcp_langchain-docs__*`, `mcp__plugin_langchain-mcp_langchain-reference__*` |

**`framework-docs` não é automático no Codex.** No Claude Code os dois servidores vêm com o plugin
`langchain-mcp`; no Codex, instalar o plugin **não** é prova de que os servidores foram registrados —
confirme com `codex mcp list` antes de afirmar que a capability responde.

`Read`, `Write`, `Edit`, `Bash`, `Grep` e `Glob` são primitivos e não precisam de provider. Se um
MCP estiver deferido, carregue-o via `ToolSearch` antes de usá-lo.

### Destino de sincronização do Claude Code

A sincronização da biblioteca escreve apenas em `~/.claude/` e preserva skills e hooks instalados
por outras ferramentas.
"""

_EXPECTED_CODEX_DELTA = """
## Delta do Codex

### Limite de confirmação humana

Peça confirmação ao usuário somente antes de:

1. excluir, sobrescrever de forma irrecuperável ou destruir um artefato; ou
2. ler ou escrever um arquivo que provavelmente contenha credentials, tokens, senhas, private keys
   ou material equivalente de autenticação.

Não peça confirmação para leitura, escrita, execução de comandos, testes ou acesso à rede que sejam
rotineiros e estejam dentro das permissões efetivas da sessão. Uma negação técnica do sandbox não
transforma uma operação rotineira em decisão sensível: use primeiro os roots e profiles configurados
pelo adapter. Se uma restrição de maior precedência ainda exigir aprovação, explique que o prompt é
imposto pelo runtime e não pela política comportamental do oh-my-harness.

### Bindings e primitivos do Codex

A tabela é o adapter desta máquina. O installer pode preencher providers configuráveis sem alterar
agents ou skills.

| Capability | Finalidade | Provider Codex nesta máquina |
| --- | --- | --- |
| `code-host` | Pull Requests, issues e reviews remotos | _(configurar durante a instalação)_ |
| `ci` | Pipelines de CI/CD | _(configurar durante a instalação)_ |
| `web` | Busca e recuperação de páginas web | Capability web do Codex |
| `code-graph` | Query, path e explain sobre um knowledge graph de código | Graphify MCP com fallback para CLI |
| `session-memory` | Busca em transcripts de sessões passadas por tópico ou arquivo | Deja CLI ou MCP quando instalado |
| `framework-docs` | Documentação viva de LangChain, LangGraph e Deep Agents, resolvida em runtime | Servidores MCP `langchain-docs` e `langchain-reference` do plugin `langchain-mcp` |
| `tunnel` | Exposição temporária de um site local por URL autenticada | _(opcional; configurar um provider aprovado)_ |

**`framework-docs` não é automático no Codex.** No Claude Code os dois servidores vêm com o plugin
`langchain-mcp`; no Codex, instalar o plugin **não** é prova de que os servidores foram registrados —
confirme com `codex mcp list` antes de afirmar que a capability responde.

Built-ins do Codex para acesso ao filesystem, busca no repositório, execução de shell e aplicação de
patch não precisam de entradas no adapter.

### Transcripts do Codex

O Codex armazena transcripts ativos em
`$CODEX_HOME/sessions/YYYY/MM/DD/rollout-<timestamp>-<session-id>.jsonl`; o `CODEX_HOME` default é
`~/.codex`. A lógica de session memory deve descobrir o rollout correspondente em vez de assumir um
diretório derivado do nome do projeto. Se o transcript não puder ser resolvido, escreva o session
record com `transcript_path: null` e informe o modo degradado.

### Destinos de instalação do Codex

A instalação do adapter Codex escreve apenas em `$CODEX_HOME` e `~/.agents/`. Ela preserva
providers, hooks, skills e outros arquivos que não pertencem ao oh-my-harness.
"""


def _normalize(text: str) -> str:
    normalized_newlines = text.replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(line.rstrip() for line in normalized_newlines.split("\n")).strip("\n")


def _extract_unique(text: bytes, start: bytes, end: bytes) -> tuple[bytes, bytes, bytes]:
    if text.count(start) != 1 or text.count(end) != 1:
        raise ValueError(f"expected exactly one marker pair: {start}, {end}")
    before, remainder = text.split(start, 1)
    content, after = remainder.split(end, 1)
    if end in before or start in after:
        raise ValueError(f"misordered marker pair: {start}, {end}")
    return before, content, after


def _headings(text: str) -> tuple[str, ...]:
    return tuple(re.findall(r"(?m)^#{2,6} .+$", text))


class GlobalGuidanceParityTest(unittest.TestCase):
    def setUp(self) -> None:
        self._claude = _ROOT.joinpath("harness/claude/CLAUDE.md").read_bytes()
        self._codex = _ROOT.joinpath("harness/codex/AGENTS.md").read_bytes()

    def test_shared_guidance_is_identical(self) -> None:
        claude_shared = self._document(self._claude, _CLAUDE_PREAMBLE)[0]
        codex_shared = self._document(self._codex, _CODEX_PREAMBLE)[0]

        self._assert_shared_equal(claude_shared, codex_shared)

    def test_only_enumerated_runtime_deltas_are_allowed(self) -> None:
        _, claude_delta = self._document(self._claude, _CLAUDE_PREAMBLE)
        _, codex_delta = self._document(self._codex, _CODEX_PREAMBLE)

        self.assertEqual(_EXPECTED_CLAUDE_DELTA.encode("utf-8"), claude_delta)
        self.assertEqual(_EXPECTED_CODEX_DELTA.encode("utf-8"), codex_delta)
        self.assertEqual(_CLAUDE_DELTA_HEADINGS, _headings(claude_delta.decode("utf-8")))
        self.assertEqual(_CODEX_DELTA_HEADINGS, _headings(codex_delta.decode("utf-8")))

    def test_unenumerated_runtime_delta_text_is_detected(self) -> None:
        _, codex_delta = self._document(self._codex, _CODEX_PREAMBLE)
        mutated = codex_delta.replace(
            b"### Limite de confirma\xc3\xa7\xc3\xa3o humana\n",
            b"### Limite de confirma\xc3\xa7\xc3\xa3o humana\n\nTexto de delta n\xc3\xa3o enumerado.\n",
            1,
        )

        self.assertNotEqual(codex_delta, mutated)
        with self.assertRaises(AssertionError):
            self.assertEqual(_EXPECTED_CODEX_DELTA.encode("utf-8"), mutated)

    def test_codex_delta_retains_machine_capability_rows(self) -> None:
        _, codex_delta = self._document(self._codex, _CODEX_PREAMBLE)

        for capability in ("code-host", "ci", "tunnel"):
            with self.subTest(capability=capability):
                row_start = f"| `{capability}` |".encode("utf-8")
                self.assertIn(row_start, codex_delta)

    def test_word_mutation_in_shared_guidance_is_detected(self) -> None:
        claude_shared = self._document(self._claude, _CLAUDE_PREAMBLE)[0]
        codex_shared = self._document(self._codex, _CODEX_PREAMBLE)[0]
        mutated = codex_shared.replace(
            "O núcleo do comportamento".encode("utf-8"),
            "O centro do comportamento".encode("utf-8"),
            1,
        )

        self.assertNotEqual(codex_shared, mutated)
        with self.assertRaises(AssertionError):
            self._assert_shared_equal(claude_shared, mutated)

    def _document(self, text: bytes, expected_preamble: str) -> tuple[bytes, bytes]:
        preamble, shared, tail = _extract_unique(text, _SHARED_START, _SHARED_END)
        self.assertEqual(_normalize(expected_preamble), _normalize(preamble.decode("utf-8")))

        if expected_preamble == _CLAUDE_PREAMBLE:
            delta_start, delta_end = _CLAUDE_DELTA_START, _CLAUDE_DELTA_END
        else:
            delta_start, delta_end = _CODEX_DELTA_START, _CODEX_DELTA_END
        bridge, delta, suffix = _extract_unique(tail, delta_start, delta_end)
        self.assertEqual("---", _normalize(bridge.decode("utf-8")))
        self.assertEqual("", _normalize(suffix.decode("utf-8")))
        return shared, delta

    def _assert_shared_equal(self, expected: bytes, actual: bytes) -> None:
        self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
