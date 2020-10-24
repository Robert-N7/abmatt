from abmatt.brres.lib.packing.interface import Packer
from abmatt.brres.lib.packing.pack_mdl0 import bp

BYTESIZE = 512
SWAP_MASK = 0x00000F
SEL_MASK = 0xFFFFF0


class PackShader(Packer):
    def __init__(self, node, binfile, index):
        self.index = index
        super().__init__(node, binfile)

    def pack_stages(self, binfile):
        i = j = 0  # j for every 2 stages, i for every stage
        stages = self.node.stages
        while i < len(stages):
            s0 = stages[i]
            s0_id = i
            i += 1
            if i < len(stages):
                s1 = stages[i]
                s1_id = i
                i += 1
            else:
                s1 = None
            bp.pack_bp_mask(binfile, SEL_MASK)
            # KCEL
            cc = s0.get_constant_color()
            ac = s0.get_constant_alpha()
            if s1:
                cc1 = s1.get_constant_color()
                ac1 = s1.get_constant_alpha()
                bp.pack_kcel(binfile, j, cc, ac, cc1, ac1)
                bp.pack_tref(binfile, j, s0.get_map_id(), s0.get_coord_id(), s0.is_enabled(), s0.get_raster_color(),
                             s1.get_map_id(), s1.get_coord_id(), s1.is_enabled(), s1.get_raster_color())
            else:
                bp.pack_kcel(binfile, j, cc, ac)
                bp.pack_tref(binfile, j, s0.get_map_id(), s0.get_coord_id(), s0.is_enabled(), s0.get_raster_color(),
                             0x7, 0x7, 0, 0x7)
            # color env
            bp.pack_color_env(binfile, s0_id, s0.sel_a, s0.sel_b, s0.sel_c, s0.sel_d,
                              s0.dest, s0.bias, s0.oper,
                              s0.clamp, s0.scale)
            if s1:
                bp.pack_color_env(binfile, s1_id, s1.sel_a, s1.sel_b, s1.sel_c, s1.sel_d,
                                  s1.dest, s1.bias, s1.oper,
                                  s1.clamp, s1.scale)
            else:
                binfile.advance(5)

            #   alpha env
            bp.pack_alpha_env(binfile, s0_id, s0.sel_a_a, s0.sel_b_a, s0.sel_c_a, s0.sel_d_a,
                              s0.dest_a, s0.bias_a, s0.oper_a,
                              s0.clamp_a, s0.scale_a, s0.texture_swap_sel, s0.raster_swap_sel)
            if s1:
                bp.pack_alpha_env(binfile, s1_id, s1.sel_a_a, s1.sel_b_a, s1.sel_c_a, s1.sel_d_a,
                                  s1.dest_a, s1.bias_a, s1.oper_a,
                                  s1.clamp_a, s1.scale_a, s1.texture_swap_sel, s1.raster_swap_sel)
            else:
                binfile.advance(5)

            #   indirect
            bp.pack_ind_cmd(binfile, s0_id, s0.ind_stage, s0.ind_format,
                            s0.ind_bias, s0.ind_alpha,
                            s0.ind_matrix, s0.ind_s_wrap, s0.ind_t_wrap,
                            s0.ind_use_prev, s0.ind_unmodify_lod)
            if s1:
                bp.pack_ind_cmd(binfile, s1_id, s1.ind_stage, s1.ind_format,
                                s1.ind_bias, s1.ind_alpha,
                                s1.ind_matrix, s1.ind_s_wrap, s1.ind_t_wrap,
                                s1.ind_use_prev, s1.ind_unmodify_lod)
            binfile.align(16)
            j += 1

    def pack(self, shader, binfile):
        """ Packs the shader """
        self.offset = binfile.start()
        binfile.write("IiI4B", BYTESIZE, binfile.getOuterOffset(), self.index,
                      len(shader.stages), 0, 0, 0)
        layer_indices = [0xff] * 8
        for i in range(shader.getTexRefCount()):
            layer_indices[i] = i
        binfile.write("8B", *layer_indices)
        binfile.align()
        for kcel in shader.swap_table:
            bp.pack_bp_mask(binfile, SWAP_MASK)
            kcel.pack(binfile)
        # indirect data
        bp.pack_ras1_iref(binfile, shader.indTexMaps, shader.indTexCoords)
        binfile.align()
        self.pack_stages(binfile)
        binfile.advanceAndEnd(BYTESIZE)
