import os


def abmatt(params):
    os.chdir('../..')
    result = os.system('".\\abmatt\\__main__.py" ' + params)
    os.chdir('tests/integration')
    return not result


def abmatt_desert(params):
    return abmatt(params + ' -b brres_files/desert_course.brres -d brres_files/test.brres -o')


def abmatt_beginner(params):
    return abmatt(params + ' -b brres_files/beginner_course.brres -d brres_files/test.brres -o')


def abmatt_water(params):
    return abmatt(params + ' -b brres_files/water_course.brres -d brres_files/test.brres -o')