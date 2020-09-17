import sys

from tests.integration.lib import abmatt_beginner, run_tests


class TestMdl0:
    def test_add_mdl0(self):
        if not abmatt_beginner('-c add -t mdl0:test_files/beginner_course.dae'):
            print('test_add_mdl0 failed!')
            return 1
        return 0


    def test_remove_mdl0(self):
        if not abmatt_beginner('-c remove -t mdl0:course'):
            print('test_remove_mdl0 failed!')
            return 1
        return 0


if __name__ == '__main__':
    sys.exit(run_tests(TestMdl0()))