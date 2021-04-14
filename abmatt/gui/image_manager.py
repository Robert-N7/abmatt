import os
import shutil
import uuid
from time import sleep

from PyQt5.QtCore import QObject, pyqtSignal, QRunnable, pyqtSlot
from PyQt5.QtGui import QPixmap

from abmatt.autofix import AutoFix
from abmatt.brres.lib.node import ClipableObserver
from abmatt.brres.tex0 import Tex0
from abmatt.image_converter import ImgConverter, ImgConverterI, DecodeError


class ImageObserver:
    def on_image_update(self, dir):
        raise NotImplementedError()


class ImageHandler:
    def subscribe(self, obj, brres):
        """Subscribes for updates for the corresponding brres"""
        raise NotImplementedError()

    def unsubscribe(self, obj, brres):
        raise NotImplementedError()

    def notify_image_observers(self, brres, dir):
        raise NotImplementedError()


class ImageSignals(QObject):
    """
    Interface to get notifications from image manager
    Sends tuple of corresponding brres and dir path
    (brres, dir)
    """
    on_image_update = pyqtSignal(tuple)


class ImageManager(QRunnable, ClipableObserver, ImageHandler):
    """
    Manages decoding tex0s into png files to be used, has its own thread
    """

    __INSTANCE = None

    @staticmethod
    def get():
        if ImageManager.__INSTANCE is None:
            ImageManager.__INSTANCE = ImageManager()
        return ImageManager.__INSTANCE

    def subscribe(self, obj, brres, tex0_name=None):
        key = self.__get_brres_key(brres)
        updater = self.image_updater.get(key)
        if not updater:
            self.image_updater[key] = [obj]
        elif obj not in updater:
            updater.append(obj)
        if brres not in self.queue:
            dir = self.brres_to_folder.get(key)
            # if not found...
            if not dir:
                self.enqueue(brres)
            elif tex0_name is not None and not os.path.exists(os.path.join(dir, tex0_name + '.png')):
                self.__enqueue(brres)
            else:
                obj.on_image_update(dir)    # sends out immediate update

    def unsubscribe(self, obj, brres):
        key = self.__get_brres_key(brres)
        updater = self.image_updater.get(key)
        if updater:
            try:
                updater.remove(obj)
                # No more objects to update?
                if len(updater) <= 0:
                    brres.unregister(self)
            except ValueError:
                pass

    @staticmethod
    def stop():
        if ImageManager.__INSTANCE is not None:
            ImageManager.__INSTANCE.enabled = False
            ImageManager.__INSTANCE = None
            # ImageManager.__INSTANCE.wait()
            # ImageManager.__INSTANCE.thread.join()

    def is_done(self):
        return self.is_ready

    # def subscribe(self, obj, brres):
    #     li = self.image_updater.get(brres.name)
    #     if not li:
    #         self.image_updater[brres.name] = [obj]
    #     else:
    #         li.append(obj)
    #
    # def unsubscribe(self, obj, brres):
    #     li = self.image_updater.get(brres.name)
    #     if li:
    #         li.remove(obj)

    def notify_image_observers(self, brres, directory):
        li = self.image_updater.get(self.__get_brres_key(brres))
        if li:
            for x in li:
                x.on_image_update(directory)

    @pyqtSlot()
    def run(self):
        try:
            AutoFix.get().info('Started image manager...', 5)
            self.__clean()
            while self.enabled:
                if len(self.queue):
                    self.__decode_brres_images(self.queue.pop(0))
                else:
                    self.is_ready = True
                sleep(0.3)
        except:
            AutoFix.get().exception(shutdown=True)

    def __enqueue(self, brres):
        if brres not in self.queue:
            self.queue.append(brres)
        self.is_ready = False

    def enqueue(self, brres):
        if self.enabled and not self.get_image_dir(brres):
            brres.register_observer(self)
            self.__enqueue(brres)
            return True
        return False

    def get_image_dir(self, brres):
        return self.brres_to_folder.get(self.__get_brres_key(brres))

    def get_image_path(self, tex0):
        dir = self.get_image_dir(tex0.parent)
        if dir:
            file = os.path.join(dir, tex0.name + '.png')
            if os.path.exists(file):
                return file

    def __decode_brres_images(self, brres):
        name = self.__get_brres_key(brres)
        folder_name = self.brres_to_folder.get(name)
        if not folder_name:
            self.brres_to_folder[name] = folder_name = self.__get_unique_folder_name()
        else:
            shutil.rmtree(folder_name, ignore_errors=True)
        try:
            ImgConverter().batch_decode(brres.textures, folder_name)
            self.signals.on_image_update.emit((brres, folder_name))
        except DecodeError as e:
            AutoFix.get().exception(e)

    def __get_unique_folder_name(self):
        return os.path.join(self.tmp_dir, str(uuid.uuid4()))

    # def __load_config(self):
    #     if os.path.exists(self.cfg_file):
    #         with open(self.cfg_file) as f:
    #             self.brres_to_folder = json.loads(f.read())

    # def __write_config(self):
    #     with open(self.cfg_file) as f:
    #         f.write(json.dumps(self.brres_to_folder))

    def __clean(self):
        folder = self.tmp_dir
        if os.path.exists(folder):
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except OSError as e:
                    pass
        else:
            os.mkdir(self.tmp_dir)

    # def __on_update_brres_images(self, brres_key, dir):
    #     updater = self.updater.get(brres_key)
    #     if updater:
    #         for x in updater:
    #             x.on_image_update(dir)

    @staticmethod
    def __get_brres_key(brres):
        return os.path.abspath(brres.name)

    def on_node_update(self, node):
        self.__enqueue(node)

    def on_child_update(self, child):
        if type(child) == Tex0:
            self.__enqueue(child.parent)  # decode again

    def __init__(self):
        if self.__INSTANCE:
            raise RuntimeError('Already initialized!')
        ImageManager.__INSTANCE = self
        super().__init__()
        self.brres_to_folder = {}
        self.is_ready = True
        self.tmp_dir = ImgConverterI.TMP_DIR
        self.enabled = True if self.tmp_dir is not None else False
        self.queue = []
        self.signals = ImageSignals()
        self.image_updater = {}
        # if self.enabled:
        #     self.thread = Thread(target=self.run)
        #     self.thread.start()
        # self.cfg_file = os.path.join(self.tmp_dir, 'brres_to_folder.txt')
        # self.__load_config()


def update_image(widget, dir, name, scale_width=64):
    if name is not None:
        img_file = os.path.join(dir, name + '.png')
        if os.path.exists(img_file):
            pixelmap = QPixmap(img_file)
            width = pixelmap.width()
            height = pixelmap.height()
            if width > height:
                pixelmap = pixelmap.scaledToWidth(scale_width)
            else:
                pixelmap = pixelmap.scaledToHeight(scale_width)
            widget.setPixmap(pixelmap)
            widget.setMask(pixelmap.mask())
            return True
    widget.clear()
    return False