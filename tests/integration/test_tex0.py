from tests.integration.lib import abmatt_desert


def test_add_tex0():
    if not abmatt_desert('-c add -t tex0:test_files/images/yama.png'):
        print('test_add_tex0 failed!')
        return 1


def test_remove_tex0():
    if not abmatt_desert('-c remove -t tex0:dst_mariokart'):
        print('test_remove_tex0 failed!')
        return 1


def test_resize_dimension_tex0():
    if not abmatt_desert('-c set -t tex0:dst_mariokart -k dimensions -v 300,300'):
        print('test_resize_dimension_tex0 failed!')
        return 1


def test_format_tex0():
    if not abmatt_desert('-c set -t tex0:dst_mariokart -k format -v rgb5a3'):
        print('test_format_tex0 failed!')
        return 1


if __name__ == '__main__':
    err_count = 0
    err_count += test_add_tex0()
    err_count += test_remove_tex0()
    err_count += test_resize_dimension_tex0()
    err_count += test_format_tex0()
    print('\t{} tests failed.'.format(err_count))