from copy import deepcopy

from pyqtgraph import opengl as gl


class GLPolygonWidget(gl.GLViewWidget):
    def __init__(self, polygon):
        super().__init__()
        self.polygon = polygon
        decoded = deepcopy(self.polygon.get_decoded())
        points = decoded.vertices.points / 1000
        points[:, [1, 2]] = points[:, [2, 1]]
        points[:, 1] *= -1
        mesh = gl.GLMeshItem(meshdata=gl.MeshData(
            points,
            decoded.vertices.face_indices
        ))
        g = gl.GLGridItem()
        self.addItem(g)
        self.addItem(mesh)
        self.setWindowTitle('Polygon Viewer')
