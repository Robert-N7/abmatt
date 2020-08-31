"""Debugging and fixing"""


class Bug:
    # bug levels
    # None 0
    # Errors 1
    # Warnings 2
    # Checks 3
    # Suggest 4
    # Prompt 5
    # notify levels, 0 silent, 1 quiet, 2 mid, 3 loud, 4 max, 5 debug
    def __init__(self, bug_level, notify_level, description, fix_des=None):
        self.bug_level = bug_level
        self.notify_level = notify_level        # lower numbers mean notify when quiet
        self.description = description
        self.fix_des = fix_des
        self.is_resolved = False
        AUTO_FIXER.notify(self)

    # def should_fix(self):
    #     return not self.is_resolved and AUTO_FIXER.should_fix(self)

    def resolve(self):
        self.is_resolved = True
        if AUTO_FIXER.loudness >= self.notify_level:
            print('(FIXED): {}'.format(self.fix_des))


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
    # Suggest 4
    # Prompt 5
    FIX_PROMPT = 5

    # Loudness levels, 0 silent, 1 quiet, 2 mid, 3 loud, 4 max, 5 debug
    LOUD_LEVELS = ('SILENT', 'QUIET', 'MID', 'LOUD', 'MAX', 'DEBUG')
    ERROR_LEVELS = ('NONE', 'ERROR', 'WARN', 'CHECK', 'SUGGEST', 'PROMPT')
    RESULTS = ('NONE', 'ERROR', 'WARN', 'CHECK', 'SUCCESS')

    def __init__(self, fix_level=3, loudness=3):
        self.loudness = loudness
        self.fix_level = fix_level

    def set_fix_level(self, fix_level):
        try:
            self.fix_level = int(fix_level)
        except ValueError:
            fix_level = fix_level.upper()
            if fix_level == 'ALL':
                self.fix_level = 4
            else:
                self.fix_level = self.ERROR_LEVELS.index(fix_level)

    def can_prompt(self):
        return self.fix_level == self.FIX_PROMPT

    def log(self, message):
        if self.loudness >= 5:
            print(message)

    def info(self, message, loudness=2):
        if self.loudness >= loudness:
            print('INFO: {}'.format(message))

    def warn(self, message, loudness=2):
        if self.loudness >= loudness:
            print('WARN: {}'.format(message))

    def error(self, message, loudness=1):
        print('ERROR: {}'.format(message))

    # def should_fix(self, bug):
    #     """Determines if a bug should be fixed"""
    #     fix_level = self.fix_level
    #     if fix_level >= bug.bug_level:
    #         should_fix = True
    #         if fix_level == self.FIX_PROMPT:
    #             should_fix = self.prompt(bug.description, bug.fix_des)
    #         if should_fix:
    #             if self.loudness >= bug.notify_level:
    #                 print('FIX: {}'.format(bug.description))
    #             return True
    #     self.notify(bug)
    #     return False

    @staticmethod
    def prompt(description, proposed_fix=None):
        while True:
            result = input('Fix: ' + description + ',' + proposed_fix + '? (y/n)').lower()
            if result[0] == 'y':
                return 1
            elif result[0] == 'n':
                return 0
            elif result[0] == 'a':  # abort option
                raise AutoFixAbort()
            else:
                print('Invalid response, expects yes, no, or abort.')

    def display_result(self, bug, result_level=4, result_message=None):
        if self.loudness >= bug.notify_level:
            if result_message:
                print('(' + self.RESULTS[result_level] + ') ' + result_message)
            else:
                print('(' + self.RESULTS[result_level] + ') ' + bug.fix_des)

    def notify(self, bug):
        """Notifies of a bug check"""
        if self.loudness >= bug.notify_level:
            print('{}: {}'.format(self.ERROR_LEVELS[bug.bug_level], bug.description))

    def get_level(self, level_str):
        """Expects level to be a string, as a number or one of the Error levels"""
        try:
            level = int(level_str)
            if not 0 <= level < 6:
                raise ValueError('Loudness level out of range (0-6)')
            return int(level)
        except ValueError:
            level_str = level_str.upper()
            if level_str == 'ALL':
                return 4
            return self.LOUD_LEVELS.index(level_str)

    def set_loudness(self, level_str):
        self.loudness = self.get_level(level_str)


AUTO_FIXER = AutoFix()
