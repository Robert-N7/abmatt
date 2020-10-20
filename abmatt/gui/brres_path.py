import os

from brres import Brres


class NotABrresError(Exception):
    pass


def get_materials_by_url(url):
    brres, mdl0, material = BrresPath(path=url).trace_path(Brres.OPEN_FILES)
    if material is None:
        if mdl0 is None:
            if not len(brres.models):
                return []
            materials = []
            for x in brres.models:
                materials.extend(x.materials)
        else:
            materials = mdl0.materials
    else:
        materials = [material]
    return materials


class BrresPath:
    """
    Custom path to inside a brres, only for mdl0 and materials
    Does not use folders
    (path_to_brres/mdl0/material)
    """

    def __init__(self, path=None, material=None):
        self.brres = self.mdl0 = self.material = self.path = None
        if path:
            self.path = path
        elif material:
            self.material = material.name
            mdl0 = material.parent
            self.mdl0 = mdl0.name
            self.brres = os.path.abspath(mdl0.parent.name)

    def get_path(self):
        if self.path is None:
            self.path = os.path.join(os.path.join(self.brres, self.mdl0), self.material)
        return self.path

    def split_path(self):
        if not self.brres:
            path = self.path
            stack = []
            # figure out what the brres path is by testing if it exists
            while path:
                if os.path.exists(path):
                    ext = os.path.splitext(os.path.basename(path))[1]
                    if ext != '.brres':
                        if ext != '' or os.path.isdir(path):
                            raise NotABrresError(path)
                    self.brres = path
                    break
                path, test = os.path.split(path)
                stack.append(test)
            if len(stack):
                self.mdl0 = stack.pop(-1)
                if len(stack):
                    self.material = stack.pop(-1)
        return self.brres, self.mdl0, self.material

    def trace_path(self, brres_path=None, model_name=None, material_name=None, return_new_brres_flag=False):
        brres = mdl0 = material = None
        if brres_path is None:
            brres_path, model_name, material_name = self.split_path()
        if not brres_path:  # No such file
            return brres, mdl0, material
        brres = Brres.get_brres(brres_path)
        new_brres = False
        if not brres:
            brres = Brres(brres_path, readFile=False)
            new_brres = True
        if brres:
            if model_name:
                mdl0 = brres.getModel(model_name)
                if mdl0:
                    if material_name:
                        material = mdl0.get_material_by_name(material_name)
        return brres, mdl0, material if not return_new_brres_flag else brres, mdl0, material, new_brres
