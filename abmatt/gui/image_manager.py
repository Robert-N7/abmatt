import os
import shutil
import uuid
from threading import Thread
from time import sleep

from PyQt5.QtGui import QPixmap

from brres import Brres
from brres.lib.node import ClipableObserver
from brres.tex0 import ImgConverter, Tex0


class ImageObserver:
    """
    Interface to get notifications from image manager
    """

    def on_image_update(self, directory):
        raise NotImplementedError()


class ImageManager(ClipableObserver):
    """
    Manages decoding tex0s into png files to be used, has its own thread
    """

    __INSTANCE = None

    @staticmethod
    def get():
        if ImageManager.__INSTANCE is None:
            ImageManager.__INSTANCE = ImageManager()
        return ImageManager.__INSTANCE

    def subscribe(self, obj, brres):
        key = self.__get_brres_key(brres)
        if brres not in self.queue:
            dir = self.brres_to_folder.get(key)     # we haven't processed it!
            if not dir:
                self.__enqueue(brres)
            else:
                obj.on_image_update(dir)    # sends out immediate update
        updater = self.updater.get(key)
        if not updater:
            self.updater[key] = [obj]
        elif obj not in updater:
            updater.append(obj)

    def unsubscribe(self, obj, brres):
        key = self.__get_brres_key(brres)
        updater = self.updater.get(key)
        if updater:
            updater.remove(obj)

    @staticmethod
    def stop():
        if ImageManager.__INSTANCE is not None:
            ImageManager.__INSTANCE.enabled = False
            ImageManager.__INSTANCE.thread.join()

    def is_done(self):
        return self.is_ready

    def run(self):
        self.__clean()
        while self.enabled:
            if len(self.queue):
                self.__decode_brres_images(self.queue.pop(0))
            else:
                self.is_ready = True
            sleep(0.3)

    def __enqueue(self, brres):
        self.queue.append(brres)
        self.is_ready = False

    def enqueue(self, brres):
        if self.enabled and not self.get_image_dir(brres):
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
        ImgConverter().batch_decode(brres.textures, folder_name)
        self.__on_update_brres_images(name, folder_name)

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

    def __on_update_brres_images(self, brres_key, dir):
        updater = self.updater.get(brres_key)
        if updater:
            for x in updater:
                x.on_image_update(dir)

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
        self.brres_to_folder = {}
        self.is_ready = True
        self.tmp_dir = Brres.TEMP_DIR
        self.enabled = True if self.tmp_dir is not None else False
        self.queue = []
        self.updater = {}
        if self.enabled:
            self.thread = Thread(target=self.run)
            self.thread.start()
        # self.cfg_file = os.path.join(self.tmp_dir, 'brres_to_folder.txt')
        # self.__load_config()


def update_image(widget, dir, name, scale_width=64):
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