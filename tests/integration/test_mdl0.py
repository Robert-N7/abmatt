import sys

from tests.integration.lib import abmatt_beginner, run_tests


class TestMdl0:
    def test_add_mdl0(self):
        return abmatt_beginner('-c add -t mdl0:test_files/beginner_course.dae')

    def test_remove_mdl0(self):
        return abmatt_beginner('-c remove -t mdl0:course')


if __name__ == '__main__':
    run_tests(TestMdl0())
