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
from abmatt.brres.mdl0.stage import Stage
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

    def __add_edit_grid(self, fptr, max_rows=1, max_cols=1, max_width=40, validator=None):
        widget = QWidget(self)
        layout = QGridLayout()
        ret = []
        for row in range(max_rows):
            widget_row = []
            for col in range(max_cols):
                edit = QLineEdit(self)
                if max_width:
                    edit.setMaximumWidth(max_width)
                if validator:
                    edit.setValidator(validator)
                edit.textChanged.connect(fptr)
                layout.addWidget(edit, row, col)
                widget_row.append(edit)
            ret.append(widget_row)
        widget.setLayout(layout)
        if len(ret) == 1:
            return widget, widget_row
        return widget, ret

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
        self.maps = Tex0WidgetGroup(self)
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
        self.sc_widget, self.scale = self.__add_edit_grid(self.on_scale_change, max_width=30, max_cols=2)
        self.__add_to_layout('Scale', self.sc_widget)
        self.rotation = self.__add_edit('Rotation', self.on_rotation_change, 30, QDoubleValidator())
        self.tr_widget, self.translation = self.__add_edit_grid(self.on_translation_change, max_width=30, max_cols=2)
        self.__add_to_layout('Translation', self.tr_widget)
        self.__add_layout_pane(self.map_pane)

        # Shader Pane ------------------------------------------
        self.current_layout = self.shader_pane = QVBoxLayout()
        self.__add_to_layout('Shader')
        self.colors = colors = []
        for i in range(3):
            colors.append(self.__add_color_widget('Color' + str(i)))
        self.const_colors = const_colors = []
        for i in range(4):
            const_colors.append(self.__add_color_widget('Const Color' + str(i)))
        self.__add_to_layout('Indirect')
        sels = ['Map' + str(i) for i in range(7)]
        sels.append('None')
        self.ind_map_sel = self.__add_combo_box('Map id', sels, self.on_ind_map_sel)
        self.ind_matrix_enable = self.__add_checkbox('Matrix Enable', self.on_ind_matrix_enable)
        self.ind_matrix_scale = self.__add_spin_box('Matrix Scale', -17, 46, self.on_ind_matrix_scale_change)
        self.ind_matrix_widget, self.ind_matrix = self.__add_edit_grid(self.on_ind_matrix_change, 2, 3, 40, QDoubleValidator(-1.0, 1.0, 7))
        self.__add_to_layout('Matrix', self.ind_matrix_widget)
        self.__add_layout_pane(self.shader_pane)

        # Stage Pane --------------------------------------------------
        self.current_layout = self.stage_pane = QVBoxLayout()
        self.__add_to_layout('Stage')
        self.stage_id = self.__add_combo_box('id', ['Stage 0'], self.on_stage_change)
        self.stage_enable = self.__add_checkbox('Enabled', self.on_stage_enable)
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
            self.__on_material_update(material)
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
            self.__on_layer_update(layer)

    def __set_stage(self, stage):
        if self.__try_set(self.stage, stage):
            self.stage = stage
            self.__on_stage_update(stage)

    def __set_shader(self, shader):
        if self.__try_set(self.shader, shader):
            self.shader = shader
            self.__set_stage(shader.stages[0])
            self.__on_shader_update(shader)

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
        for i in range(3):
            self.colors[i].set_color(material.getColor(i))
        for i in range(4):
            self.const_colors[i].set_color(material.getConstantColor(i))
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
        if self.shader is not material.shader:
            self.__set_shader(material.shader)

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
        for i in range(2):
            self.scale[i].setText(str(layer.scale[i]))
        self.rotation.setText(str(layer.rotation))
        for i in range(2):
            self.translation[i].setText(str(layer.translation[i]))

    def __on_shader_update(self, shader):
        self.ind_map_sel.setCurrentIndex(shader.indTexMaps[0])
        self.ind_matrix_enable.setChecked(self.material.isIndMatrixEnabled())
        self.ind_matrix_scale.setValue(self.material.getIndMatrixScale())
        ind_matrix = self.ind_matrix
        mat_matrix = self.material.getIndMatrix()
        for i in range(2):
            for j in range(3):
                ind_matrix[i][j].setText(str(mat_matrix[i][j]))
        my_count = self.stage_id.count()
        need_count = len(shader.stages)
        if my_count > need_count:
            current_i = self.stage_id.currentIndex()
            for i in range(my_count - 1, need_count - 1, -1):
                self.stage_id.removeItem(i)
            if current_i >= need_count and len(shader.stages):
                self.stage_id.setCurrentIndex(0)
        elif my_count < need_count:
            for i in range(my_count, need_count):
                self.stage_id.addItem('Map ' + str(i))

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
        if type(node) == Material:
            self.__on_material_update(node)
        elif type(node) == Layer:
            self.__on_layer_update(node)
        elif type(node) == Shader:
            self.__on_shader_update(node)
        elif type(node) == Stage:
            self.__on_stage_update(node)

    def on_child_update(self, child):
        pass

    def on_rename_update(self, node):
        if type(node) == Layer:
            self.maps.set_tex0s(self.material.get_tex0s())

    def on_color_change(self, widget, color):
        if widget == self.material_color:
            self.material.set_material_color(color)
        elif widget == self.ambient_color:
            self.material.set_ambient_color(color)
        else:
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
    def on_map_change(self, tex0, index):
        layer = self.material.layers[index]
        if self.layer is not layer:
            self.__set_layer(layer)

    def on_map_add(self, tex0, index):
        self.material.addLayer(tex0.name)

    def on_map_remove(self, tex0, index):
        self.material.removeLayerI(index)

    def on_map_replace(self, tex0, index):
        self.layer.rename(tex0.name)

    def on_uwrap_change(self, i):
        self.layer.setUWrapStr(self.uwrap.currentText())

    def on_vwrap_change(self, i):
        self.layer.setVWrapStr(self.vwrap.currentText())

    def on_minfilter_change(self, i):
        self.layer.setMinFilterStr(self.minfilter.currentText())

    def on_magfilter_change(self, i):
        self.layer.setMagFilterStr(self.magfilter.currentText())

    def on_lod_bias_change(self):
        self.layer.setLodBiasStr(self.lod_bias.text())

    def on_mapmode_change(self, i):
        self.layer.setMapmodeStr(self.mapmode.currentText())

    def on_coordinate_change(self, i):
        self.layer.setCoordinatesStr(self.coordinates.currentText())

    def on_projection_change(self, i):
        self.layer.setProjectionStr(self.projection.currentText())

    def on_inputform_change(self, i):
        self.layer.setInputFormStr(self.inputform.currentText())

    def on_normalize_enable(self):
        self.layer.normalize = self.normalize.isChecked()

    def on_scale_change(self):
        # validate the scale
        scale = []
        for x in self.scale:
            try:
                scale.append(float(x.text()))
            except ValueError:
                x.setText('0.0')
                return
        self.layer.set_scale(scale)

    def on_rotation_change(self):
        try:
            self.layer.set_rotation(float(self.rotation.text()))
        except ValueError:
            self.rotation.setText('0.0')

    def on_translation_change(self):
        tr = []
        for x in self.translation:
            try:
                tr.append(float(x.text()))
            except ValueError:
                x.setText('0.0')
                return
        self.layer.set_translation(tr)

    def on_anisotrophy_change(self, i):
        self.layer.setAnisotrophyStr(self.max_anisotrophy.currentText())

    def on_clamp_enable(self):
        self.layer.setClampBiasStr(str(self.clamp_bias.isChecked()).lower())

    def on_interpolate_enable(self):
        self.layer.setTexelInterpolateStr(str(self.interpolate.isChecked()).lower())

    # STAGE
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

    def on_stage_ind_matrix_change(self):
        enable = self.stage_ind_matrix_enable.isChecked()
        if enable:
            self.stage.set_ind_bias(stage.IND_BIAS_STU)
            self.stage.set_ind_matrix(stage.IND_MATRIX_0)
        else:
            self.stage.set_ind_bias(stage.IND_BIAS_NONE)
            self.stage.set_ind_matrix(stage.IND_MATRIX_NONE)

    # ------------------------------------------------
    # End EVENT HANDLERS
    # ------------------------------------------------
