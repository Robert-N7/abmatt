from tests.integration.lib import IntegTest, abmatt_beginner, abmatt


class TestConvert(IntegTest):
    def test_to_dae(self):
        return abmatt_beginner('convert to test_files/test.dae')

    def test_from_dae(self):
        return abmatt('convert test_files/3ds_bll.DAE to brres_files/test.brres -o')

    def test_to_obj(self):
        return abmatt_beginner('convert to test_files/test.obj')

    def test_from_obj(self):
        return abmatt('convert test_files/3ds_bll.obj to brres_files/test.brres -o')


if __name__ == '__main__':
    TestConvert()