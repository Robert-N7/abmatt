import sys

from tests.integration.lib import abmatt_desert, IntegTest


class TestTex0(IntegTest):
    def test_add_tex0(self):
        return abmatt_desert('-c add -t tex0:test_files/images/yama.png')

    def test_remove_tex0(self):
        return abmatt_desert('-c remove -t tex0:dst_mariokart')

    def test_resize_dimension_tex0(self):
        return abmatt_desert('-c set -t tex0:dst_mariokart -k dimensions -v 300,300')

    def test_format_tex0(self):
        return abmatt_desert('-c set -t tex0:dst_mariokart -k format -v rgb5a3')


if __name__ == '__main__':
    TestTex0()
