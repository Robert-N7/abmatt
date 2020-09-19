import sys

from tests.integration.lib import abmatt_beginner, abmatt, run_tests


class TestConvert:
    def test_convert_dae_to_brres(self):
        return abmatt('convert test_files/beginner_course.dae to brres_files/test.brres')

    def test_convert_brres_to_dae(self):
        return abmatt_beginner('convert to test_files/test.dae')


if __name__ == '__main__':
    run_tests(TestConvert())
