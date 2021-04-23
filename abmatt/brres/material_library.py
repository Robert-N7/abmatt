import os

from abmatt.autofix import AutoFix
from abmatt.brres import Brres
from abmatt.brres.lib.node import ClipableObserver
from abmatt.brres.mdl0 import Mdl0
from abmatt.brres.mdl0.material.material import Material


class MaterialLibrary(ClipableObserver):
    LIBRARY = None
    LIBRARY_PATH = None

    @staticmethod
    def get():
        if not MaterialLibrary.LIBRARY:
            if MaterialLibrary.LIBRARY_PATH is None:
                return None
            MaterialLibrary.LIBRARY = MaterialLibrary(MaterialLibrary.LIBRARY_PATH)
        return MaterialLibrary.LIBRARY

    def __init__(self, path):
        if self.LIBRARY is not None:
            raise RuntimeError('Already Initialized library!')
        if path is None:
            path = os.path.join(os.getcwd(), 'mat_lib.brres')
            self.LIBRARY_PATH = path
        try:
            self.brres = Brres(path)
        except FileNotFoundError as e:
            AutoFix.get().info(f'Material library "{path}" not found.')
            self.brres = Brres(path, readFile=False)
            self.brres.add_mdl0(Mdl0('lib', self.brres))
        self.on_brres_update()

    def on_node_update(self, node):
        if type(node) != Material:
            self.on_brres_update()

    def on_rename_update(self, node, old_name):
        if type(node) == Material:
            try:
                self.materials[node.name] = self.materials.pop(old_name)
            except KeyError:
                pass

    def is_modified(self):
        return self.brres.is_modified()

    def on_brres_update(self):
        self.materials = {}
        self.brres.register_observer(self)
        for model in self.brres.models:
            model.register_observer(self)
            for material in model.materials:
                material.register_observer(self)
                if material.name not in self.materials:
                    self.materials[material.name] = material
                else:
                    AutoFix.get().warn('Multiple materials named {} in material library'.format(material.name))