from tests.lib import abmatt, abmatt_desert


def test_add_tex0():
    if not abmatt_desert('-c add -t tex0:test_files/images/yama.png'):
        print('test_add_tex0 failed!')


def test_remove_tex0():
    if not abmatt_desert('-c remove -t tex0:dst_mariokart'):
        print('test_remove_tex0 failed!')


if __name__ == '__main__':
    test_add_tex0()
    test_remove_tex0()
