from pathlib import Path
import subprocess
import tempfile
import unittest


_ROOT = Path(__file__).resolve().parents[2]


class KnowledgeBaseTaxonomyContractTests(unittest.TestCase):
    def _read(self, relative_path: str) -> str:
        return _ROOT.joinpath(relative_path).read_text(encoding="utf-8")

    def test_write_routes_project_knowledge_through_a_topic(self) -> None:
        contract = self._read("core/skills/kb-write/SKILL.md")

        self.assertIn("scope -> domain -> topic -> concept", contract)
        self.assertIn(
            "work/projects/<project>/<topic>/<YYYY-MM-DD>--<short-slug>.md",
            contract,
        )
        self.assertIn(
            "`type` does not select the directory",
            " ".join(contract.split()),
        )
        self.assertNotIn("Pasta nasce na **segunda** nota", contract)

    def test_project_resolution_asks_only_when_identity_is_unknown(self) -> None:
        contract = " ".join(self._read("core/skills/kb-write/SKILL.md").split())

        self.assertIn("explicit project name", contract)
        self.assertIn("`remote_url`", contract)
        self.assertIn("observed Git root", contract)
        self.assertIn("never search for another slug", contract)
        self.assertIn("stable Git identity is unavailable", contract)
        self.assertIn("ask once for the canonical name and slug", contract)
        self.assertIn("collision blocks writing", contract)
        self.assertIn("existing artifact without sufficient identity", contract)
        self.assertIn("fails closed", contract)
        self.assertIn("`explorer` and `kb-session`", contract)

    def test_topic_path_and_short_filename_are_stable(self) -> None:
        contract = self._read("core/skills/kb-write/SKILL.md")
        normalized = " ".join(contract.split())

        self.assertIn("2-6 substantive terms", contract)
        self.assertIn(
            "never move or rename a note during a normal write",
            normalized,
        )
        self.assertIn("Concept ID", contract)
        self.assertNotIn("<slug-do-titulo>", contract)

    def test_topic_is_indexed_and_available_to_retrieval(self) -> None:
        write = self._read("core/skills/kb-write/SKILL.md")
        infra = self._read("core/skills/kb-infra/SKILL.md")
        retrieval = self._read("core/skills/kb-retrieval/SKILL.md")

        self.assertIn("topic: <stable-subject>", write)
        keyword_indexes = infra.split("Create keyword indexes for", 1)[1].split(
            "with `PayloadSchemaType.KEYWORD`", 1
        )[0]
        note_payload = next(
            line for line in infra.splitlines() if line.startswith('| Note point (`kind: "note"`)')
        )
        self.assertIn("`topic`", keyword_indexes)
        self.assertIn("`topic`", note_payload)
        self.assertIn("`topic`", retrieval)
        self.assertIn("topic folder", retrieval)

    def test_agents_enforce_the_same_topic_first_routing(self) -> None:
        paths = (
            "harness/claude/agents/tools/knowledge-base.md",
            "harness/codex/agents/knowledge-base.toml",
        )

        for path in paths:
            with self.subTest(path=path):
                content = self._read(path)
                normalized = " ".join(content.split()).lower()
                self.assertIn("canonical project/context to topic to concept", normalized)
                self.assertIn("block domain collisions", normalized)
                self.assertIn("instead of inventing alternate slugs", normalized)
                self.assertIn("writing, retrieval, and session work", normalized)
                self.assertIn("owning skills", normalized)

    def test_readme_documents_topic_first_layout(self) -> None:
        readme = self._read("README.md")

        self.assertIn("<topic>/", readme)
        self.assertIn("<date>--<short-slug>.md", readme)
        self.assertIn("topic-first", readme)
        self.assertNotIn("one folder per entity type", readme)

    def test_exact_lookup_precedes_semantic_and_disambiguates(self) -> None:
        retrieval = self._read("core/skills/kb-retrieval/SKILL.md")
        exact = retrieval.index("## Resolve exact entities and addresses first")
        semantic = retrieval.index("## Run the retrieval ladder")

        self.assertLess(exact, semantic)
        self.assertIn("A unique match answers directly", retrieval)
        self.assertIn("Multiple matches require disambiguation", retrieval)
        self.assertIn("Zero matches", retrieval)
        self.assertIn("never select the first match", retrieval)

    def test_addressable_knowledge_survives_write_index_and_retrieval(self) -> None:
        write = self._read("core/skills/kb-write/SKILL.md")
        infra = self._read("core/skills/kb-infra/SKILL.md")
        retrieval = self._read("core/skills/kb-retrieval/SKILL.md")
        session = self._read("core/skills/kb-session/SKILL.md")
        template = self._read("core/skills/kb-write/references/note-template.md")

        source_fields = ("entities", "aliases", "entity_refs", "references", "temporal_refs")
        derived_fields = ("entity_kinds", "entity_keys", "reference_targets", "temporal_values")
        for field in source_fields:
            with self.subTest(layer="write", field=field):
                self.assertIn(f"`{field}`", write)
            with self.subTest(layer="session", field=field):
                self.assertIn(f'"{field}"', session)
        for field in derived_fields:
            with self.subTest(layer="infra", field=field):
                self.assertIn(f"`{field}`", infra)
            with self.subTest(layer="retrieval", field=field):
                self.assertIn(f"`{field}`", retrieval)

        mappings = (
            "`entity_kinds` from `entity_refs[*].kind`",
            "`entity_keys` from `entity_refs[*].name`",
            "`reference_targets` from safe, present `references[*].target`",
            "`temporal_values` from `temporal_refs[*].value`",
        )
        infra_flat = " ".join(infra.split())
        for mapping in mappings:
            with self.subTest(mapping=mapping):
                self.assertIn(mapping, infra_flat)
        self.assertIn("NFKC + Unicode casefold + whitespace collapse", infra_flat)
        self.assertIn("timezone-aware RFC 3339", infra_flat)
        self.assertIn("Only timezone-aware RFC 3339 instants become indexed", " ".join(write.split()))
        self.assertIn("values remain in `temporal_values` with `occurred_at: null`", write)
        self.assertIn("Live upsert and full reindex use this same mapping", infra_flat)
        self.assertIn("material address", template)

    def test_project_identity_lives_in_a_project_note(self) -> None:
        write = " ".join(self._read("core/skills/kb-write/SKILL.md").split())
        retrieval = " ".join(self._read("core/skills/kb-retrieval/SKILL.md").split())

        self.assertIn("`knowledge_type: project`", write)
        self.assertIn(
            "`work/projects/<project>/identity/<YYYY-MM-DD>--project-identity.md`",
            write,
        )
        for field in ("name", "aliases", "repository_path", "remote_url", "default_branch"):
            with self.subTest(field=field):
                self.assertIn(f"`{field}`", write)
        self.assertIn("never rewrite it in place", write)
        self.assertIn("`knowledge_type: project` note under", retrieval)
        self.assertIn("`work/projects/*/identity/` first", retrieval)

    def test_no_kb_surface_still_depends_on_the_context_snapshot(self) -> None:
        surfaces = (
            "core/skills/kb-retrieval/SKILL.md",
            "core/skills/kb-infra/SKILL.md",
            "core/skills/kb-session/SKILL.md",
            "core/skills/explorer/SKILL.md",
        )
        for surface in surfaces:
            with self.subTest(surface=surface):
                contract = self._read(surface)
                self.assertNotIn("context.md", contract)
                self.assertNotIn("context-load", contract)
                self.assertNotIn("last_hash", contract)

        writer = self._read("core/skills/kb-write/SKILL.md")
        self.assertNotIn("context-load", writer)
        self.assertNotIn("last_hash", writer)
        self.assertEqual(1, writer.count("context.md"))
        self.assertIn("context.md", self._migration_section(writer))

    def _migration_section(self, writer: str) -> str:
        heading = "## Migrate legacy project identity once"
        self.assertIn(heading, writer)
        return writer.split(heading, 1)[1].split("\n## ", 1)[0]

    def test_legacy_project_identity_migrates_once_and_fails_closed(self) -> None:
        writer = self._read("core/skills/kb-write/SKILL.md")
        migration = " ".join(self._migration_section(writer).split())

        self.assertIn("no active `knowledge_type: project` note", migration)
        self.assertIn("`~/knowledge-base/work/projects/<project>/context.md`", migration)
        self.assertIn("Parse only its first YAML frontmatter block with `yaml.safe_load`", migration)
        self.assertIn("never execute the file", migration)
        self.assertIn("missing, non-mapping, or malformed value is dropped, never guessed", migration)
        for field in ("name", "aliases", "repository_path", "remote_url", "default_branch"):
            with self.subTest(field=field):
                self.assertIn(f"`{field}`", migration)

        guard = (
            "HTTP(S) userinfo",
            "query string",
            "fragment",
            "signed URL",
            "ambiguous parsing",
            "SSH/SCP transport username",
            "`remote_url: null`",
            "`redacted`",
            "never echoed",
        )
        for rule in guard:
            with self.subTest(rule=rule):
                self.assertIn(rule, migration)

        self.assertIn("never edits, moves, or deletes it", migration)
        self.assertIn("an existing active project note means no migration", migration)
        self.assertIn("writes nothing and reports `skipped`", migration)
        self.assertIn("indexing pending", migration)
        self.assertIn("writes no note, leaves the legacy file untouched", migration)
        self.assertIn("reports the migration as failed", migration)

    def test_retrieval_and_agent_request_the_one_shot_migration(self) -> None:
        retrieval = " ".join(self._read("core/skills/kb-retrieval/SKILL.md").split())
        self.assertIn("one-shot legacy migration", retrieval)

        for path in (
            "harness/claude/agents/tools/knowledge-base.md",
            "harness/codex/agents/knowledge-base.toml",
        ):
            with self.subTest(path=path):
                agent = " ".join(self._read(path).split())
                self.assertIn("one-shot legacy migration defined by `kb-write`", agent)
                self.assertIn("preserving the legacy file", agent)

    def test_remote_values_fail_closed_across_project_note_write_and_retrieval(self) -> None:
        boundaries = {
            "explorer": self._read("core/skills/explorer/SKILL.md"),
            "writer": self._read("core/skills/kb-write/SKILL.md"),
            "retrieval": self._read("core/skills/kb-retrieval/SKILL.md"),
        }
        required_policy = (
            "HTTP(S) userinfo",
            "query string",
            "fragment",
            "signed URL",
            "ambiguous parsing",
            "SSH/SCP transport username",
            "`remote_url: null`",
        )

        for boundary, contract in boundaries.items():
            normalized = " ".join(contract.split())
            for rule in required_policy:
                with self.subTest(boundary=boundary, rule=rule):
                    self.assertIn(rule, normalized)
        self.assertIn("Never emit the raw remote", boundaries["explorer"])
        self.assertIn("Never echo a rejected value", boundaries["writer"])
        self.assertIn(
            "never echo the sensitive target",
            " ".join(boundaries["retrieval"].split()),
        )
        self.assertIn("Revalidate legacy stored remotes", boundaries["retrieval"])
        self.assertIn(
            "a rejected project remote persists as `remote_url: null`",
            " ".join(boundaries["writer"].split()),
        )
        self.assertIn(
            "Fictitious example: `https://user:token@example.com/repo.git?signature=secret`",
            boundaries["explorer"],
        )
        self.assertIn("`git@example.com:team/repo.git`", boundaries["explorer"])

    def test_legacy_entity_metadata_remains_reindexable(self) -> None:
        infra = " ".join(self._read("core/skills/kb-infra/SKILL.md").split())
        session = " ".join(self._read("core/skills/kb-session/SKILL.md").split())

        self.assertIn("Project missing multi-value fields as `[]`", infra)
        self.assertIn("nullable scalar fields as `null`", infra)
        self.assertIn("Reindexing never modifies source JSON", infra)
        self.assertIn("full reindex", infra)
        self.assertIn("Omission in the current update never deletes", session)
        self.assertIn("derive the flat lookup fields again", session)
        merge_keys = (
            "`entity_refs` by kind plus normalized canonical name",
            "`references` by kind plus normalized target plus entity",
            "`temporal_refs` by value plus timezone plus meaning",
        )
        for merge_key in merge_keys:
            with self.subTest(merge_key=merge_key):
                self.assertIn(merge_key, session)

    def test_disk_timeline_is_recursive_and_excludes_reserved_files(self) -> None:
        retrieval = self._read("core/skills/kb-retrieval/SKILL.md")
        command = next(
            line.strip().strip("`.")
            for line in retrieval.splitlines()
            if line.strip().startswith("`find ~/knowledge-base/<domain>")
        )

        with tempfile.TemporaryDirectory() as temporary:
            domain = Path(temporary)
            old_note = domain / "z-topic/2025-01-01--old-note.md"
            new_note = domain / "a-topic/subtopic/2026-09-01--new-note.md"
            reserved = domain / "zz-topic/index.md"
            for path in (old_note, new_note, reserved):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch()

            result = subprocess.run(
                command.replace("~/knowledge-base/<domain>", str(domain)),
                shell=True,
                check=True,
                capture_output=True,
                text=True,
            )

        self.assertEqual([str(new_note), str(old_note)], result.stdout.splitlines())

    def test_disk_type_filter_parses_only_yaml_frontmatter(self) -> None:
        retrieval = self._read("core/skills/kb-retrieval/SKILL.md")
        normalized = " ".join(retrieval.split())

        self.assertIn("yaml.safe_load", retrieval)
        self.assertIn("only the first YAML frontmatter block", normalized)
        self.assertIn('lines.index("---", 1)', retrieval)
        self.assertIn("~/knowledge-base/<domain> type system", retrieval)
        self.assertNotIn('text.split("---", 2)', retrieval)
        self.assertNotIn('grep -rl "^type:', retrieval)
