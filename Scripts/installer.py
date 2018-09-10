from tkinter import Tk, Button, StringVar, Label, OptionMenu, Entry
import os
from threading import Thread
import shutil
from collections import OrderedDict
import requests
import platform
import json


class InstallerGui(object):

    def __init__(self, master):
        self.master = master
        self.widgets = OrderedDict()
        self.string_var = None
        self.build()
        self.place()

    @property
    def https_host(self):
        return "https://pyppa.pythonanywhere.com/"

    def build(self):
        self.master.title('PyPPA Installer')
        self.master.geometry("250x190")     # width x height
        # label
        self.widgets['label'] = {}
        self.widgets['label']['version'] = Label(master=self.master, text="Select a version:")
        self.widgets['label']['destination'] = Label(master=self.master, text="Provide a destination path:")
        # optionmenu
        options = self.get_versions()
        self.string_var = StringVar(master=self.master)
        self.string_var.set(options[0])
        self.widgets['optionmenu'] = {}
        self.widgets['optionmenu']['version'] = OptionMenu(self.master, self.string_var, *options)
        # entry
        self.widgets['entry'] = {}
        self.widgets['entry']['destination'] = Entry(master=self.master, )
        self.widgets['entry']['destination'].insert(0, os.path.expanduser("~"))     # default is home directory
        # button
        self.widgets['button'] = {}
        self.widgets['button']['install'] = Button(master=self.master, text="Install", command=self.install)

    def place(self):
        x = 10
        y = 10
        # iterate in an orderly fashion
        ordered_widgets = [(self.widgets['label']['version'], 25),
                           (self.widgets['optionmenu']['version'], 60),
                           (self.widgets['label']['destination'], 25),
                           (self.widgets['entry']['destination'], 30),
                           (self.widgets['button']['install'], 0)]
        for w, i in ordered_widgets:
            w.place(x=x, y=y)
            y += i

    def get_versions(self):
        client_os = platform.system()
        r = requests.post(url=self.https_host + 'available_versions', data={'os': client_os})
        available_versions = json.loads(r.content)
        available_versions = [v.replace('.zip', '') for v in available_versions]
        return available_versions

    def install(self):
        v = self.string_var.get()
        d = self.widgets['entry']['destination'].get()
        # initialize the installation object and let it run automatically
        i = Installation(version=v, destination=d)
        i.build_destination()
        i.build_version()
        i.build_bin()
        exit()


class Installation(object):

    def __init__(self, version, destination, auto_build=False):
        '''
        An installation object to handle the transport of files from server to local machine
        :param version: (str) the version id of the desired installation
        :param destination: (str) the filepath where the /PyPPA/ directory will be built on the local machine
        '''
        self._version = version
        self._destination = destination
        if auto_build:
            self.build_destination()
            self.build_version()
            self.build_bin()

    @property
    def version(self):
        return self._version

    @property
    def destination(self):
        return self._destination

    @property
    def https_host(self):
        return "https://pyppa.pythonanywhere.com/"

    def build_destination(self):
        try:
            os.makedirs(self.destination)
        except FileExistsError:
            print("Path exists, proceeding to install...")
        else:
            print("Created path: {}".format(self.destination))

    def build_version(self):
        # fetch the version zip
        localpath = os.path.join(self.destination, "{}.zip".format(self.version))
        print("Collecting {}...".format(self.version))
        self._fetch_version(localpath)

        # unzip the version zip
        unpackpath = os.path.join(self.destination, self.version)
        print("Unzipping {}...".format(self.version))
        shutil.unpack_archive(localpath, unpackpath)

        print("Cleaning {}...".format(self.version))
        # delete old version zip
        os.remove(localpath)

        # move files out of Core/
        corepath = os.path.join(self.destination, self.version, 'Core')
        for f in os.listdir(corepath):
            srcpath = os.path.join(corepath, f)
            assert os.path.isfile(srcpath)
            destpath = os.path.join(self.destination, self.version, f)
            shutil.move(srcpath, destpath)

        # delete empty Core/
        shutil.rmtree(corepath)

    def _fetch_version(self, localpath):
        r = requests.post(url=self.https_host + 'install_version', data={'version': self.version}, stream=True)
        with open(localpath, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)

    def build_bin(self):
        # read the bin/resources.txt file
        resourcespath = os.path.join(self.destination, self.version, 'bin', 'resources.txt')
        with open(resourcespath, 'r') as f:
            resources = f.readlines()
            resources = [r.replace('\n', '') for r in resources]

        # load the required resources
        localpath = os.path.join(self.destination, self.version, 'bin', '{}')
        threads = []
        for r in resources:
            # r is a directory which contains one or more zip files
            t = Thread(target=self._fetch_resource, args=(localpath.format(r),))
            threads.append(t)
            t.start()

        # wait to finish downloading
        for t in threads:
            t.join()

    def _fetch_resource(self, localpath):
        dirname = os.path.basename(localpath)
        # return list of files in the specified directory
        r = requests.post(url=self.https_host+'check_resource', data={'dirname': dirname}, stream=True)
        resource_files = json.loads(r.content)
        # process files sequentially for now
        for filename in resource_files:
            r = requests.post(url=self.https_host+'install_resource', data={'filename': filename}, stream=True)
            with open(localpath, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            # then need to unzip


if __name__ == "__main__":
    root = Tk()
    InstallerGui(root)
    root.mainloop()
