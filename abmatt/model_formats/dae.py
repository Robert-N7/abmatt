from collada import Collada, DaeBrokenRefError, DaeIncompleteError


def brres_to_dae(brres):
    return None     # todo


# Model sections
# definitions
# Bones
# vertices
# normals
# colors
# uvs
# materials
# shaders
# objects
# texture links


def dae_to_brres(dae_file):
    mesh = Collada(dae_file, ignore=[DaeBrokenRefError, DaeIncompleteError])
    for geo in mesh.geometries:
        triset = geo.primitives[0]

    return None     # todo