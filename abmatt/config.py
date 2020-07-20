#!/usr/bin/python
"""For reading configuration file"""
import os

from abmatt.autofix import AUTO_FIXER
from abmatt.command import Command
from abmatt.subfile import SubFile
from abmatt.matching import MATCHING, validBool
from abmatt.brres import Brres
from abmatt.layer import Layer
from abmatt.mdl0 import Mdl0
from abmatt.pat0 import Pat0
from abmatt.srt0 import Srt0
from abmatt.shader import Shader


def parse_line(line):
    if line:
        comment = line.find('#')
        if comment >= 0:
            line = line[:comment]
        split_line = line.split('=', 1)
        if len(split_line) > 1:
            return [x.strip().lower() for x in split_line]
    return None


class Config:
    def __init__(self, filename):
        self.config = {}
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                for cnt, line, in enumerate(f):
                    result = parse_line(line)
                    if result is not None:
                        self.config[result[0]] = result[1]

    def __getitem__(self, item):
        return self.config.get(item)

    def __setitem__(self, key, value):
        self.config[key] = value


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


def load_config(app_dir, loudness=None, autofix_level=None):
    conf = Config(os.path.join(app_dir, 'config.conf'))
    if not loudness:
        loudness = conf['loudness']
    if loudness:
        try:
            AUTO_FIXER.set_loudness(loudness)
        except ValueError:
            AUTO_FIXER.warn('Invalid loudness level {}'.format(loudness))
    if not autofix_level:
        autofix_level = conf['autofix']
    if autofix_level:
        try:
            AUTO_FIXER.set_fix_level(autofix_level)
        except ValueError:
            AUTO_FIXER.warn('Invalid autofix level {}'.format(autofix_level))
    max_brres_files = conf['max_brres_files']
    if max_brres_files:
        try:
            i = int(max_brres_files)
            Command.MAX_FILES_OPEN = i
        except:
            pass
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