# !/usr/bin/env python
from threading import Thread
from time import sleep

from PyQt5.QtWidgets import QMessageBox, QLineEdit, QApplication
from PyQt5.QtGui import QIcon

from autofix import AutoFix


class ConvertObserver:
    def on_conversion_finish(self, converter):
        raise NotImplementedError()


class ConvertManager:
    __INSTANCE = None

    @staticmethod
    def get():
        if ConvertManager.__INSTANCE is None:
            ConvertManager.__INSTANCE = ConvertManager()
        return ConvertManager.__INSTANCE

    def __init__(self):
        if self.__INSTANCE is not None:
            raise RuntimeError('Convert Manager already initialized!')
        self.queue = []
        self.observers = []
        self.thread = Thread(target=self.run)
        self.is_running = True
        self.item = None
        self.thread.start()

    def subscribe(self, obj):
        if obj not in self.observers:
            self.observers.append(obj)

    def unsubscribe(self, obj):
        if obj in self.observers:
            self.observers.remove(obj)

    def enqueue(self, converter):
        if converter == self.item:
            AutoFix.get().error('Conversion already in progress!')
            return False
        for x in self.queue:
            if x == converter:
                AutoFix.get().error('Conversion already in progress!')
                return False
        self.queue.append(converter)
        return True

    @staticmethod
    def stop():
        manager = ConvertManager.__INSTANCE
        if manager:
            manager.is_running = False
            manager.thread.join()

    def run(self):
        while True:
            if len(self.queue):
                self.item = self.queue.pop(0)
                self.item.convert()
                for x in self.observers:
                    x.on_conversion_finish(self.item)
            if not self.is_running:
                break
            sleep(0.2)
