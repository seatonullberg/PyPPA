from data.facial_profiles.facial_profile import FacialProfile
from Speaker import vocalize
import pickle
import os
from private_config import DATA_DIR


class PyPPA_WatcherPlugin(object):

    def __init__(self, command):
        self.command = command
        self.COMMAND_HOOK_DICT = {'scan_faces': ['scan for faces', 'scan for face', 'stand for faces', 'stand for face',
                                                 'scan faces', 'scan face']}
        # This is atypical use of the FUNCTION_KEY_DICT
        # Here use it for direct (unspoken) commands from Watcher
        # spoken commands handled fully by COMMAND_HOOK_DICT
        self.FUNCTION_KEY_DICT = {'greet': self.greet}
        self.isBlocking = True
        self.obj_facial_profile = FacialProfile()

    # the additional argument typically used for the spelling is designated as args_dict for the direct command
    # therefore, no user spoken query type commands can be executed with this Plugin
    def function_handler(self, command_hook, args_dict):
        if command_hook == 'scan_faces':
            self.scan_faces()
        # if the command was passed directly from Watcher
        elif command_hook in self.FUNCTION_KEY_DICT:
            # execute the desired command
            self.FUNCTION_KEY_DICT[command_hook](args_dict)

    def update_database(self):
        pass

    def scan_faces(self):
        # load the list of most recently detected faces
        faces_path = [DATA_DIR, 'facial_profiles', 'archived_faces.p']
        faces = pickle.load(open(os.path.join('', *faces_path), 'rb'))
        for f in faces:
            # if the detected face has no name (not previously recognized)
            if f['name'] is "Unknown":
                # write profile for new face
                self.obj_facial_profile.write_profile({'encoding': f['encoding'],
                                                       'name': 'Unspecified',
                                                       'image': f['image']})
        self.isBlocking = False

    def greet(self, args_dict):
        vocalize(args_dict['greeting'])
