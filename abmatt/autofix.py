"""Debugging and fixing"""


class AutoFixAbort(BaseException):
    """Raised by prompt"""
    def __init__(self):
        super(AutoFixAbort, self).__init__('Operation aborted')


class AutoFix:
    # Fix Level
    # None 0
    # Errors 1
    # Warnings 2
    # Checks 3
    # Info 4    / all
    # Prompt 5
    FIX_LEVEL = 3
    FIX_PROMPT = 5

    LOUDNESS = 4  # Loudness levels, 0 silent, 1 errors, 2 warnings, 3 Checks, 4 Info
    ERROR_LEVELS = ('NONE', 'ERROR', 'WARNING', 'CHECK', 'INFO', 'PROMPT')

    def can_prompt(self):
        return self.FIX_LEVEL == self.FIX_PROMPT

    def should_fix(self, description, bug_level):
        """Determines if a bug should be fixed"""
        fix_level = AutoFix.FIX_LEVEL
        if fix_level >= bug_level:
            should_fix = True
            if fix_level == self.FIX_PROMPT:
                should_fix = self.prompt(description)
            if should_fix:
                if self.LOUDNESS >= bug_level:
                    print('FIX: {}'.format(description))
                return True
        self.notify(description, bug_level)
        return False

    @staticmethod
    def prompt(description):
        while True:
            result = input('Auto fix: ' + description + '? (y/n)').lower()
            if result[0] == 'y':
                return 1
            elif result[0] == 'n':
                return 0
            elif result[0] == 'a':  # abort option
                raise AutoFixAbort()
            else:
                print('Invalid response, expects yes, no, or abort.')

    def notify(self, description, bug_level):
        """Notifies of a bug check"""
        if bug_level <= self.LOUDNESS:
            print('{}: {}'.format(self.ERROR_LEVELS[bug_level], description))

    def get_level(self, level_str):
        """Expects level to be a string, as a number or one of the Error levels"""
        if level_str.isDigit():
            level = int(level_str)
            if not 0 <= level < 6:
                raise ValueError('Loudness level out of range (0-6)')
            return int(level)
        else:
            level_str = level_str.upper()
            if level_str == 'ALL':
                return 4
            return self.ERROR_LEVELS.index(level_str)

    def set_loudness(self, level_str):
        AutoFix.LOUDNESS = self.get_level(level_str)

    def set_fix_level(self, level_str):
        AutoFix.FIX_LEVEL = self.get_level(level_str)

AUTO_FIXER = AutoFix()
