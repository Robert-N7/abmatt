from tests.lib import abmatt_beginner


def test_add_mdl0():
    if not abmatt_beginner('-c add -t mdl0:test_files/course.dae'):
        print('test_add_mdl0 failed!')


def test_remove_mdl0():
    if not abmatt_beginner('-c remove -t mdl0:course'):
        print('test_remove_mdl0 failed!')


if __name__ == '__main__':
    test_add_mdl0()
    test_remove_mdl0()