from abmatt.command import Command
from tests.lib import AbmattTest


class TestCommand(AbmattTest):
    def test_load(self):
        self.assertTrue(Command('load {}'.format(self._get_test_fname('presets.txt'))).run_cmd())
        self.assertTrue(Command.PRESETS.get('load_preset'))
