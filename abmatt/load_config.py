import os

from brres import Brres
from autofix import AutoFix
from brres.lib.matching import validBool, MATCHING, parse_color, validInt
from brres.mdl0 import Mdl0
from brres.mdl0.layer import Layer
from brres.mdl0.material import Material
from brres.mdl0.shader import Shader, Stage
from brres.pat0 import Pat0
from brres.srt0 import Srt0
from brres.subfile import SubFile
from brres.tex0 import Tex0, ImgConverterI
from command import Command
from config import Config


def set_rename_unknown(val):
    try:
        Mdl0.RENAME_UNKNOWN_REFS = Layer.RENAME_UNKNOWN_REFS = Pat0.RENAME_UNKNOWN_REFS = validBool(val)
    except ValueError:
        pass


def set_remove_unknown(val):
    try:
        Mdl0.REMOVE_UNKNOWN_REFS = Layer.REMOVE_UNKNOWN_REFS = Pat0.REMOVE_UNKNOWN_REFS = Srt0.REMOVE_UNKNOWN_REFS = \
            validBool(val)
    except ValueError:
        pass


def set_remove_unused(val):
    try:
        Shader.REMOVE_UNUSED_LAYERS = Stage.REMOVE_UNUSED_LAYERS = validBool(val)
    except ValueError:
        pass


def load_config(app_dir, loudness=None, autofix_level=None):
    conf = Config.get_instance(os.path.join(app_dir, 'config.conf'))
    if not loudness:
        loudness = conf['loudness']
    if loudness:
        try:
            AutoFix.get().set_loudness(loudness)
        except ValueError:
            AutoFix.get().warn('Invalid loudness level {}'.format(loudness))
    if not len(conf):
        AutoFix.get().warn('No configuration detected (etc/abmatt/config.conf).')
        return
    Command.set_max_brres_files(conf)
    # Matching stuff
    MATCHING.set_case_sensitive(conf['case_sensitive'])
    MATCHING.set_partial_matching(conf['partial_matching'])
    MATCHING.set_regex_enable(conf['regex_matching'])
    # Autofixes
    try:
        SubFile.FORCE_VERSION = validBool(conf['force_version'])
    except ValueError:
        pass
    try:
        Brres.REMOVE_UNUSED_TEXTURES = validBool(conf['remove_unused_textures'])
    except ValueError:
        pass
    try:
        Layer.MINFILTER_AUTO = validBool(conf['minfilter_auto'])
    except ValueError:
        pass
    set_rename_unknown(conf['rename_unknown_refs'])
    set_remove_unknown(conf['remove_unknown_refs'])
    set_remove_unused(conf['remove_unused_layers'])
    try:
        Mdl0.DETECT_MODEL_NAME = validBool(conf['detect_model_name'])
    except ValueError:
        pass
    try:
        Mdl0.DRAW_PASS_AUTO = validBool(conf['draw_pass_auto'])
    except ValueError:
        pass
    try:
        Shader.MAP_ID_AUTO = validBool(conf['map_id_auto'])
    except ValueError:
        pass
    try:
        Material.DEFAULT_COLOR = parse_color(conf['default_material_color'])
    except ValueError:
        pass
    try:
        Tex0.RESIZE_TO_POW_TWO = validBool(conf['resize_pow_two'])
    except ValueError:
        pass
    try:
        Tex0.set_max_image_size(validInt(conf['max_image_size'], 0, 10000))
    except (TypeError, ValueError):
        pass
    resample = conf['img_resample']
    if resample is not None:
        ImgConverterI.set_resample(resample)
    Brres.MATERIAL_LIBRARY = conf['material_library']
    return conf