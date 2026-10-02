"""The repository names no machine path: one resolver reads flag > env > XDG config file."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'core/skills/kb-write/scripts'
RESOLVER = SCRIPTS / 'kb/adapters/paths.py'
sys.path.insert(0, str(SCRIPTS))

from kb.adapters.paths import MissingPath, resolve  # noqa: E402

LITERALS = r'~/knowledge-base|HOME/knowledge-base|\.local/share/omh-kb|projects/sites'
EXCLUDED = (':!tests', ':!installers/codex/lib/permissions.py', ':!harness/codex/README.md')
NAMES = ('OMH_KB_ROOT', 'OMH_KB_RUNTIME', 'OMH_SITES_ROOT')


class Sandbox(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name) / 'home'
        self.config = Path(self.tmp.name) / 'xdg'
        (self.config / 'omh').mkdir(parents=True)
        self.env = {key: value for key, value in os.environ.items()
                    if key not in NAMES and key != 'XDG_CONFIG_HOME'}
        self.env.update(HOME=str(self.home), XDG_CONFIG_HOME=str(self.config))

    def _config(self, text, base=None):
        path = (base or self.config) / 'omh/config'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def _resolve(self, name, flag=None, **extra):
        with patch.dict(os.environ, {**self.env, **extra}, clear=True):
            return resolve(name, flag)

    def _cli(self, name, **extra):
        return subprocess.run([sys.executable, str(RESOLVER), name], capture_output=True, text=True,
                              env={**self.env, **extra}, timeout=5)


class PathResolutionTest(Sandbox):
    def test_flag_overrides_env_which_overrides_config_file(self):
        self._config('OMH_KB_ROOT=/b\n')
        self.assertEqual(Path('/f'), self._resolve('OMH_KB_ROOT', '/f', OMH_KB_ROOT='/a'))
        self.assertEqual(Path('/a'), self._resolve('OMH_KB_ROOT', OMH_KB_ROOT='/a'))
        self.assertEqual(Path('/b'), self._resolve('OMH_KB_ROOT'))

    def test_xdg_config_home_is_honored_and_tilde_expanded(self):
        self._config('OMH_SITES_ROOT=~/p\n')
        result = self._cli('OMH_SITES_ROOT')
        self.assertEqual((0, f'{self.home}/p\n'), (result.returncode, result.stdout))

    def test_home_config_is_the_fallback_without_xdg_config_home(self):
        self._config('OMH_SITES_ROOT=/from-home\n', base=self.home / '.config')
        del self.env['XDG_CONFIG_HOME']
        self.assertEqual(Path('/from-home'), self._resolve('OMH_SITES_ROOT'))

    def test_missing_value_exits_3_without_default(self):
        for text in (None, 'OMH_KB_ROOT=/elsewhere\n'):
            with self.subTest(config=text):
                if text:
                    self._config(text)
                result = self._cli('OMH_SITES_ROOT')
                self.assertEqual((3, '', 'missing path: OMH_SITES_ROOT\n'),
                                 (result.returncode, result.stdout, result.stderr))
        with self.assertRaisesRegex(MissingPath, 'missing path: OMH_KB_RUNTIME'):
            self._resolve('OMH_KB_RUNTIME')

    def test_comments_and_blank_lines_are_ignored(self):
        self._config('# OMH_KB_ROOT=/commented\n\n  OMH_KB_ROOT = /kept  \n')
        self.assertEqual(Path('/kept'), self._resolve('OMH_KB_ROOT'))

    def test_unknown_name_is_rejected(self):
        self._config('HOME_DIR=/x\n')
        with self.assertRaisesRegex(ValueError, 'unknown path: HOME_DIR'):
            self._resolve('HOME_DIR')
        self.assertEqual(2, self._cli('OMH_PLANS_DIR').returncode)


class PathConsumersTest(Sandbox):
    def test_kb_cli_reports_missing_runtime(self):
        result = subprocess.run([sys.executable, str(SCRIPTS / 'kb.py'), 'check', '--root', self.tmp.name,
                                 '--json'], capture_output=True, text=True, env=self.env, timeout=30)
        self.assertEqual(4, result.returncode, result.stderr)
        self.assertIn('missing path: OMH_KB_RUNTIME', json.loads(result.stdout)['reason'])

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


class NoMachinePathTest(unittest.TestCase):
    def test_tracked_files_hold_no_machine_path_literal(self):
        result = subprocess.run(['git', 'grep', '-nE', LITERALS, '--', '.', *EXCLUDED],
                                cwd=ROOT, capture_output=True, text=True)
        self.assertEqual('', result.stdout)

    def test_code_readers_use_the_shared_resolver(self):
        result = subprocess.run(['git', 'grep', '-n', "os.environ.get('OMH_", '--', 'core'],
                                cwd=ROOT, capture_output=True, text=True)
        self.assertNotIn('OMH_KB_ROOT', result.stdout)
        self.assertNotIn('OMH_KB_RUNTIME', result.stdout)


if __name__ == '__main__':
    unittest.main()
