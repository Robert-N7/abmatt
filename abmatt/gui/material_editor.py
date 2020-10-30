import re

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QWindow, QDoubleValidator
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QGridLayout, QLineEdit, QCheckBox, QGroupBox, QComboBox, \
    QSlider, QVBoxLayout, QFrame, QHBoxLayout, QDialog, QMessageBox, QSpinBox

from abmatt.brres.lib.node import ClipableObserver
from abmatt.brres.mdl0 import stage
from abmatt.brres.mdl0.material.layer import Layer
from abmatt.brres.mdl0.material.material import Material
from abmatt.brres.mdl0.shader import Shader
from abmatt.brres.pat0.pat0_material import Pat0MatAnimation
from abmatt.brres.srt0.srt0_animation import SRTMatAnim
from abmatt.gui.color_widget import ColorWidget, ColorWidgetHandler
from abmatt.gui.map_widget import Tex0WidgetGroup, Tex0WidgetSubscriber


class MaterialEditor(QWidget, ClipableObserver, ColorWidgetHandler, Tex0WidgetSubscriber):
    def __init__(self, material):
        super().__init__()
        self.stage = self.layer = self.shader = self.material = None
        self.anim = self.last_anim = None
        self.__init_UI(material)
        self.set_material(material)
        self.show()

    def __init_grid(self):
        self.grid = QGridLayout()
        self.row = 0
        frame = QFrame(self)
        frame.setFrameStyle(QFrame.Panel)
        frame.setLayout(self.grid)
        self.current_layout.addWidget(frame)

    def __add_to_layout(self, col0_label, col1=None):
        label = QLabel(col0_label, self)
        if col1:
            self.grid.addWidget(col1, self.row, 1)
        else:
            self.__init_grid()
        self.grid.addWidget(label, self.row, 0)
        self.row += 1

    def __add_checkbox(self, name, fptr):
        widget = QCheckBox(self)
        widget.stateChanged.connect(fptr)
        self.__add_to_layout(name, widget)
        return widget

    def __add_combo_box(self, name, opts, fptr):
        widget = QComboBox(self)
        widget.addItems(opts)
        widget.currentIndexChanged.connect(fptr)
        self.__add_to_layout(name, widget)
        return widget

    def __add_slider(self, name, min, max, fptr):
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(min)
        slider.setMaximum(max)
        slider.valueChanged.connect(fptr)
        self.__add_to_layout(name, slider)
        return slider

    def __add_spin_box(self, name, min, max, fptr):
        spin_box = QSpinBox(self)
        spin_box.setMinimum(min)
        spin_box.setMaximum(max)
        spin_box.valueChanged.connect(fptr)
        self.__add_to_layout(name, spin_box)
        return spin_box

    def __add_color_widget(self, name):
        c = ColorWidget(handler=self)
        self.__add_to_layout(name, c)
        return c

    def __add_layout_pane(self, layout):
        widget = QWidget(self)
        widget.setLayout(layout)
        self.top_layout.addWidget(widget)

    def __add_edit(self, name, fptr, max_width=None, validator=None):
        edit = QLineEdit(self)
        if max_width is not None:
            edit.setMaximumWidth(max_width)
        if validator is not None:
            edit.setValidator(validator)
        edit.textChanged.connect(fptr)
        self.__add_to_layout(name, edit)
        return edit

    def __init_UI(self, material):
        self.setWindowTitle('Material Editor')
        self.top_layout = QHBoxLayout()

        # MATERIAL PANE ----------------------------------------
        self.current_layout = self.mat_pane = QVBoxLayout()
        self.__init_grid()
        # self.layout = QGridLayout()
        self.name = QLabel(material.name)
        self.__add_to_layout('Material', self.name)
        self.cull_combo = self.__add_combo_box('Cull', Material.CULL_STRINGS, self.on_cull_change)
        self.animation = self.__add_combo_box('Animation', ['None', 'SRT0', 'PAT0'], self.on_animation_change)

        self.__add_to_layout('Alpha Function')
        self.ref0 = self.__add_slider('Ref0', 0, 255, self.on_ref0_change)
        self.comp0 = self.__add_combo_box('Comp0', Material.COMP_STRINGS, self.on_comp0_change)
        self.logic = self.__add_combo_box('Logic', Material.LOGIC_STRINGS, self.on_logic_change)
        self.ref1 = self.__add_slider('Ref1', 0, 255, self.on_ref1_change)
        self.comp1 = self.__add_combo_box('Comp1', Material.COMP_STRINGS, self.on_comp1_change)
        self.const_alpha_enabled = self.__add_checkbox('Constant Alpha Enable', self.on_const_alpha_enable)
        self.const_alpha = self.__add_slider('Constant Alpha', 0, 255, self.on_const_alpha_change)

        self.__add_to_layout('Blend')
        self.is_xlu = self.__add_checkbox('Xlu', self.on_xlu_change)
        self.blend_enabled = self.__add_checkbox('Blend Enable', self.on_blend_change)
        self.blend_logic_enable = self.__add_checkbox('Logic Enable', self.on_blend_logic_enable)
        self.blend_logic = self.__add_combo_box('Logic', Material.BLLOGIC_STRINGS, self.on_blend_logic_change)
        self.blend_source = self.__add_combo_box('Source', Material.BLFACTOR_STRINGS, self.on_blend_source_change)
        self.blend_dest = self.__add_combo_box('Dest', Material.BLFACTOR_STRINGS, self.on_blend_dest_change)

        self.__add_to_layout('LightChannel')
        self.vertex_color = self.__add_checkbox('Vertex Color', self.on_vertex_color_change)
        self.material_color = self.__add_color_widget('Material Color')
        self.ambient_color = self.__add_color_widget('Ambient Color')

        self.__add_to_layout('Z-Mode')
        self.compare_before_texture = self.__add_checkbox('Compare Before Texture', self.comp_before_tex_enable)
        self.depth_test = self.__add_checkbox('Depth Test', self.depth_test_enable)
        self.depth_update = self.__add_checkbox('Depth Update', self.depth_update_enable)
        self.__add_layout_pane(self.mat_pane)

        # MAP PANE ------------------------------------------------------------
        self.current_layout = self.map_pane = QVBoxLayout()
        self.maps = Tex0WidgetGroup(self, subscriber=self)
        self.__add_to_layout('Maps')
        self.__add_to_layout('Tex0:', self.maps)
        self.uwrap = self.__add_combo_box('U-Wrap', Layer.WRAP, self.on_uwrap_change)
        self.vwrap = self.__add_combo_box('V-Wrap', Layer.WRAP, self.on_vwrap_change)
        self.minfilter = self.__add_combo_box('Minfilter', Layer.FILTER, self.on_minfilter_change)
        self.magfilter = self.__add_combo_box('Magfilter', Layer.FILTER, self.on_magfilter_change)
        self.lod_bias = self.__add_edit('Lod Bias', self.on_lod_bias_change, 30, QDoubleValidator())
        self.max_anisotrophy = self.__add_combo_box('Anisotrophy', Layer.ANISOTROPHY, self.on_anisotrophy_change)
        self.clamp_bias = self.__add_checkbox('Clamp Bias', self.on_clamp_enable)
        self.interpolate = self.__add_checkbox('Texel Interpolate', self.on_interpolate_enable)
        self.mapmode = self.__add_combo_box('Map Mode', Layer.MAPMODE, self.on_mapmode_change)
        self.coordinates = self.__add_combo_box('Coordinates', Layer.COORDINATES, self.on_coordinate_change)
        self.projection = self.__add_combo_box('Projection', Layer.PROJECTION, self.on_projection_change)
        self.inputform = self.__add_combo_box('Input Form', Layer.INPUTFORM, self.on_inputform_change)
        self.normalize = self.__add_checkbox('Normalize', self.on_normalize_enable)
        self.scale = self.__add_edit('Scale', self.on_scale_change, 70)
        self.rotation = self.__add_edit('Rotation', self.on_rotation_change, 30, QDoubleValidator())
        self.translation = self.__add_edit('Translation', self.on_translation_change, 70)
        self.__add_layout_pane(self.map_pane)

        # Shader Pane ------------------------------------------
        self.current_layout = self.shader_pane = QVBoxLayout()
        self.__add_to_layout('Shader')
        self.color0 = self.__add_color_widget('Color0')
        self.color1 = self.__add_color_widget('Color1')
        self.color2 = self.__add_color_widget('Color2')
        self.const_color0 = self.__add_color_widget('Const Color0')
        self.const_color1 = self.__add_color_widget('Const Color1')
        self.const_color2 = self.__add_color_widget('Const Color2')
        self.const_color3 = self.__add_color_widget('Const Color3')
        self.__add_to_layout('Indirect')
        sels = ['Map' + str(i) for i in range(7)]
        sels.append('None')
        self.ind_map_sel = self.__add_combo_box('Map id', sels, self.on_ind_map_sel)
        self.ind_matrix_enable = self.__add_checkbox('Matrix Enable', self.on_ind_matrix_enable)
        self.ind_matrix_scale = self.__add_spin_box('Matrix Scale', -17, 46, self.on_ind_matrix_scale_change)
        ind_matrix = QWidget(self)
        layout = QGridLayout()
        self.ind_matrix = []
        for i in range(2):
            row = []
            for j in range(3):
                widget = QLineEdit()
                widget.textChanged.connect(self.on_ind_matrix_change)
                widget.setValidator(QDoubleValidator(-1.0, 1.0, 7))
                widget.setMaximumWidth(40)
                layout.addWidget(widget, i, j)
                row.append(widget)
            self.ind_matrix.append(row)
        ind_matrix.setLayout(layout)
        self.__add_to_layout('Matrix', ind_matrix)
        self.__add_layout_pane(self.shader_pane)

        # Stage Pane --------------------------------------------------
        self.current_layout = self.stage_pane = QVBoxLayout()
        self.__add_to_layout('Stage')
        self.stage_id = self.__add_combo_box('id', ['Stage 0'], self.on_stage_change)
        self.__add_checkbox('Enabled', self.on_stage_enable)
        self.stage_map_id = self.__add_combo_box('Map', sels, self.on_stage_map_id_change)
        self.stage_raster = self.__add_combo_box('Raster', stage.RASTER_COLORS, self.on_stage_raster_change)
        self.stage_ind_matrix_enable = self.__add_checkbox('Indirect Matrix', self.on_stage_ind_matrix_change)
        self.__add_to_layout('Stage Color')
        self.color_constant = self.__add_combo_box('Constant', stage.COLOR_CONSTANTS, self.on_color_constant_change)
        self.color_a = self.__add_combo_box('A', stage.COLOR_SELS, self.on_color_a_change)
        self.color_b = self.__add_combo_box('B', stage.COLOR_SELS, self.on_color_b_change)
        self.color_c = self.__add_combo_box('C', stage.COLOR_SELS, self.on_color_c_change)
        self.color_d = self.__add_combo_box('D', stage.COLOR_SELS, self.on_color_d_change)
        self.color_bias = self.__add_combo_box('Bias', stage.BIAS, self.on_color_bias_change)
        self.color_oper = self.__add_combo_box('Operation', stage.OPER, self.on_color_oper_change)
        self.color_clamp = self.__add_checkbox('Clamp', self.on_color_clamp_enable)
        self.color_scale = self.__add_combo_box('Scale', stage.SCALE, self.on_color_scale_change)
        self.color_dest = self.__add_combo_box('Destination', stage.COLOR_DEST, self.on_color_dest_change)
        self.__add_to_layout('Stage Alpha')
        self.alpha_constant = self.__add_combo_box('Constant', stage.ALPHA_CONSTANTS, self.on_alpha_constant_change)
        self.alpha_a = self.__add_combo_box('A', stage.ALPHA_SELS, self.on_alpha_a_change)
        self.alpha_b = self.__add_combo_box('B', stage.ALPHA_SELS, self.on_alpha_b_change)
        self.alpha_c = self.__add_combo_box('C', stage.ALPHA_SELS, self.on_alpha_c_change)
        self.alpha_d = self.__add_combo_box('D', stage.ALPHA_SELS, self.on_alpha_d_change)
        self.alpha_bias = self.__add_combo_box('Bias', stage.BIAS, self.on_alpha_bias_change)
        self.alpha_oper = self.__add_combo_box('Operation', stage.OPER, self.on_alpha_oper_change)
        self.alpha_clamp = self.__add_checkbox('Clamp', self.on_alpha_clamp_enable)
        self.alpha_scale = self.__add_combo_box('Scale', stage.SCALE, self.on_alpha_scale_change)
        self.alpha_dest = self.__add_combo_box('Destination', stage.ALPHA_DEST, self.on_alpha_dest_change)
        self.__add_layout_pane(self.stage_pane)

        # self.animations = QLabel('None', self)
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
        if self.__try_set(self.material, material):
            self.material = material
            if len(material.layers):
                self.__set_layer(material.layers[0])
            else:
                self.__set_layer(None)
            self.__set_shader(material.shader)
            self.__set_anim(material.get_animation())

    def __set_anim(self, anim):
        if self.__try_set(self.anim, anim):
            self.anim = anim

    def __set_layer(self, layer):
        if self.__try_set(self.layer, layer):
            self.layer = layer

    def __set_stage(self, stage):
        if self.__try_set(self.stage, stage):
            self.stage = stage

    def __set_shader(self, shader):
        if self.__try_set(self.shader, shader):
            self.shader = shader

    # ------------------------------------------------------
    # EVENT HANDLERS
    # ------------------------------------------------------
    # Interface updates
    def on_node_update(self, node):
        pass

    def on_child_update(self, child):
        pass

    def on_rename_update(self, node):
        pass

    def on_color_change(self, widget, color):
        pass

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
                    self.anim.paste(self.last_anim)
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
            self.material.setBlendDestStr(self.blend_dest.currentText())

    def on_blend_source_change(self, i):
        if self.material.blend_source != i:
            self.material.setBlendSrcStr(self.blend_source.currentText())

    def on_blend_logic_change(self, i):
        if self.material.blend_logic != i:
            self.material.setBlendLogicStr(self.blend_logic.currentText())

    def on_blend_logic_enable(self):
        if self.material.blend_logic_enabled != self.blend_logic_enable.isChecked():
            self.material.enableBlendLogic(self.blend_logic_enable.isChecked())

    def on_blend_change(self):
        if self.material.blend_enabled != self.blend_enabled.isChecked():
            self.material.enable_blend(self.blend_enabled.isChecked())

    def on_xlu_change(self):
        if self.material.is_xlu() != self.is_xlu.isChecked():
            self.material.enable_xlu(self.is_xlu.isChecked())

    def on_comp1_change(self, i):
        if self.material.comp1 != i:
            self.material.setComp1Str(self.comp1.currentText())

    def on_ref1_change(self, i):
        if self.material.ref1 != i:
            self.material.setRef1Str(str(i))

    def on_logic_change(self, i):
        if self.material.logic != i:
            self.material.setLogic(self.logic.currentText())

    def on_comp0_change(self, i):
        if self.material.comp0 != i:
            self.material.setComp0Str(self.comp0.currentText())

    def on_ref0_change(self, i):
        if self.material.ref0 != i:
            self.material.setRef0Str(str(i))

    def on_cull_change(self, i):
        if self.material.cullmode != i:
            self.material.setCullModeStr(self.cull_combo.currentText())

    def on_const_alpha_change(self, i):
        if self.material.constant_alpha != i:
            self.material.setConstantAlphaStr(str(i))

    def on_const_alpha_enable(self):
        if self.material.constant_alpha_enabled != self.const_alpha_enabled.isChecked():
            self.material.setConstantAlphaStr('120')

    def comp_before_tex_enable(self):
        if self.material.compareBeforeTexture != self.compare_before_texture.isChecked():
            self.material.setCompareBeforeTexStr()

    def depth_test_enable(self):
        if self.material.depth_test != self.depth_test.isChecked():
            self.material.setEnableDepthTest(self.depth_test.isChecked())

    def depth_update_enable(self):
        if self.material.depth_update != self.depth_update.isChecked():
            self.material.setEnableDepthUpdate(self.depth_update.isChecked())

    # ------------------------------------------------------
    # INDIRECT
    def on_ind_matrix_enable(self):
        if self.material.isIndMatrixEnabled() != self.ind_matrix_enable.isChecked():
            self.material.setIndMatrixEnable(enable=self.ind_matrix_enable.isChecked())

    def on_ind_map_sel(self, i):
        if self.shader.getIndMap() != i:
            self.shader.setIndMap(i)
            self.shader.setIndCoord(i)

    def on_ind_matrix_scale_change(self):
        if self.material.getIndMatrixScale() != self.ind_matrix_scale.value():
            self.material.setIndMatrixScale(self.ind_matrix_scale.value())

    def on_ind_matrix_change(self):
        matrix = []
        for row in self.ind_matrix:
            x = []
            for col in range(len(row)):
                text = row[col].text()
                if not re.match('-?[0-1](\.\d+)?', text):
                    row[col].setText('0')
                    return
                x.append(text)
            matrix.append(x)
        self.material.setIndMatrix(matrix)

    # ----------------------------------------------
    #   LAYER functions
    # ----------------------------------------------
    def on_map_change(self, index):
        self.__set_layer(self.material.layers[index])

    def on_uwrap_change(self):
        pass

    def on_vwrap_change(self):
        pass

    def on_minfilter_change(self):
        pass

    def on_magfilter_change(self):
        pass

    def on_lod_bias_change(self):
        pass

    def on_mapmode_change(self):
        pass

    def on_coordinate_change(self):
        pass

    def on_projection_change(self):
        pass

    def on_inputform_change(self):
        pass

    def on_normalize_enable(self):
        pass

    def on_scale_change(self):
        pass

    def on_rotation_change(self):
        pass

    def on_translation_change(self):
        pass

    def on_anisotrophy_change(self):
        pass

    def on_clamp_enable(self):
        pass

    def on_interpolate_enable(self):
        pass

    def on_scn0_light_ref_change(self):
        pass

    def on_scn0_camera_ref_change(self):
        pass

    # STAGE
    def on_stage_change(self):
        pass

    def on_stage_enable(self):
        pass

    def on_stage_map_id_change(self):
        pass

    def on_stage_raster_change(self):
        pass

    def on_color_constant_change(self):
        pass

    def on_color_a_change(self):
        pass

    def on_color_b_change(self):
        pass

    def on_color_c_change(self):
        pass

    def on_color_d_change(self):
        pass

    def on_color_bias_change(self):
        pass

    def on_color_oper_change(self):
        pass

    def on_color_clamp_enable(self):
        pass

    def on_color_scale_change(self):
        pass

    def on_color_dest_change(self):
        pass

    def on_alpha_constant_change(self):
        pass

    def on_alpha_a_change(self):
        pass

    def on_alpha_b_change(self):
        pass

    def on_alpha_c_change(self):
        pass

    def on_alpha_d_change(self):
        pass

    def on_alpha_bias_change(self):
        pass

    def on_alpha_oper_change(self):
        pass

    def on_alpha_clamp_enable(self):
        pass

    def on_alpha_scale_change(self):
        pass

    def on_alpha_dest_change(self):
        pass

    def on_stage_ind_matrix_change(self):
        pass
    # ------------------------------------------------
    # End EVENT HANDLERS
    # ------------------------------------------------