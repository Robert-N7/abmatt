import struct


def get_bit_width(interpreter_path):
    size = struct.calcsize('P') * 8
    return 'x86' if size == 32 else 'x64'
    # dir = os.path.dirname(interpreter_path)
    # dir, dir_name = os.path.split(dir)
    # if 'Python' in dir_name:
    #     return 'x86' if dir_name[-3:] == '-32' else 'x64'
    # base, dir_name = os.path.split(dir)
    # if 'venv' in dir_name:
    #     c = Config(os.path.join(dir, 'pyvenv.cfg'))
    #     dir, dir_name = os.path.split(c['home'])
    #     if 'python' in dir_name:
    #         return 'x86' if dir_name[-3:] == '-32' else 'x64'
    # raise ValueError(f'Bit width undetected in {interpreter_path}')
