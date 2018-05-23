'''
Use this plugin strictly for tasks with visual cues that are not related to any other plugin
- mostly utility type stuff
'''

from Speaker import vocalize
import pickle
import os
from private_config import DATA_DIR
from Plugins.base_plugin import BasePlugin
from facial_profile import FacialProfile


# TODO: add subroutines to FacialProfiles for more activity
class PyPPA_WatcherPlugin(BasePlugin):

    def __init__(self, command):
        self.obj_facial_profile = FacialProfile()
        self.COMMAND_HOOK_DICT = {'scan_faces': ['scan for faces', 'scan for face', 'stand for faces', 'stand for face',
                                                 'scan faces', 'scan face']}
        self.MODIFIERS = {'scan_faces': {}}
        super().__init__(command=command,
                         command_hook_dict=self.COMMAND_HOOK_DICT,
                         modifiers=self.MODIFIERS)

    def function_handler(self, args=None):
        # also not robust to expansion yet
        if self.command_dict['command_hook'] == 'scan_faces':
            self.scan_faces()
        else:
            # for args sent directly from Watcher
            # will send a name and any args to include with function call
            if args[0] == 'greet':
                self.greet(args[1])

    def scan_faces(self):
        # load the data from the most recent frame
        data_path = [DATA_DIR, 'public_pickles', 'frame_data.p']
        data = pickle.load(open(os.path.join('', *data_path), 'rb'))
        for name, encoding, image in zip(data['face_names'], data['face_encodings'], data['images']):
            # if the detected face has no name (not previously recognized)
            if name == "Unknown":
                # write profile for new face
                self.obj_facial_profile.write_profile({'encoding': encoding,
                                                       'name': 'Unspecified',
                                                       'image': image})
        self.isBlocking = False

    def greet(self, args_dict):
        vocalize(args_dict['greeting'])
