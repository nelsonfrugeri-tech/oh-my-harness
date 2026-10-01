from __future__ import annotations

import sys
import unittest
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'core/skills/kb-write/scripts'))
from kb.entities.extraction import extract
from kb.entities.kinds import EntityKind
from kb.entities.model import CandidateKind
from kb.entities.proof import prove
from kb.entities.secrets import find_secrets
from kb.entities.tables import parse_tables


def declared(**values):
    return {kind.value: values.get(kind.value, []) for kind in EntityKind}


def entity_table(value='c6-bank', kind='company'):
    return ('| Entidade | Tipo | Quem/o que é | Relação | Período | Fonte |\n'
            '| --- | --- | --- | --- | --- | --- |\n'
            f'| {value} | {kind} | Banco | Contratante | Atual | Sessão |')


def figure_table(value='12500.00', unit='BRL'):
    return ('| Valor | Unidade | O que mede | Quando | Fonte |\n'
            '| --- | --- | --- | --- | --- |\n'
            f'| {value} | {unit} | Proposta | 2026-10-01T12:00:00Z | Sessão |')


class EntityTests(unittest.TestCase):
    def test_extract_literal_addresses_dates_and_money(self):
        text = 'Veja https://example.org/a e /tmp/a.md em 2026-10-01 por R$ 12.500,00.'
        values = {(item.kind, item.value) for item in extract(text)}
        self.assertIn((EntityKind.URLS, 'https://example.org/a'), values)
        self.assertIn((EntityKind.PATHS, '/tmp/a.md'), values)
        self.assertIn((CandidateKind.DATE, '2026-10-01'), values)
        self.assertIn((CandidateKind.FIGURE, '12500 BRL'), values)

    def test_undeclared_items_are_all_reported(self):
        report = prove(declared(), 'https://example.org /tmp/a 2026-10-01 R$ 12.500,00', '')
        self.assertEqual(4, len([i for i in report.issues if i.code == 'undeclared']))

    def test_company_must_appear_in_prose(self):
        report = prove(declared(companies=['c6-bank']), 'Outra empresa.', 'C6 Bank')
        self.assertIn('absent-from-prose', [i.code for i in report.issues])

    def test_names_are_normalized_without_substring_matches(self):
        self.assertTrue(prove(declared(companies=['c6-bank']), 'O C6 Bank contratou.', 'c6-bank').ok)
        self.assertFalse(prove(declared(people=['ana']), 'A banana.', 'Ana').ok)

    def test_new_entities_need_transcript_but_inherited_do_not(self):
        values = declared(companies=['c6-bank'])
        self.assertFalse(prove(values, 'C6 Bank', '').ok)
        self.assertTrue(prove(values, 'C6 Bank', '', values).ok)

    def test_absent_transcript_is_explicit(self):
        self.assertFalse(prove(declared(), '', None).transcript_available)

    def test_all_thirteen_keys_are_required_and_unknown_rejected(self):
        self.assertFalse(prove({}, '', '').ok)
        values = declared()
        values['banks'] = []
        self.assertFalse(prove(values, '', '').ok)

    def test_tables_parse_typed_values_and_singular_kind(self):
        tables = parse_tables({'Entities': entity_table(), 'Figures': figure_table(unit='BRL/mês')})
        self.assertEqual((), tables.issues)
        self.assertEqual(EntityKind.COMPANIES, tables.entities[0].kind)
        self.assertEqual(Decimal('12500'), tables.figures[0].value)
        self.assertEqual('BRL/mês', tables.figures[0].unit)

    def test_table_parity_is_bidirectional(self):
        tables = parse_tables({'Entities': entity_table()})
        self.assertFalse(prove(declared(), '', '', tables=tables).ok)
        self.assertFalse(prove(declared(companies=['c6-bank']), 'C6 Bank', 'C6 Bank',
                               tables=parse_tables({})).ok)

    def test_figures_match_localized_numbers_in_transcript(self):
        tables = parse_tables({'Figures': figure_table()})
        for number in ('12.500,00', '12500.00', '12,5 mil'):
            with self.subTest(number=number):
                self.assertTrue(prove(declared(), 'Proposta de R$ 12.500,00.',
                                      f'Proposta R$ {number}', tables=tables).ok)
        self.assertFalse(prove(declared(), 'R$ 12.500,00', 'R$ 999', tables=tables).ok)

    def test_currency_must_be_iso_and_dates_require_timezone(self):
        self.assertTrue(parse_tables({'Figures': figure_table(unit='ZZZ')}).issues)
        self.assertTrue(parse_tables({'Figures': figure_table().replace('T12:00:00Z', '')}).issues)

    def test_table_headers_and_empty_evidence_are_rejected(self):
        tables = parse_tables({'Timeline': '| Quando | Quem | O quê | Como | Evidência |\n'
                               '|---|---|---|---|---|\n|2026-10-01T12:00:00Z|Ana|Fez|CLI||'})
        self.assertTrue(tables.issues)
        self.assertTrue(parse_tables({'Entities': '| wrong |\n|---|\n|x|'}).issues)

    def test_secrets_are_detected_without_echoing_values(self):
        for secret in ('https://host/a?token=abc123', 'https://user:pass@host/a',
                       'senha: abc123', '4111 1111 1111 1111', '529.982.247-25',
                       '-----BEGIN PRIVATE KEY-----'):
            with self.subTest(secret=secret):
                findings = find_secrets(secret)
                self.assertTrue(findings)
                self.assertNotIn(secret, repr(findings))

    def test_literal_paths_and_urls_are_not_slugged_or_prefix_matched(self):
        values = declared(urls=['https://example.org/A'], paths=['/tmp/A.md'])
        self.assertTrue(prove(values, 'https://example.org/A /tmp/A.md',
                              'https://example.org/A /tmp/A.md').ok)
        self.assertFalse(prove(values, 'https://example.org/AB /tmp/A.md',
                               'https://example.org/A /tmp/A.md').ok)

    def test_noncanonical_slugs_are_rejected(self):
        self.assertFalse(prove(declared(companies=['C6 Bank']), 'C6 Bank', 'C6 Bank').ok)

    def test_malformed_entity_values_return_violations(self):
        for values in ({'companies': 'oops'}, {'companies': [None]},
                       {'companies': ['x', 'x']}):
            self.assertFalse(prove(declared(**values), '', '').ok)

    def test_figure_proof_requires_compatible_currency_context(self):
        tables = parse_tables({'Figures': figure_table()})
        for transcript in ('A proposta foi de 12500 USD.', 'Valor 12,5 mil'):
            with self.subTest(transcript=transcript):
                self.assertFalse(prove(declared(), 'R$ 12.500,00', transcript, tables=tables).ok)
        for number in ('12.500,00', '12500.00', '12,5 mil'):
            with self.subTest(number=number):
                self.assertTrue(prove(declared(), 'R$ 12.500,00', f'Proposta R$ {number}',
                                      tables=tables).ok)

    def test_date_timestamp_must_not_match_a_different_time(self):
        table = '| Data | O que é | Quem | Status | Fonte |\n|---|---|---|---|---|\n'
        table += '|2026-10-01T12:00:00Z|Prazo|Ana|Aberto|Sessão|'
        tables = parse_tables({'Dates': table})
        report = prove(declared(), '2026-10-01T13:00:00Z', '2026-10-01T12:00:00Z', tables=tables)
        self.assertFalse(report.ok)

    def test_transcript_inheritance_still_requires_prose(self):
        values = declared(companies=['c6-bank'])
        self.assertFalse(prove(values, 'Outra empresa', '', values).ok)

    def test_sensitive_table_cells_are_rejected(self):
        tables = parse_tables({'Entities': entity_table().replace('Banco', 'senha: abc123')})
        self.assertTrue(tables.issues)

    def test_unknown_currency_and_free_noncurrency_units(self):
        self.assertFalse(parse_tables({'Figures': figure_table(unit='ano')}).issues)
        self.assertTrue(parse_tables({'Figures': figure_table(unit='ZZZ/mês')}).issues)

    def test_declared_entity_only_in_its_table_is_not_narrative_evidence(self):
        table = entity_table()
        body = '## Facts\n\nA proposta foi recebida.\n\n## Entities\n\n' + table
        report = prove(declared(companies=['c6-bank']), body, 'C6 Bank',
                       tables=parse_tables({'Entities': table}))
        self.assertIn('absent-from-prose', [issue.code for issue in report.issues])
        self.assertTrue(prove(declared(companies=['c6-bank']),
                              body.replace('A proposta', 'O C6 Bank enviou a proposta'),
                              'C6 Bank', tables=parse_tables({'Entities': table})).ok)

    def test_declared_dates_and_figures_only_in_tables_do_not_prove_narrative(self):
        date = '| Data | O que é | Quem | Status | Fonte |\n|---|---|---|---|---|\n'
        date += '|2026-10-01T12:00:00Z|Prazo|Ana|Aberto|Sessão|'
        sections = {'Dates': date, 'Figures': figure_table()}
        body = '## Facts\n\nRecebemos uma proposta.\n\n' + '\n\n'.join(
            f'## {name}\n\n{text}' for name, text in sections.items())
        report = prove(declared(), body, '2026-10-01T12:00:00Z R$ 12500',
                       tables=parse_tables(sections))
        self.assertEqual(2, len([i for i in report.issues if i.code == 'absent-from-prose']))

    def test_sources_addresses_still_require_declaration(self):
        report = prove(declared(), '## Sources\n\nhttps://example.org/source /tmp/source.md', '')
        self.assertEqual(2, len([i for i in report.issues if i.code == 'undeclared']))

    def test_inherited_figures_skip_current_transcript_but_changes_do_not(self):
        tables = parse_tables({'Figures': figure_table()})
        self.assertTrue(prove(declared(), 'R$ 12500', '', tables=tables,
                              inherited_tables=tables).ok)
        updated = parse_tables({'Figures': figure_table(value='13000')})
        self.assertFalse(prove(declared(), 'R$ 13000', '', tables=updated,
                               inherited_tables=tables).ok)
        contextual = parse_tables({'Figures': figure_table().replace('Proposta', 'Contrato')})
        self.assertFalse(prove(declared(), 'R$ 12500', '', tables=contextual,
                               inherited_tables=tables).ok)

    def test_inherited_dates_require_narrative_and_new_dates_require_transcript(self):
        date = '| Data | O que é | Quem | Status | Fonte |\n|---|---|---|---|---|\n'
        date += '|2026-10-01T12:00:00Z|Prazo|Ana|Aberto|Sessão|'
        tables = parse_tables({'Dates': date})
        self.assertTrue(prove(declared(), 'Prazo em 2026-10-01.', '', tables=tables,
                              inherited_tables=tables).ok)
        self.assertFalse(prove(declared(), '## Dates\n\n' + date, '', tables=tables,
                               inherited_tables=tables).ok)
        updated = parse_tables({'Dates': date.replace('2026-10-01', '2026-10-02')})
        self.assertFalse(prove(declared(), 'Prazo em 2026-10-02.', '', tables=updated,
                               inherited_tables=tables).ok)

    def test_sources_after_declarations_remain_visible_to_extraction(self):
        body = '## Entities\n\n' + entity_table() + '\n\n## Sources\n\nhttps://example.org/source'
        report = prove(declared(companies=['c6-bank']), body, 'C6 Bank')
        self.assertTrue(any(i.code == 'undeclared' and i.message == 'https://example.org/source'
                            for i in report.issues))

    def test_code_example_alone_is_not_narrative_presence(self):
        report = prove(declared(companies=['c6-bank']), '```text\nC6 Bank\n```', 'C6 Bank')
        self.assertIn('absent-from-prose', [issue.code for issue in report.issues])

    def test_technical_acronyms_are_not_treated_as_currency(self):
        self.assertEqual((), extract('ISO 4217 e RFC 3339'))

    def test_ordinary_numbers_and_urls_are_not_secrets(self):
        self.assertEqual((), find_secrets('https://example.org R$ 12.500,00 2026-10-01'))


if __name__ == '__main__':
    unittest.main()
