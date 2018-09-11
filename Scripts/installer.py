from tkinter import Tk, Button, StringVar, Label, OptionMenu, Entry
import os
from threading import Thread
import shutil
from collections import OrderedDict
import requests
import platform
import json
from tqdm import tqdm
import sys


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
        print("Installation complete!")
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
        self.pm = None  # ProgressMonitor object
        if auto_build:
            self.build_destination()
            self.build_version()
            self.build_bin()
            # add automatic chmod
            # -- use proposed autoconfig?

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
        resourcepath = os.path.join(self.destination, self.version, 'bin', 'resources.txt')
        with open(resourcepath, 'r') as f:
            resources = f.readlines()
            resources = [r.replace('\n', '') for r in resources]

        # prepare the monitor
        self.pm = ProgressMonitor(resourcepath=resourcepath,
                                  host=self.https_host)
        monitor_thread = Thread(target=self.pm.monitor)
        monitor_thread.start()

        # load the required resources
        localpath = os.path.join(self.destination, self.version, 'bin', '{}')
        threads = []
        for r in resources:
            # r is a directory which contains one or more zip files
            t = Thread(target=self._fetch_resource, args=(localpath.format(r),))
            threads.append(t)
            t.start()

        # wait until all downloaded
        monitor_thread.join()
        # add bin path to system so python can import
        sys.path.append(os.path.dirname(localpath))

    def _fetch_resource(self, localpath):
        dirname = os.path.basename(localpath)
        # return list of files in the specified directory
        r = requests.post(url=self.https_host+'check_resource',
                          data={'dirname': dirname},
                          stream=True)
        d = json.loads(r.content)

        # spawn threads to process each file
        threads = []
        for filename in d:
            _localpath = os.path.join(localpath, filename)
            t = Thread(target=self._process_resource, args=(dirname, filename, _localpath))
            threads.append(t)
            t.start()

    def _process_resource(self, dirname, filename, localpath):
        '''
        download -> unzip -> delete zip
        :param dirname: parent directory of the resource file
        :param filename: name of the resource file
        :param localpath: path to store the file locally
        :return:
        '''

        # download individual file
        print("Downloading {d}/{f}...".format(d=dirname, f=filename))
        r = requests.post(url=self.https_host+'install_resource',
                          data={'filename': filename,
                                'dirname': dirname},
                          stream=True)
        # check if directory exists
        if not os.path.isdir(os.path.dirname(localpath)):
            os.makedirs(os.path.dirname(localpath))
        with open(localpath, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)

        # unzip individual file
        print("Unzipping {d}/{f}...".format(d=dirname, f=filename))
        # go back 2 levels
        unpackpath = os.path.dirname(localpath)
        unpackpath = os.path.dirname(unpackpath)
        try:
            shutil.unpack_archive(localpath, unpackpath)
        except IsADirectoryError:
            raise
        except shutil.ReadError:
            print("Error encountered while downloading {d}/{f}".format(d=dirname, f=filename))
            print("Attempting to download {d}/{f} again...".format(d=dirname, f=filename))
            self.pm.retry_list.append(localpath)  # notify the progress monitor that a retry has occurred
            os.remove(localpath)
            self._process_resource(dirname, filename, localpath)
            return
        # delete the old zip file
        print("Removing {d}/{f}...".format(d=dirname, f=filename))
        os.remove(localpath)
        if localpath in self.pm.retry_list:
            self.pm.retry_list.remove(localpath)


class ProgressMonitor(object):

    def __init__(self, resourcepath, host):
        self._resourcepath = resourcepath
        self.host = host
        self.resource_dict = {}
        self._init_resource_dict()
        self.pbar = tqdm(total=self.total_bytes, unit='bytes')
        self._progress = 0
        self.retry_list = []

    @property
    def resourcepath(self):
        return self._resourcepath

    @property
    def binpath(self):
        return os.path.dirname(self.resourcepath)

    @property
    def progress(self):
        return self._progress

    @property
    def resource_names(self):
        with open(self.resourcepath, 'r') as f:
            names = f.readlines()
            names = [n.replace('\n', '') for n in names]
        return names

    def _init_resource_dict(self):
        for name in self.resource_names:
            r = requests.post(url=self.host+'check_resource',
                              data={'dirname': name},
                              stream=True)
            d = json.loads(r.content)
            self.resource_dict[name] = d

    @property
    def total_bytes(self):
        total = 0
        for name in self.resource_dict:
            for filename in self.resource_dict[name]:
                size = self.resource_dict[name][filename]['size']
                total += size
        return total

    def is_active(self):
        # returns false only when all entries in self.resource_dict
        # show status: complete
        complete_count = 0
        all_files = []
        for name in self.resource_dict:
            for filename in self.resource_dict[name]:
                filepath = os.path.join(self.binpath, name, filename)
                all_files.append(filepath)
                d = self.resource_dict[name][filename]
                if d['status'] == 'complete':
                    complete_count += 1
        if complete_count < len(all_files):
            return True
        else:
            return False

    def was_retried(self, filepath):
        if filepath in self.retry_list:
            return True
        else:
            return False

    def monitor(self):
        while self.is_active():
            loop_progress = 0
            for name in self.resource_dict:
                for filename in self.resource_dict[name]:
                    filepath = os.path.join(self.binpath, name, filename)
                    d = self.resource_dict[name][filename]
                    if d['status'] is None:
                        # never before encountered
                        # check to see if it exists yet
                        if os.path.isfile(filepath):
                            # activate
                            d['status'] = 'active'
                            # update progress
                            current_size = os.path.getsize(filepath)
                            loop_progress += (current_size - d['last_size'])
                            d['last_size'] = current_size
                    elif d['status'] == 'active':
                        # previously encountered
                        # check to see if it still exists
                        if os.path.isfile(filepath):
                            # update the progress
                            try:
                                current_size = os.path.getsize(filepath)
                            except FileNotFoundError:
                                # the file was deleted immediately after the if statement
                                current_size = d['size']
                            loop_progress += (current_size - d['last_size'])
                            d['last_size'] = current_size
                        else:
                            # file completed downloading or was retried
                            if self.was_retried(filepath):
                                # the program is attempting to reinstall the file
                                d['status'] = None
                                d['last_size'] = 0
                            else:
                                # the download completed successfully
                                d['status'] = 'complete'
                                print("Completed: {}".format(filename))
            self._progress += loop_progress
            self.pbar.update(loop_progress)


if __name__ == "__main__":
    root = Tk()
    InstallerGui(root)
    root.mainloop()
