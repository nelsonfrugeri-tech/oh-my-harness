from dataclasses import fields

from .model import Entities
from .sections import COMMON_OPTIONAL, CONDITIONAL_SECTIONS, SCHEMAS
from .vocabulary import NoteType


FRONTMATTER = '''---
id: "<UUID v4>"
type: {type}
title: "<10–70 caracteres>"
description: "<120–300 caracteres em pt-BR>"
summary: "<600–1500 caracteres em pt-BR>"
tags: ["<kebab-case>"]
status: pending
version: 1
created_at: "<RFC 3339 UTC>"
updated_at: "<RFC 3339 UTC>"
generated:
  harness: "<claude-code|codex|cursor>"
  model: null
  session_id: "<ID real da sessão>"
  cwd: "<caminho absoluto>"
  machine_id: "<UUID da identidade estável>"
'''
TABLES = {
    'Entities': '| Entidade | Tipo | Quem/o que é | Relação | Período | Fonte |\n| --- | --- | --- | --- | --- | --- |',
    'Dates': '| Data | O que é | Quem | Status | Fonte |\n| --- | --- | --- | --- | --- |',
    'Figures': '| Valor | Unidade | O que mede | Quando | Fonte |\n| --- | --- | --- | --- | --- |',
    'Timeline': '| Quando | Quem | O quê | Como | Evidência |\n| --- | --- | --- | --- | --- |',
}
REFERENCE_INTRO = '''# Note template

Generated from `kb.note` schema. Regenerate with `render_reference()`; do not edit by hand.
All narrative text is written in pt-BR. The placeholders below must be replaced before validation.
Required headings keep their relative order. Optional headings may appear anywhere.
Remove unused optional sections and unused conditional tables; do not leave empty sections.
Entities, Dates and Figures are required when the corresponding declarations or facts exist.
Timeline rows require RFC 3339 timestamps and nonempty evidence; Dates and Figures also use
RFC 3339 timestamps. Currency units use ISO 4217. Entity types are the 13 frontmatter keys.

New notes start pending. Only approval publishes them. A domain identity note is a reference at
`<scope>/<domain>/identity/identity.md`; a code project also supplies `repository_path`,
`remote_url` and `default_branch` (`remote_url: null` when unavailable or redacted). Frozen versions add `superseded_at` and
`superseded_reason` (30–500 characters), and use status superseded. Neither set of fields belongs
to the ordinary new-note skeleton. Tags contain 1–6 distinct kebab-case values.
'''


def render_template(note_type: NoteType) -> str:
    schema = SCHEMAS[note_type]
    lines = [FRONTMATTER.format(type=note_type.value).rstrip()]
    if note_type is NoteType.EVENT:
        lines.append('occurred_at: "<RFC 3339 com fuso>"')
    lines.extend(('parent: null', 'related: []', 'children: []', 'entities:'))
    lines.extend('  ' + field.name + ': []' for field in fields(Entities))
    lines.append('---')
    for heading in schema.required + schema.optional + COMMON_OPTIONAL + CONDITIONAL_SECTIONS:
        annotation = 'Obrigatória' if heading in schema.required else 'Opcional'
        if heading in CONDITIONAL_SECTIONS:
            annotation = 'Condicional: inclua quando houver dados correspondentes'
        content = TABLES.get(heading, '<Descreva os fatos em pt-BR com contexto, papel e relação.>')
        lines.append(f'\n## {heading}\n\n<!-- {annotation} -->\n\n{content}')
    return '\n'.join(lines) + '\n'


def render_reference() -> str:
    sections = [REFERENCE_INTRO.rstrip()]
    for note_type in NoteType:
        sections.append(f'## {note_type.value}\n\n```markdown\n{render_template(note_type)}```')
    return '\n\n'.join(sections) + '\n'
