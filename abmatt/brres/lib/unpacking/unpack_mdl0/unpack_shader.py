from brres.lib.unpacking.interface import Unpacker
from brres.lib.unpacking.unpack_mdl0 import bp
from brres.mdl0.shader import Shader
from brres.mdl0.stage import Stage


class UnpackShader(Unpacker):
    def __init__(self, name, mdl0, binfile):
        s = Shader(name, None)
        super().__init__(s, binfile)

    def unpack(self, shader, binfile):
        """ Unpacks shader TEV """
        self.offset = binfile.start()
        binfile.readLen()
        outer, index, stage_count, res0, res1, res2, = binfile.read("2I4B", 12)
        layer_indices = binfile.read("8B", 8)
        for i in range(len(layer_indices)):
            assert i == layer_indices[i]
        assert (stage_count <= 16)
        shader.stages = []
        for i in range(stage_count):
            shader.stages.append(Stage(len(shader.stages), shader))
        binfile.advance(8)
        for x in shader.swap_table:
            binfile.advance(5)  # skip extra masks
            x.unpack(binfile)
        shader.indTexMaps, shader.indTexCoords = bp.unpack_ras1_iref(binfile)
        binfile.align()
        i = 0
        while i < stage_count:
            stage0 = shader.stages[i]
            i += 1
            if i < stage_count:
                stage1 = shader.stages[i]
                i += 1
            else:
                stage1 = None
            binfile.advance(5)  # skip mask
            stage0.constant, stage0.constant_a, s1_constant, s1_alpha_constant = bp.unpack_kcel(binfile)
            tref_0, tref_1 = bp.unpack_tref(binfile)
            stage0.map_id, stage0.coord_id, stage0.enabled, stage0.raster_color = tref_0
            stage0.sel_a, stage0.sel_b, stage0.sel_c, stage0.sel_d, \
                stage0.dest, stage0.bias, stage0.oper, stage0.clamp, stage0.scale = bp.unpack_color_env(binfile)
            if stage1:
                stage1.constant = s1_constant
                stage1.constant_a = s1_alpha_constant
                stage1.map_id, stage1.coord_id, stage1.enabled, stage1.raster_color = tref_1
                stage1.sel_a, stage1.sel_b, stage1.sel_c, stage1.sel_d, \
                    stage1.dest, stage1.bias, stage1.oper, stage1.clamp, stage0.scale = bp.unpack_color_env(binfile)
            else:
                binfile.advance(5)  # skip unpack color env
            stage0.sel_a_a, stage0.sel_b_a, stage0.sel_c_a, stage0.sel_d_a, \
                stage0.dest_a, stage0.bias_a, stage0.oper_a, stage0.clamp_a, stage0.scale_a, \
                stage0.texture_swap_sel, stage0.raster_swap_sel = bp.unpack_alpha_env(binfile)
            if stage1:
                stage1.sel_a_a, stage1.sel_b_a, stage1.sel_c_a, stage1.sel_d_a, \
                    stage1.dest_a, stage1.bias_a, stage1.oper_a, stage1.clamp_a, stage1.scale_a, \
                    stage1.texture_swap_sel, stage1.raster_swap_sel = bp.unpack_alpha_env(binfile)
            else:
                binfile.advance(5)
            stage0.ind_stage, stage0.ind_format, stage0.ind_bias, stage0.ind_alpha, \
                stage0.ind_matrix, stage0.ind_s_wrap, stage0.ind_t_wrap, \
                stage0.ind_use_prev, stage0.ind_unmodify_lod = bp.unpack_ind_cmd(binfile)
            if stage1:
                stage1.ind_stage, stage1.ind_format, stage1.ind_bias, stage1.ind_alpha, \
                    stage1.ind_matrix, stage1.ind_s_wrap, stage1.ind_t_wrap, \
                    stage1.ind_use_prev, stage1.ind_unmodify_lod = bp.unpack_ind_cmd(binfile)
            else:
                binfile.advance(5)
            binfile.align(16)
        binfile.end()
