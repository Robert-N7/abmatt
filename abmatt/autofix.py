"""Debugging and fixing"""
from threading import Thread
from time import sleep

from colorama import init
init()

class bcolors:
    HEADER = '\033[35m'
    OKBLUE = '\033[34m'
    OKGREEN = '\033[32m'
    WARNING = '\033[33m'
    FAIL = '\033[31m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


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
        AutoFix.get().notify(self)

    # def should_fix(self):
    #     return not self.is_resolved and AutoFix.get().should_fix(self)

    def resolve(self):
        self.is_resolved = True
        AutoFix.get().info(f'(FIXED): {self.fix_des}', self.notify_level)


class AutoFixAbort(BaseException):
    """Raised by prompt"""
    def __init__(self):
        super(AutoFixAbort, self).__init__('Operation aborted')

class Message:
    def __init__(self, message):
        self.message = message

    def send(self, pipe):
        raise NotImplementedError()


class AutoFix:
    # Fix Level
    # None 0
    # Errors 1
    # Warnings 2
    # Checks 3
    # Suggest 4
    # Prompt 5
    FIX_PROMPT = 5
    __AUTO_FIXER = None

    # Loudness levels, 0 silent, 1 quiet, 2 mid, 3 loud, 4 max, 5 debug
    LOUD_LEVELS = ('SILENT', 'QUIET', 'MID', 'LOUD', 'MAX', 'DEBUG')
    ERROR_LEVELS = (bcolors.ENDC, bcolors.FAIL, bcolors.FAIL, bcolors.OKBLUE, bcolors.OKBLUE, bcolors.BOLD)
    RESULTS = ('NONE', 'ERROR', 'WARN', 'CHECK', 'SUCCESS')

    class Info(Message):
        def send(self, pipe):
            message = self.message
            print(message)
            if pipe:
                pipe.info(message)

    class Warn(Message):
        def send(self, pipe):
            message = self.message
            print(f'{bcolors.FAIL}WARN: {message}{bcolors.ENDC}')
            if pipe:
                pipe.warn(message)

    class Error(Message):
        def send(self, pipe):
            message = self.message
            print(f'{bcolors.FAIL}ERROR: {message}{bcolors.ENDC}')
            if pipe:
                pipe.error(message)


    def __init__(self, fix_level=3, loudness=3):
        if(self.__AUTO_FIXER): raise RuntimeError('Autofixer already initialized')
        self.loudness = loudness
        self.fix_level = fix_level
        self.queue = []
        self.is_running=True
        self.pipe = None        # if set, output is sent to the pipe, must implement info warn and error.
        self.thread = Thread(target=self.run)
        self.thread.start()

    def run(self):
        while self.is_running:
            while len(self.queue):
                message = self.queue.pop(0)
                message.send(self.pipe)
            sleep(0.1)

    def enqueue(self, message):
        self.queue.append(message)

    @staticmethod
    def get(fixe_level=3, loudness=3):
        if AutoFix.__AUTO_FIXER is None:
            AutoFix.__AUTO_FIXER = AutoFix(fixe_level, loudness)
        return AutoFix.__AUTO_FIXER

    def set_pipe(self, obj):
        self.pipe = obj

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
            self.enqueue(self.Info(message))

    def info(self, message, loudness=2):
        if self.loudness >= loudness:
            self.enqueue(self.Info(message))

    def warn(self, message, loudness=2):
        if self.loudness >= loudness:
            self.enqueue(self.Warn(message))

    def error(self, message, loudness=1):
        if self.loudness >= loudness:
            self.enqueue(self.Error(message))

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
                result_message = '(' + self.RESULTS[result_level] + ') ' + result_message
            else:
                result_message = '(' + self.RESULTS[result_level] + ') ' + bug.fix_des
            self.info(result_message, 0)

    def notify(self, bug):
        """Notifies of a bug check"""
        if self.loudness >= bug.notify_level:
            self.info(bug.description, 0)

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

