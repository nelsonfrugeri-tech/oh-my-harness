"""The repository names no machine path: one resolver reads flag > env > XDG config file."""
import os
from pathlib import Path
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

    def test_values_must_be_literal_absolute_or_home_paths(self):
        invalid = ('"/q"', '$HOME/kb', 'rel/dir', '/tmp/$HOME/kb', '/tmp/"quoted"/kb', "/tmp/'q'/kb",
                   '~root/kb', '~omh-no-such-user/kb', '~')
        for value in invalid:
            with self.subTest(layer='config', value=value):
                self._config(f'OMH_KB_ROOT={value}\n')
                result = self._cli('OMH_KB_ROOT')
                self.assertEqual((2, '', 'invalid path: OMH_KB_ROOT\n'),
                                 (result.returncode, result.stdout, result.stderr))
            with self.subTest(layer='env and flag', value=value):
                with self.assertRaisesRegex(ValueError, 'invalid path: OMH_KB_ROOT'):
                    self._resolve('OMH_KB_ROOT', OMH_KB_ROOT=value)
                with self.assertRaisesRegex(ValueError, 'invalid path: OMH_KB_ROOT'):
                    self._resolve('OMH_KB_ROOT', value)

    def test_tilde_inside_an_absolute_path_is_literal(self):
        icloud = '/Volumes/data/Mobile Documents/iCloud~md~obsidian/Documents/kb'
        self.assertEqual(Path(icloud), self._resolve('OMH_KB_ROOT', OMH_KB_ROOT=icloud))

    def test_last_assignment_wins_so_an_appended_fix_takes_effect(self):
        self._config('OMH_KB_ROOT=relative\nOMH_KB_ROOT=/fixed\n')
        self.assertEqual(Path('/fixed'), self._resolve('OMH_KB_ROOT'))

    def test_unreadable_config_is_reported_not_treated_as_missing(self):
        (self.config / 'omh/config').mkdir()
        result = self._cli('OMH_KB_ROOT')
        self.assertEqual(2, result.returncode)
        self.assertIn('unreadable config:', result.stderr)

    def test_bom_and_empty_assignments_do_not_hide_a_value(self):
        for text, expected in (('\ufeffOMH_KB_ROOT=/first\n', '/first'),
                               ('OMH_KB_ROOT=\nOMH_KB_ROOT=/second\n', '/second')):
            with self.subTest(config=text):
                self._config(text)
                self.assertEqual(Path(expected), self._resolve('OMH_KB_ROOT'))

    def test_values_are_stripped_in_every_layer(self):
        self.assertEqual(Path('/a'), self._resolve('OMH_KB_ROOT', OMH_KB_ROOT='  /a  '))
        with self.assertRaisesRegex(MissingPath, 'missing path: OMH_KB_ROOT'):
            self._resolve('OMH_KB_ROOT', OMH_KB_ROOT='   ')

    def test_filesystem_root_home_and_shell_syntax_are_rejected(self):
        for value in ('/', '~/', '/a # note'):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, 'invalid path: OMH_KB_ROOT'):
                    self._resolve('OMH_KB_ROOT', OMH_KB_ROOT=value)
        self._config('export OMH_KB_ROOT=/a\n')
        with self.assertRaisesRegex(ValueError, 'invalid line'):
            self._resolve('OMH_KB_ROOT')

    def test_an_empty_home_never_yields_a_relative_path_or_config(self):
        with self.assertRaisesRegex(ValueError, 'invalid path: OMH_KB_ROOT'):
            self._resolve('OMH_KB_ROOT', OMH_KB_ROOT='~/kb', HOME='')
        del self.env['XDG_CONFIG_HOME']
        with self.assertRaisesRegex(ValueError, 'unusable home'):
            self._resolve('OMH_KB_ROOT', HOME='')

    def test_a_dangling_config_symlink_is_reported(self):
        (self.config / 'omh/config').symlink_to(self.config / 'omh/nowhere')
        with self.assertRaisesRegex(ValueError, 'unreadable config'):
            self._resolve('OMH_KB_ROOT')


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
