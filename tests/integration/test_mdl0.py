from tests.integration.lib import abmatt_beginner


def test_add_mdl0():
    if not abmatt_beginner('-c add -t mdl0:test_files/course.dae'):
        print('test_add_mdl0 failed!')
        return 1


def test_remove_mdl0():
    if not abmatt_beginner('-c remove -t mdl0:course'):
        print('test_remove_mdl0 failed!')
        return 1


if __name__ == '__main__':
    err_count = 0
    err_count += test_add_mdl0()
    err_count += test_remove_mdl0()
    print('\t{} tests failed.'.format(err_count))