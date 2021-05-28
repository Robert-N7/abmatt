import re

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDoubleValidator, QColor
from PyQt5.QtWidgets import QLabel, QWidget, QGridLayout, QLineEdit, QCheckBox, QComboBox, \
    QSlider, QVBoxLayout, QFrame, QHBoxLayout, QSpinBox, QTabWidget, QColorDialog

from abmatt.lib.node import ClipableObserver
from abmatt.brres.mdl0 import stage
from abmatt.brres.mdl0.material.layer import Layer
from abmatt.brres.mdl0.material.material import Material
from abmatt.brres.mdl0.shader import Shader
from abmatt.brres.mdl0.stage import Stage
from abmatt.brres.pat0.pat0_material import Pat0MatAnimation
from abmatt.brres.srt0.srt0_animation import SRTMatAnim
from abmatt.gui.color_widget import ColorWidget, ColorWidgetHandler
from abmatt.gui.map_widget import Tex0WidgetGroup, Tex0WidgetSubscriber


class MaterialContainer(QTabWidget, ClipableObserver):
    def __init__(self, material):
        super(MaterialContainer, self).__init__()
        self.mat_editor = MaterialEditor(self, material)
        self.addTab(self.mat_editor, 'Material')
        self.shader_editor = ShaderEditor(self, material)
        self.addTab(self.shader_editor, 'Shader')
        self.material = material
        material.register_observer(self)
        self.setWindowTitle('Material Editor')
        self.resize(800, 800)
        self.show()

    def on_node_update(self, node):
        self.mat_editor.on_node_update(node)
        self.shader_editor.on_node_update(node)

    def set_material(self, material):
        self.material = material
        self.mat_editor.set_material(material)
        self.shader_editor.set_shader(material.shader)

    def __del__(self):
        self.material.unregister(self)


class EditorStyle(QWidget):
    def _init_grid(self):
        self.grid = QGridLayout()
        self.row = 0
        frame = QFrame(self)
        frame.setFrameStyle(QFrame.Panel)
        frame.setLayout(self.grid)
        self.current_layout.addWidget(frame)

    def _add_to_layout(self, col0_label, col1=None):
        label = QLabel(col0_label, self)
        if col1:
            self.grid.addWidget(col1, self.row, 1)
        else:
            self._init_grid()
        self.grid.addWidget(label, self.row, 0)
        self.row += 1

    def _add_checkbox(self, name, fptr):
        widget = QCheckBox(self)
        widget.stateChanged.connect(fptr)
        self._add_to_layout(name, widget)
        return widget

    def _add_combo_box(self, name, opts, fptr):
        widget = QComboBox(self)
        # widget.setS
        widget.addItems(opts)
        widget.currentIndexChanged.connect(fptr)
        self._add_to_layout(name, widget)
        return widget

    def _add_slider(self, name, min, max, fptr):
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(min)
        slider.setMaximum(max)
        slider.valueChanged.connect(fptr)
        self._add_to_layout(name, slider)
        return slider

    def _add_spin_box(self, name, min, max, fptr):
        spin_box = QSpinBox(self)
        spin_box.setMinimum(min)
        spin_box.setMaximum(max)
        spin_box.valueChanged.connect(fptr)
        self._add_to_layout(name, spin_box)
        return spin_box

    def _add_color_widget(self, name):
        c = ColorWidget(handler=self)
        self._add_to_layout(name, c)
        return c

    def _add_layout_pane(self, layout):
        widget = QWidget(self)
        widget.setLayout(layout)
        self.top_layout.addWidget(widget)

    def _add_edit(self, name, fptr, max_width=None, validator=None):
        edit = QLineEdit(self)
        if max_width is not None:
            edit.setMaximumWidth(max_width)
        if validator is not None:
            edit.setValidator(validator)
        edit.textChanged.connect(fptr)
        self._add_to_layout(name, edit)
        return edit


class ShaderEditor(EditorStyle, ClipableObserver, ColorWidgetHandler):

    def __init__(self, parent, material):
        super(ShaderEditor, self).__init__(parent)
        self.shader = self.stage = None
        self.handler = parent
        self.__init_UI()
        self.set_shader(material.shader)
        self.material = material
        self.on_material_update(material)

    def __init_matrix_ui(self):
        widget = QWidget(self)
        layout = QGridLayout()
        self.ind_matrix = []
        fptr = [
            [self.on_ind_matrix_change_00, self.on_ind_matrix_change_01, self.on_ind_matrix_change_02],
            [self.on_ind_matrix_change_10, self.on_ind_matrix_change_11, self.on_ind_matrix_change_12]
        ]
        for i in range(2):
            row = []
            for j in range(3):
                edit = QLineEdit('0', self)
                # edit.setMinimumWidth(50)
                edit.setValidator(QDoubleValidator(-1.0, 1.0, 7))
                edit.textChanged.connect(fptr[i][j])
                row.append(edit)
                layout.addWidget(edit, i, j)
            self.ind_matrix.append(row)
        widget.setLayout(layout)
        self._add_to_layout('Matrix', widget)
        self.ind_matrix_widget = widget

    def __init_UI(self):
        self.top_layout = QHBoxLayout()
        # Shader Pane ------------------------------------------
        self.current_layout = self.shader_pane = QVBoxLayout()
        self._add_to_layout('Shader')
        self.stage_count = self._add_spin_box('Stage Count', 1, 7, self.on_stage_count_change)
        self.colors = colors = []
        for i in range(3):
            colors.append(self._add_color_widget('Color' + str(i)))
        self.const_colors = const_colors = []
        for i in range(4):
            const_colors.append(self._add_color_widget('Const Color' + str(i)))
        # self.color_button = QPushButton('Set Single Color...', self)
        # self.color_button.clicked.connect(self.choose_single_color)
        # self._add_to_layout('Use Single Color:', self.color_button)
        self._add_to_layout('Indirect')
        sels = ['Map' + str(i) for i in range(7)]
        sels.append('None')
        self.ind_map_sel = self._add_combo_box('Map id', sels, self.on_ind_map_sel)
        self.ind_matrix_enable = self._add_checkbox('Matrix Enable', self.on_ind_matrix_enable)
        self.ind_matrix_scale = self._add_spin_box('Matrix Scale', -17, 46, self.on_ind_matrix_scale_change)
        self.__init_matrix_ui()
        self._add_layout_pane(self.shader_pane)

        # Stage Pane --------------------------------------------------
        self.current_layout = self.stage_pane = QVBoxLayout()
        self._add_to_layout('Stage')
        self.stage_id = self._add_combo_box('id', ['Stage 0'], self.on_stage_change)
        self.stage_enable = self._add_checkbox('Enabled', self.on_stage_enable)
        self.stage_map_id = self._add_combo_box('Map', sels, self.on_stage_map_id_change)
        self.stage_raster = self._add_combo_box('Raster', stage.RASTER_COLORS, self.on_stage_raster_change)
        self.stage_ind_matrix_enable = self._add_checkbox('Indirect Matrix', self.on_stage_ind_matrix_change)
        self._add_to_layout('Stage Color')
        self.color_constant = self._add_combo_box('Constant', stage.COLOR_CONSTANTS, self.on_color_constant_change)
        self.color_a = self._add_combo_box('A', stage.COLOR_SELS, self.on_color_a_change)
        self.color_b = self._add_combo_box('B', stage.COLOR_SELS, self.on_color_b_change)
        self.color_c = self._add_combo_box('C', stage.COLOR_SELS, self.on_color_c_change)
        self.color_d = self._add_combo_box('D', stage.COLOR_SELS, self.on_color_d_change)
        self.color_bias = self._add_combo_box('Bias', stage.BIAS, self.on_color_bias_change)
        self.color_oper = self._add_combo_box('Operation', stage.OPER, self.on_color_oper_change)
        self.color_clamp = self._add_checkbox('Clamp', self.on_color_clamp_enable)
        self.color_scale = self._add_combo_box('Scale', stage.SCALE, self.on_color_scale_change)
        self.color_dest = self._add_combo_box('Destination', stage.COLOR_DEST, self.on_color_dest_change)
        self._add_to_layout('Stage Alpha')
        self.alpha_constant = self._add_combo_box('Constant', stage.ALPHA_CONSTANTS, self.on_alpha_constant_change)
        self.alpha_a = self._add_combo_box('A', stage.ALPHA_SELS, self.on_alpha_a_change)
        self.alpha_b = self._add_combo_box('B', stage.ALPHA_SELS, self.on_alpha_b_change)
        self.alpha_c = self._add_combo_box('C', stage.ALPHA_SELS, self.on_alpha_c_change)
        self.alpha_d = self._add_combo_box('D', stage.ALPHA_SELS, self.on_alpha_d_change)
        self.alpha_bias = self._add_combo_box('Bias', stage.BIAS, self.on_alpha_bias_change)
        self.alpha_oper = self._add_combo_box('Operation', stage.OPER, self.on_alpha_oper_change)
        self.alpha_clamp = self._add_checkbox('Clamp', self.on_alpha_clamp_enable)
        self.alpha_scale = self._add_combo_box('Scale', stage.SCALE, self.on_alpha_scale_change)
        self.alpha_dest = self._add_combo_box('Destination', stage.ALPHA_DEST, self.on_alpha_dest_change)
        self._add_layout_pane(self.stage_pane)

        self.setLayout(self.top_layout)

    def choose_single_color(self):
        initial = self.colors[0].color
        color = QColorDialog.getColor(QColor(initial[0], initial[1], initial[2], initial[3]),
                                      options=QColorDialog.ShowAlphaChannel)
        if color.isValid():
            color = ColorWidget.get_rgba255(color)
            self.material.set_single_color(color)

    def __set_stage(self, stage):
        if self.__try_set(self.stage, stage):
            self.stage = stage
            self.__on_stage_update(stage)

    def set_shader(self, shader):
        if self.__try_set(self.shader, shader):
            self.shader = shader
            self.__set_stage(shader.stages[0])
            self.__on_shader_update(shader)

    def __try_set(self, old, new):
        if old is new:
            return False
        if old is not None:
            old.unregister(self)
        if new is not None:
            new.register_observer(self)
        return True

    def on_material_update(self, material):
        for i in range(3):
            self.colors[i].set_color(material.getColor(i))
        for i in range(4):
            self.const_colors[i].set_color(material.getConstantColor(i))
        self.ind_matrix_enable.setChecked(material.isIndMatrixEnabled())
        self.ind_matrix_scale.setValue(material.getIndMatrixScale())
        mat_matrix = material.getIndMatrix()
        ind_matrix = self.ind_matrix
        for i in range(2):
            for j in range(3):
                ind_matrix[i][j].setText(str(mat_matrix[i][j]))

    def __on_shader_update(self, shader):
        self.ind_map_sel.setCurrentIndex(shader.ind_tex_maps[0])
        my_count = self.stage_id.count()
        need_count = len(shader.stages)
        self.stage_count.setValue(need_count)
        if my_count > need_count:
            current_i = self.stage_id.currentIndex()
            for i in range(my_count - 1, need_count - 1, -1):
                self.stage_id.removeItem(i)
            if current_i >= need_count and len(shader.stages):
                self.stage_id.setCurrentIndex(0)
        elif my_count < need_count:
            for i in range(my_count, need_count):
                self.stage_id.addItem('Stage ' + str(i))

    def __on_stage_update(self, stage):
        self.stage_enable.setChecked(stage.is_enabled())
        self.stage_map_id.setCurrentIndex(stage.map_id)
        # need to double check this
        self.stage_raster.setCurrentText(stage.get_str('rastercolor'))
        self.stage_ind_matrix_enable.setChecked(bool(stage.ind_matrix))
        self.color_constant.setCurrentText(stage.get_str('colorconstantselection'))
        self.color_a.setCurrentIndex(stage.get_color_a())
        self.color_b.setCurrentIndex(stage.get_color_b())
        self.color_c.setCurrentIndex(stage.get_color_c())
        self.color_d.setCurrentIndex(stage.get_color_d())
        self.color_bias.setCurrentIndex(stage.get_color_bias())
        self.color_oper.setCurrentIndex(stage.get_color_oper())
        self.color_clamp.setChecked(stage.get_color_clamp())
        self.color_scale.setCurrentIndex(stage.get_color_scale())
        self.color_dest.setCurrentIndex(stage.get_color_dest())
        self.alpha_constant.setCurrentText(stage.get_str('alphaconstantselection'))
        self.alpha_a.setCurrentIndex(stage.get_alpha_a())
        self.alpha_b.setCurrentIndex(stage.get_alpha_b())
        self.alpha_c.setCurrentIndex(stage.get_alpha_c())
        self.alpha_d.setCurrentIndex(stage.get_alpha_d())
        self.alpha_bias.setCurrentIndex(stage.get_alpha_bias())
        self.alpha_oper.setCurrentIndex(stage.get_alpha_oper())
        self.alpha_clamp.setChecked(stage.get_alpha_clamp())
        self.alpha_scale.setCurrentIndex(stage.get_alpha_scale())
        self.alpha_dest.setCurrentIndex(stage.get_alpha_dest())

    def on_node_update(self, node):
        if type(node) == Shader:
            self.__on_shader_update(node)
        elif type(node) == Stage:
            self.__on_stage_update(node)
        elif type(node) == Material:
            if node is not self.material:
                self.material = self.__try_set(self.material, node)
            self.on_material_update(node)

    # COLOR EVENT HANDLERS
    def on_color_change(self, widget, color):
        found = False
        for i in range(3):
            if widget == self.colors[i]:
                self.material.set_color(color, i)
                found = True
                break
        if not found:
            for i in range(4):
                if widget == self.const_colors[i]:
                    self.material.set_constant_color(color, i)
                    break
        return True


    # STAGE EVENT HANDLERS
    def on_stage_count_change(self, val):
        self.shader.set_stage_count(val)

    def on_stage_change(self, i):
        self.__set_stage(self.shader.stages[i])

    def on_stage_enable(self):
        self.stage.set_enabled(self.stage_enable.isChecked())

    def on_stage_map_id_change(self, i):
        self.stage.set_map_id(i)
        self.stage.set_coord_id(i)

    def on_stage_raster_change(self, i):
        self.stage.set_str('rastercolor', self.stage_raster.currentText())

    def on_color_constant_change(self, i):
        self.stage.set_str('colorconstantselection', self.color_constant.currentText())

    def on_color_a_change(self, i):
        self.stage.set_color_a(i)

    def on_color_b_change(self, i):
        self.stage.set_color_b(i)

    def on_color_c_change(self, i):
        self.stage.set_color_c(i)

    def on_color_d_change(self, i):
        self.stage.set_color_d(i)

    def on_color_bias_change(self, i):
        self.stage.set_color_bias(i)

    def on_color_oper_change(self, i):
        self.stage.set_color_oper(i)

    def on_color_clamp_enable(self):
        self.stage.set_color_clamp(self.color_clamp.isChecked())

    def on_color_scale_change(self, i):
        self.stage.set_color_scale(i)

    def on_color_dest_change(self, i):
        self.stage.set_color_dest(i)

    def on_alpha_constant_change(self, i):
        self.stage.set_str('alphaconstantselection', self.alpha_constant.currentText())

    def on_alpha_a_change(self, i):
        self.stage.set_alpha_a(i)

    def on_alpha_b_change(self, i):
        self.stage.set_alpha_b(i)

    def on_alpha_c_change(self, i):
        self.stage.set_alpha_c(i)

    def on_alpha_d_change(self, i):
        self.stage.set_alpha_d(i)

    def on_alpha_bias_change(self, i):
        self.stage.set_alpha_bias(i)

    def on_alpha_oper_change(self, i):
        self.stage.set_alpha_oper(i)

    def on_alpha_clamp_enable(self):
        self.stage.set_alpha_clamp(self.alpha_clamp.isChecked())

    def on_alpha_scale_change(self, i):
        self.stage.set_alpha_scale(i)

    def on_alpha_dest_change(self, i):
        self.stage.set_alpha_dest(i)

    # ------------------------------------------------------
    # INDIRECT
    def on_stage_ind_matrix_change(self):
        enable = self.stage_ind_matrix_enable.isChecked()
        if enable:
            self.stage.set_ind_bias(stage.IND_BIAS_STU)
            self.stage.set_ind_matrix(stage.IND_MATRIX_0)
        else:
            self.stage.set_ind_bias(stage.IND_BIAS_NONE)
            self.stage.set_ind_matrix(stage.IND_MATRIX_NONE)

    def on_ind_matrix_enable(self):
        if self.material.isIndMatrixEnabled() != self.ind_matrix_enable.isChecked():
            self.material.set_ind_matrix_enable(enable=self.ind_matrix_enable.isChecked())

    def on_ind_map_sel(self, i):
        if self.shader.get_ind_map() != i:
            self.shader.set_ind_map(i)
            self.shader.set_ind_coord(i)

    def on_ind_matrix_scale_change(self):
        if self.material.getIndMatrixScale() != self.ind_matrix_scale.value():
            self.material.set_ind_matrix_scale(self.ind_matrix_scale.value())

    def on_ind_matrix_change_00(self):
        self.on_ind_matrix_change(0, 0)

    def on_ind_matrix_change_01(self):
        self.on_ind_matrix_change(0, 1)

    def on_ind_matrix_change_02(self):
        self.on_ind_matrix_change(0, 2)

    def on_ind_matrix_change_10(self):
        self.on_ind_matrix_change(1, 0)

    def on_ind_matrix_change_11(self):
        self.on_ind_matrix_change(1, 1)

    def on_ind_matrix_change_12(self):
        self.on_ind_matrix_change(1, 2)

    def on_ind_matrix_change(self, row, col):
        widget = self.ind_matrix[row][col]
        text = widget.text()
        if not re.match('-?[0-1](\.\d+)?', text):
            widget.setText('0')
        else:
            self.material.set_ind_matrix_single(float(text), row, col)


class MaterialEditor(EditorStyle, ClipableObserver, ColorWidgetHandler, Tex0WidgetSubscriber):
    def __init__(self, parent, material):
        super().__init__(parent)
        self.handler = parent
        self.layer = self.material = None
        self.anim = self.last_anim = None
        self.__init_UI(material)
        self.set_material(material)

    def __init_UI(self, material):
        self.top_layout = QHBoxLayout()
        # MATERIAL PANE ----------------------------------------
        self.current_layout = self.mat_pane = QVBoxLayout()
        self._init_grid()
        # self.layout = QGridLayout()
        self.name = QLabel(material.name)
        self._add_to_layout('Material', self.name)
        self.cull_combo = self._add_combo_box('Cull', Material.CULL_STRINGS, self.on_cull_change)
        self.animation = self._add_combo_box('Animation', ['None', 'SRT0', 'PAT0'], self.on_animation_change)

        self._add_to_layout('Alpha Function')
        self.ref0 = self._add_slider('Ref0', 0, 255, self.on_ref0_change)
        self.comp0 = self._add_combo_box('Comp0', Material.COMP_STRINGS, self.on_comp0_change)
        self.logic = self._add_combo_box('Logic', Material.LOGIC_STRINGS, self.on_logic_change)
        self.ref1 = self._add_slider('Ref1', 0, 255, self.on_ref1_change)
        self.comp1 = self._add_combo_box('Comp1', Material.COMP_STRINGS, self.on_comp1_change)
        self.const_alpha_enabled = self._add_checkbox('Constant Alpha Enable', self.on_const_alpha_enable)
        self.const_alpha = self._add_slider('Constant Alpha', 0, 255, self.on_const_alpha_change)

        self._add_to_layout('Blend')
        self.is_xlu = self._add_checkbox('Xlu', self.on_xlu_change)
        self.blend_enabled = self._add_checkbox('Blend Enable', self.on_blend_change)
        self.blend_logic_enable = self._add_checkbox('Logic Enable', self.on_blend_logic_enable)
        self.blend_logic = self._add_combo_box('Logic', Material.BLLOGIC_STRINGS, self.on_blend_logic_change)
        self.blend_source = self._add_combo_box('Source', Material.BLFACTOR_STRINGS, self.on_blend_source_change)
        self.blend_dest = self._add_combo_box('Dest', Material.BLFACTOR_STRINGS, self.on_blend_dest_change)

        self._add_to_layout('LightChannel')
        self.vertex_color = self._add_checkbox('Vertex Color', self.on_vertex_color_change)
        self.material_color = self._add_color_widget('Material Color')
        self.ambient_color = self._add_color_widget('Ambient Color')

        self._add_to_layout('Z-Mode')
        self.compare_before_texture = self._add_checkbox('Compare Before Texture', self.comp_before_tex_enable)
        self.depth_test = self._add_checkbox('Depth Test', self.depth_test_enable)
        self.depth_update = self._add_checkbox('Depth Update', self.depth_update_enable)
        self._add_layout_pane(self.mat_pane)

        # MAP PANE ------------------------------------------------------------
        self.current_layout = self.map_pane = QVBoxLayout()
        self.maps = Tex0WidgetGroup(self)
        self._add_to_layout('Maps')
        self._add_to_layout('Tex0:', self.maps)
        self.uwrap = self._add_combo_box('U-Wrap', Layer.WRAP, self.on_uwrap_change)
        self.vwrap = self._add_combo_box('V-Wrap', Layer.WRAP, self.on_vwrap_change)
        self.minfilter = self._add_combo_box('Minfilter', Layer.FILTER, self.on_minfilter_change)
        self.magfilter = self._add_combo_box('Magfilter', Layer.FILTER, self.on_magfilter_change)
        self.lod_bias = self._add_edit('Lod Bias', self.on_lod_bias_change, 30, QDoubleValidator())
        self.max_anisotrophy = self._add_combo_box('Anisotrophy', Layer.ANISOTROPHY, self.on_anisotrophy_change)
        self.clamp_bias = self._add_checkbox('Clamp Bias', self.on_clamp_enable)
        self.interpolate = self._add_checkbox('Texel Interpolate', self.on_interpolate_enable)
        self.mapmode = self._add_combo_box('Map Mode', Layer.MAPMODE, self.on_mapmode_change)
        self.coordinates = self._add_combo_box('Coordinates', Layer.COORDINATES, self.on_coordinate_change)
        self.projection = self._add_combo_box('Projection', Layer.PROJECTION, self.on_projection_change)
        self.inputform = self._add_combo_box('Input Form', Layer.INPUTFORM, self.on_inputform_change)
        self.normalize = self._add_checkbox('Normalize', self.on_normalize_enable)
        self.scale_widget = QWidget(self)
        layout = QHBoxLayout()
        self.scale_x = QLineEdit(self)
        self.scale_x.textChanged.connect(self.on_scale_x_change)
        self.scale_y = QLineEdit(self)
        self.scale_y.textChanged.connect(self.on_scale_y_change)
        layout.addWidget(self.scale_x)
        layout.addWidget(self.scale_y)
        self.scale_widget.setLayout(layout)
        self._add_to_layout('Scale', self.scale_widget)
        self.rotation = self._add_edit('Rotation', self.on_rotation_change, 30, QDoubleValidator())
        self.tr_widget = QWidget(self)
        layout = QHBoxLayout()
        self.tr_x = QLineEdit(self)
        self.tr_x.textChanged.connect(self.on_translation_x_change)
        self.tr_y = QLineEdit(self)
        self.tr_y.textChanged.connect(self.on_translation_y_change)
        layout.addWidget(self.tr_x)
        layout.addWidget(self.tr_y)
        self.tr_widget.setLayout(layout)
        self._add_to_layout('Translation', self.tr_widget)
        self._add_layout_pane(self.map_pane)

        self.setLayout(self.top_layout)

    def __try_set(self, old, new):
        if old is new:
            return False
        if old is not None:
            old.unregister(self)
        if new is not None:
            new.register_observer(self)
        return True

    def set_material(self, material):
        # if self.__try_set(self.material, material):
        self.material = material
        self.__on_material_update(material)
        if len(material.layers):
            self.__set_layer(material.layers[0])
        else:
            self.__set_layer(None)
        self.__set_anim(material.get_animation())

    def __set_anim(self, anim):
        if self.__try_set(self.anim, anim):
            self.anim = anim

    def __set_layer(self, layer):
        if self.__try_set(self.layer, layer):
            self.layer = layer
            self.__on_layer_update(layer)

    # ------------------------------------------------------
    # EVENT HANDLERS
    # ------------------------------------------------------
    # Interface updates
    def __on_material_update(self, material):
        self.name.setText(material.name)
        self.cull_combo.setCurrentIndex(material.cullmode)
        self.__on_anim_update()
        self.ref0.setValue(material.ref0)
        self.comp0.setCurrentIndex(material.comp0)
        self.logic.setCurrentIndex(material.logic)
        self.ref1.setValue(material.ref1)
        self.comp1.setCurrentIndex(material.comp1)
        self.const_alpha_enabled.setChecked(material.constant_alpha_enabled)
        self.const_alpha.setValue(material.constant_alpha)
        self.is_xlu.setChecked(material.xlu)
        self.blend_enabled.setChecked(material.blend_enabled)
        self.blend_logic_enable.setChecked(material.blend_logic_enabled)
        self.blend_logic.setCurrentIndex(material.blend_logic)
        self.blend_source.setCurrentIndex(material.blend_source)
        self.blend_dest.setCurrentIndex(material.blend_dest)
        self.vertex_color.setChecked(material.is_vertex_color_enabled())
        self.material_color.set_color(material.get_material_color())
        self.ambient_color.set_color(material.get_ambient_color())
        self.compare_before_texture.setChecked(material.compareBeforeTexture)
        self.depth_test.setChecked(material.depth_test)
        self.depth_update.setChecked(material.depth_update)
        found = False
        self.maps.set_tex0s(material.get_tex0s())
        self.maps.set_brres(material.getBrres())
        for x in material.layers:
            if self.layer is x:
                found = True
                break
        if not found:
            if len(material.layers):
                self.__set_layer(material.layers[0])
        # if self.shader is not material.shader:
        #     self.__set_shader(material.shader)

    def __on_anim_update(self):
        if self.material.pat0:
            self.animation.setCurrentIndex(2)
        elif self.material.srt0:
            self.animation.setCurrentIndex(1)
        else:
            self.animation.setCurrentIndex(0)

    def __on_layer_update(self, layer):
        self.uwrap.setCurrentIndex(layer.uwrap)
        self.vwrap.setCurrentIndex(layer.vwrap)
        self.minfilter.setCurrentIndex(layer.minfilter)
        self.magfilter.setCurrentIndex(layer.magfilter)
        self.lod_bias.setText(str(layer.lod_bias))
        self.max_anisotrophy.setCurrentIndex(layer.max_anisotrophy)
        self.clamp_bias.setChecked(layer.clamp_bias)
        self.interpolate.setChecked(layer.texel_interpolate)
        self.mapmode.setCurrentIndex(layer.map_mode)
        self.coordinates.setCurrentIndex(layer.coordinates)
        self.projection.setCurrentIndex(layer.projection)
        self.inputform.setCurrentIndex(layer.inputform)
        self.normalize.setChecked(layer.normalize)
        self.scale_x.setText(str(layer.scale[0]))
        self.scale_y.setText(str(layer.scale[1]))
        self.rotation.setText(str(layer.rotation))
        self.tr_x.setText(str(layer.translation[0]))
        self.tr_y.setText(str(layer.translation[1]))

    def on_node_update(self, node):
        if type(node) == Material:
            self.__on_material_update(node)
        elif type(node) == Layer:
            self.__on_layer_update(node)

    def on_child_update(self, child):
        pass

    def on_rename_update(self, node, old_name):
        if type(node) == Layer:
            self.maps.set_tex0s(self.material.get_tex0s())

    def on_color_change(self, widget, color):
        if widget == self.material_color:
            self.material.set_material_color(color)
        elif widget == self.ambient_color:
            self.material.set_ambient_color(color)
        return True

    # gui updates
    def on_animation_change(self, i):
        if i == 0:
            if self.anim:
                self.last_anim = self.anim
                self.anim = None
                return self.material.remove_animation()
        elif i == 1:
            if type(self.anim) != SRTMatAnim:
                if self.anim:
                    self.material.remove_animation()
                t = self.last_anim
                self.last_anim = self.anim
                self.anim = self.material.add_srt0()
                if type(t) == type(self.anim):
                    self.anim.paste(t)
        elif i == 2:
            if type(self.anim) != Pat0MatAnimation:
                if self.anim:
                    self.material.remove_animation()
                t = self.last_anim
                self.last_anim = self.anim
                self.anim = self.material.add_pat0()
                if type(t) == type(self.anim):
                    self.anim.paste(self.last_anim)

    def on_vertex_color_change(self):
        if self.material.is_vertex_color_enabled() != self.vertex_color.isChecked():
            self.material.enable_vertex_color(self.vertex_color.isChecked())

    def on_blend_dest_change(self, i):
        if self.material.blend_dest != i:
            self.material.set_blend_dest_str(self.blend_dest.currentText())

    def on_blend_source_change(self, i):
        if self.material.blend_source != i:
            self.material.set_blend_src_str(self.blend_source.currentText())

    def on_blend_logic_change(self, i):
        if self.material.blend_logic != i:
            self.material.set_blend_logic_str(self.blend_logic.currentText())

    def on_blend_logic_enable(self):
        if self.material.blend_logic_enabled != self.blend_logic_enable.isChecked():
            self.material.enable_blend_logic(self.blend_logic_enable.isChecked())

    def on_blend_change(self):
        if self.material.blend_enabled != self.blend_enabled.isChecked():
            self.material.enable_blend(self.blend_enabled.isChecked())

    def on_xlu_change(self):
        if self.material.is_xlu() != self.is_xlu.isChecked():
            self.material.enable_xlu(self.is_xlu.isChecked())

    def on_comp1_change(self, i):
        if self.material.comp1 != i:
            self.material.set_comp1_str(self.comp1.currentText())

    def on_ref1_change(self, i):
        if self.material.ref1 != i:
            self.material.set_ref1_str(str(i))

    def on_logic_change(self, i):
        if self.material.logic != i:
            self.material.set_logic(self.logic.currentText())

    def on_comp0_change(self, i):
        if self.material.comp0 != i:
            self.material.set_comp0_str(self.comp0.currentText())

    def on_ref0_change(self, i):
        if self.material.ref0 != i:
            self.material.set_ref0_str(str(i))

    def on_cull_change(self, i):
        if self.material.cullmode != i:
            self.material.set_cull_mode_str(self.cull_combo.currentText())

    def on_const_alpha_change(self, i):
        self.material.set_constant_alpha(i)

    def on_const_alpha_enable(self):
        enable = self.const_alpha_enabled.isChecked()
        if self.material.constant_alpha_enabled != enable:
            if enable:
                self.material.enable_constant_alpha()
                self.material.set_constant_alpha(120)
            else:
                self.material.enable_constant_alpha(False)

    def comp_before_tex_enable(self):
        if self.material.compareBeforeTexture != self.compare_before_texture.isChecked():
            self.material.set_compare_before_tex_str()

    def depth_test_enable(self):
        if self.material.depth_test != self.depth_test.isChecked():
            self.material.set_enable_depth_test(self.depth_test.isChecked())

    def depth_update_enable(self):
        if self.material.depth_update != self.depth_update.isChecked():
            self.material.set_enable_depth_update(self.depth_update.isChecked())

    # ----------------------------------------------
    #   LAYER functions
    # ----------------------------------------------
    def on_map_change(self, tex0, index):
        layer = self.material.layers[index]
        if self.layer is not layer:
            self.__set_layer(layer)

    def on_map_add(self, tex0, index):
        self.material.add_layer(tex0.name)

    def on_map_remove(self, tex0, index):
        self.material.remove_layer_i(index)

    def on_map_replace(self, tex0, index):
        self.layer.rename(tex0.name)

    def on_uwrap_change(self, i):
        self.layer.set_u_wrap_str(self.uwrap.currentText())

    def on_vwrap_change(self, i):
        self.layer.set_v_wrap_str(self.vwrap.currentText())

    def on_minfilter_change(self, i):
        self.layer.set_minfilter_str(self.minfilter.currentText())

    def on_magfilter_change(self, i):
        self.layer.set_magfilter_str(self.magfilter.currentText())

    def on_lod_bias_change(self):
        self.layer.set_lod_bias_str(self.lod_bias.text())

    def on_mapmode_change(self, i):
        self.layer.set_map_mode_str(self.mapmode.currentText())

    def on_coordinate_change(self, i):
        self.layer.set_coordinate_str(self.coordinates.currentText())

    def on_projection_change(self, i):
        self.layer.set_projection_str(self.projection.currentText())

    def on_inputform_change(self, i):
        self.layer.set_input_form_str(self.inputform.currentText())

    def on_normalize_enable(self):
        self.layer.normalize = self.normalize.isChecked()

    def on_scale_x_change(self):
        try:
            self.layer.set_x_scale(self.scale_x.text())
        except ValueError:
            self.scale_x.setText(str(self.layer.scale[0]))

    def on_scale_y_change(self):
        try:
            self.layer.set_y_scale(self.scale_y.text())
        except ValueError:
            self.scale_y.setText(str(self.layer.scale[1]))

    def on_rotation_change(self):
        try:
            self.layer.set_rotation(float(self.rotation.text()))
        except ValueError:
            self.rotation.setText('0.0')

    def on_translation_x_change(self):
        try:
            self.layer.set_x_translation(self.tr_x.text())
        except ValueError:
            self.tr_x.setText(str(self.layer.translation[0]))

    def on_translation_y_change(self):
        try:
            self.layer.set_y_translation(self.tr_y.text())
        except ValueError:
            self.tr_y.setText(str(self.layer.translation[1]))

    def on_anisotrophy_change(self, i):
        self.layer.set_anisotrophy_str(self.max_anisotrophy.currentText())

    def on_clamp_enable(self):
        self.layer.set_clamp_bias_str(str(self.clamp_bias.isChecked()).lower())

    def on_interpolate_enable(self):
        self.layer.set_texel_interpolate_str(str(self.interpolate.isChecked()).lower())

    # ------------------------------------------------
    # End EVENT HANDLERS
    # ------------------------------------------------
