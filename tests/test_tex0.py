from tests.lib import abmatt, abmatt_desert


def test_add_tex0():
    if not abmatt_desert('-c add -t tex0:test_files/images/yama.png'):
        print('test_add_tex0 failed!')


def test_remove_tex0():
    if not abmatt_desert('-c remove -t tex0:dst_mariokart'):
        print('test_remove_tex0 failed!')


def test_resize_dimension_tex0():
    if not abmatt_desert('-c set -t tex0:dst_mariokart -k dimensions -v 300,300'):
        print('test_resize_dimension_tex0 failed!')


def test_format_tex0():
    if not abmatt_desert('-c set -t tex0:dst_mariokart -k format -v rgb5a3'):
        print('test_format_tex0 failed!')


if __name__ == '__main__':
    test_add_tex0()
    test_remove_tex0()
    test_resize_dimension_tex0()
    test_format_tex0()