import fnmatch
import os
import sys

from abmatt.autofix import AutoFix
from abmatt.brres import Brres
from abmatt.converters.convert_dae import DaeConverter


def analyze_material(mat):
    pass
    # for s in mat.shader.stages:
    #     if s.ind_format != stage.IND_F_8_BIT_OFFSETS:
    #         print('Indirect format change!')
    #     if s.ind_alpha != stage.IND_ALPHA_OFF:
    #         print('Indirect Alpha!')
    #     if s.ind_s_wrap != stage.IND_WRAP_NONE:
    #         print('S WRAP!')
    #     if s.ind_t_wrap != stage.IND_WRAP_NONE:
    #         print('T WRAP!')
    #     if s.ind_use_prev:
    #         print('Use prev!')
    #     if s.ind_unmodify_lod:
    #         print('Unmodify lod!')
    # DOES NOT CHANGE
    # if stage.map_id != stage.coord_id:
    #     print(f'{mat.name} shader has map id that does not match coord id')

    # ONLY 1 INSTANCE OF CHANGING
    # if stage.texture_swap_sel:
    #     print(f'{mat.name} texture swap sel enabled!')
    # if stage.raster_swap_sel:
    #     print(f'{mat.name} raster swap sel enabled!')

    # CHANGES
    # if stage.bias:
    #     print(f'{mat.name} bias enabled!')
    # if stage.oper:
    #     print(f'{mat.name} operation not add.')
    # if stage.clamp != True:
    #     print(f'{mat.name} clamp not enabled')

    # THESE CHANGE
    # if layer.scn0_light_ref != -1:
    #     print(f'{layer.name} scn0 light ref not -1 in {layer.parent.getBrres().name}!')
    # if layer.scn0_camera_ref != -1:
    #     print(f'{layer.name} scn0 camera ref not -1 in {layer.parent.getBrres().name}!')
    # if layer.clamp_bias:
    #     print(f'{layer.name} clamp enabled!')
    # if layer.texel_interpolate:
    #     print(f'{layer.name} interpolate enabled!')
    # if layer.magfilter != 1:
    #     print(f'{layer.name} magfilter {layer.magfilter}')

    # THESE DON"T CHANGE
    # if layer.emboss_source != 5:
    #     print(f'{layer.name} emboss source {layer.emboss_source}!')
    # if layer.type:
    #     print(f'{layer.name} type {layer.type}!')
    # if layer.emboss_light:
    #     print(f'{layer.name} emboss light {layer.emboss_light}!')

    # changes
    # if not mat.depth_test:
    #     print(f'{mat.name} depth test {mat.depth_test}')

    # These don't change ##########################################
    # if mat.depth_function != material.COMP_LESS_THAN_OR_EQUAL:
    #     print(f'{mat.name} depth function {mat.depth_function}')
    # if mat.blend_dither:
    #     print(f'{mat.name} blend dither enabled')
    # if mat.blend_update_color:
    #     print(f'{mat.name} blend update color enabled')
    # if mat.blend_update_alpha:
    #     print(f'{mat.name} blend update alpha enabled')
    # if mat.blend_subtract:
    #     print(f'{mat.name} blend subtract enabled')
    ###############################################################

    # THESE DO CHANGE ###########################################
    # if mat.blend_logic != material.BLEND_LOGIC_COPY:
    #     print(f'{mat.name} blend logic {mat.blend_logic}')
    # if mat.blend_source != material.BLEND_FACTOR_SOURCE_ALPHA:
    #     print(f'{mat.name} blend source {mat.blend_source}')
    # if mat.blend_dest != material.BLEND_FACTOR_INVERSE_SOURCE_ALPHA:
    #     print(f'{mat.name} blend dest {mat.blend_dest}')
    # if mat.blend_logic_enabled:
    #     print(f'{mat.name} blend logic enabled')
    ##############################################################

    # Always use matrix 0, ind_map and ind_coord the same and always first one


def perform_analysis(brres):
    s = ''
    has_count = 0
    if brres.chr0:
        s += ' has chr0'
    if brres.shp0:
        s += ' has shp0'
        has_count += 1
    if brres.clr0:
        s += ' has clr0'
        has_count += 1
    if brres.unused_pat0:
        s += ' has unused pat0'
    if brres.unused_srt0:
        s += ' has unused srt0'
    if brres.scn0:
        s += ' has scn0'
        has_count += 1
    if has_count:
        AutoFix.info(f'{brres.name} {s}')
    # AutoFix.info('Analyzing {}'.format(brres.name))
    export = False
    # for model in brres.models:
    #     for mat in model.materials:
    #         if len(mat.polygons) > 1:
    #             print(f'{brres.name}/{model.name} has multiple polys/mat')
    #             print('Mat {} used more than once by {}'.format(mat.name, [x.name for x in mat.polygons]))
    #
    #     has_uv_mtx = False
    #     for x in poly.uv_mtx_indices:
    #         if x >= 0:
    #             has_uv_mtx = True
    #             break
    #     if has_uv_mtx:
    #         decode_polygon(poly, decode_mdl0_influences(model))
    # for model in brres.models:
    #     for material in model.materials:
    #         analyze_material(material)
    # brres.save(os.path.join(os.path.dirname(os.getcwd()), 'tmp', 'tmp.brres'), overwrite=True)


def gather_files(root, match_filter=None, filter='.brres', exclude=['tmp']):
    """
    Recursively gathers brres files in root
    :param root: path
    :param files: list to gather files in
    """
    for file in os.listdir(root):
        path = os.path.join(root, file)
        if file.startswith('.'):
            continue
        if os.path.isdir(path) and file not in exclude:
            yield from gather_files(path, match_filter, filter)
        elif file.endswith(filter):
            if match_filter is None or fnmatch.fnmatch(file, match_filter):
                yield path


def get_project_root():
    directory = os.getcwd()
    while True:
        new_dir, name = os.path.split(directory)
        if name == 'abmatt':
            return directory
        directory = new_dir
        if not directory:
            break


if __name__ == '__main__':
    args = sys.argv[1:]
    filter = None
    if not len(args):
        root = os.getcwd()
        if os.path.basename(root) == 'debug':
            root = os.path.dirname(root)
            os.chdir(root)
    else:
        root = args.pop(0)
        if not os.path.exists(root) or not os.path.isdir(root):
            print('Invalid root path')
            sys.exit(1)
    for x in gather_files(root, filter):
        perform_analysis(Brres(x))
