"""Every consumer honors the resolver contract: missing (exit 3) vs invalid (exit 2)."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import unittest

from test_paths import RESOLVER, ROOT, SCRIPTS, Sandbox

GUARD = ROOT / 'core/hooks/kb-write-guard.sh'


class PathConsumersTest(Sandbox):
    def _kb(self, *args):
        return subprocess.run([sys.executable, str(SCRIPTS / 'kb.py'), *args, '--json'], capture_output=True,
                              text=True, env=self.env, timeout=30)

    def test_kb_cli_reports_missing_and_invalid_paths_apart_from_degraded(self):
        missing = self._kb('check', '--root', self.tmp.name)
        self.assertEqual((5, {'status': 'MissingPath', 'reason': 'missing path: OMH_KB_RUNTIME'}),
                         (missing.returncode, json.loads(missing.stdout)))
        self.assertEqual('missing path: OMH_KB_RUNTIME\n', missing.stderr)
        self._config('OMH_KB_ROOT=relative\n')
        invalid = self._kb('check')
        self.assertEqual((6, 'InvalidPath'), (invalid.returncode, json.loads(invalid.stdout)['status']))

    def test_hooks_fail_open_silently_when_kb_root_is_missing(self):
        for hook, payload in (('kb-pointer.sh', {'cwd': str(ROOT)}),
                              ('kb-write-guard.sh', {'tool_name': 'Write', 'cwd': str(ROOT),
                                                     'tool_input': {'file_path': '/any/x.md'}})):
            with self.subTest(hook=hook):
                result = subprocess.run(['bash', str(ROOT / 'core/hooks' / hook)], input=json.dumps(payload),
                                        capture_output=True, text=True, env=self.env, timeout=5)
                self.assertEqual((0, '', ''), (result.returncode, result.stdout, result.stderr))

    def test_write_guard_reads_kb_root_from_config_file(self):
        bundle = Path(self.tmp.name) / 'kb'
        bundle.mkdir()
        self._config(f'OMH_KB_ROOT={bundle}\n')
        payload = {'tool_name': 'Write', 'cwd': str(ROOT), 'tool_input': {'file_path': str(bundle / 'x.md')}}
        result = subprocess.run(['bash', str(ROOT / 'core/hooks/kb-write-guard.sh')], input=json.dumps(payload),
                                capture_output=True, text=True, env=self.env, timeout=5)
        self.assertEqual('deny', json.loads(result.stdout)['hookSpecificOutput']['permissionDecision'])

    def _guard(self, target, **extra):
        payload = {'tool_name': 'Write', 'cwd': str(ROOT), 'tool_input': {'file_path': str(target)}}
        result = subprocess.run(['bash', str(ROOT / 'core/hooks/kb-write-guard.sh')], input=json.dumps(payload),
                                capture_output=True, text=True, env={**self.env, **extra}, timeout=10)
        return json.loads(result.stdout)['hookSpecificOutput']['permissionDecision'] if result.stdout else None

    def _guard_result(self, target):
        payload = {'tool_name': 'Write', 'cwd': str(ROOT), 'tool_input': {'file_path': str(target)}}
        return subprocess.run(['bash', str(GUARD)], input=json.dumps(payload), capture_output=True, text=True,
                              env=self.env, timeout=10)

    def test_broken_config_denies_markdown_only_and_never_its_own_fix(self):
        self._config('OMH_KB_ROOT=relative\n')
        denied = json.loads(self._guard_result('/any/x.md').stdout)['hookSpecificOutput']
        self.assertEqual('deny', denied['permissionDecision'])
        self.assertIn('invalid path: OMH_KB_ROOT', denied['permissionDecisionReason'])
        self.assertIsNone(self._guard('/any/x.py'))
        self.assertIsNone(self._guard(self.config / 'omh/config'))

    def test_pointer_warns_once_about_a_broken_config(self):
        self._config('OMH_KB_ROOT=relative\n')
        result = subprocess.run(['bash', str(ROOT / 'core/hooks/kb-pointer.sh')],
                                input=json.dumps({'cwd': str(ROOT)}), capture_output=True, text=True,
                                env=self.env, timeout=5)
        self.assertEqual(0, result.returncode)
        self.assertEqual(1, len(result.stdout.splitlines()))
        self.assertIn('invalid path: OMH_KB_ROOT', result.stdout)

    @unittest.skipUnless(Path('/usr/bin/python3').exists(), 'no system python3 to pin')
    def test_hooks_run_under_the_oldest_system_python(self):
        bundle = Path(self.tmp.name) / 'kb'
        bundle.mkdir()
        self._config(f'OMH_KB_ROOT={bundle}\n')
        pinned = Path(self.tmp.name) / 'bin'
        pinned.mkdir()
        (pinned / 'python3').symlink_to('/usr/bin/python3')
        path = f"{pinned}:{self.env['PATH']}"
        self.assertEqual('deny', self._guard(bundle / 'x.md', PATH=path))
        result = subprocess.run([str(pinned / 'python3'), str(RESOLVER), 'OMH_KB_ROOT'], capture_output=True,
                                text=True, env=self.env, timeout=5)
        self.assertEqual((0, f'{bundle}\n'), (result.returncode, result.stdout))

    def test_kb_infra_bootstrap_keeps_the_resolver_exit_code(self):
        skill = (ROOT / 'core/skills/kb-infra/SKILL.md').read_text()
        line = next(line for line in skill.splitlines() if line.startswith('KB_RUNTIME="$(python3'))
        script = line.replace('<kb-write-dir>', str(ROOT / 'core/skills/kb-write'))
        for text, expected in ((None, 3), ('OMH_KB_RUNTIME=relative/path\n', 2)):
            with self.subTest(config=text):
                if text:
                    self._config(text)
                result = subprocess.run(['bash', '-c', script], capture_output=True, text=True,
                                        env=self.env, timeout=5)
                self.assertEqual(expected, result.returncode, result.stderr)

    @unittest.skipIf(shutil.which('docker') is None, 'docker unavailable')
    def test_compose_volume_comes_from_kb_runtime(self):
        command = ['docker', 'compose', '-f', str(ROOT / 'core/skills/kb-infra/docker-compose.yml'),
                   'config', '--format', 'json']
        self.env['HOME'] = os.environ['HOME']  # the compose CLI plugin lives under the real ~/.docker
        rendered = subprocess.run(command, capture_output=True, text=True, check=True,
                                  env={**self.env, 'OMH_KB_RUNTIME': '/srv/omh'})
        volume = json.loads(rendered.stdout)['services']['qdrant']['volumes'][0]
        self.assertEqual('/srv/omh/qdrant', volume['source'])
        missing = subprocess.run(command, capture_output=True, text=True, env=self.env)
        self.assertNotEqual(0, missing.returncode)
        self.assertIn('missing path: OMH_KB_RUNTIME', missing.stderr)

    def test_skill_commands_resolve_every_path_they_use(self):
        # Each Bash call starts a fresh shell: a command line using $KB_RUNTIME or $KB_ROOT must set it.
        for skill in ('kb-infra', 'kb-retrieval', 'kb-write'):
            text = (ROOT / 'core/skills' / skill / 'SKILL.md').read_text()
            for block in re.findall(r'```bash\n(.*?)```', text, re.S):
                for variable in ('KB_RUNTIME', 'KB_ROOT', 'KB_VENV'):
                    if f'${variable}' in block or f'${{{variable}}}' in block:
                        with self.subTest(skill=skill, variable=variable, block=block[:60]):
                            self.assertIn(f'{variable}=', block)


if __name__ == '__main__':
    unittest.main()
