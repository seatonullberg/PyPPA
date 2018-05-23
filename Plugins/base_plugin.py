import pickle
from private_config import DATA_DIR
import os


class BasePlugin(object):

    def __init__(self, command, command_hook_dict, modifiers):
        self.COMMAND_HOOK_DICT = command_hook_dict
        self.MODIFIERS = modifiers
        self.command_dict = {'command_hook': '',
                             'premodifier': '',
                             'modifier': '',
                             'postmodifier': ''}
        # redefine self.command_dict
        self.command_parser(command)
        # check validity of command
        if self.command_dict['command_hook'] != '':
            self.acceptsCommand = True
        else:
            self.acceptsCommand = False
        # default to blocking
        self.isBlocking = True

    def command_parser(self, command):
        '''
        Process the user input to return a dict of command information
        - {'command_hook':str(), 'premodifier':str(), 'modifier':str(), 'postmodifier':str()}
        :return: None, redefines self.command_dict
        '''
        # get the command hook
        ch_range = (0, 0)
        for hook in self.COMMAND_HOOK_DICT:
            for spelling in self.COMMAND_HOOK_DICT[hook]:
                # find the first instance of a command hook
                ch_index = command.find(spelling)
                if ch_index == -1:
                    # the spelling is not in the command
                    continue
                else:
                    self.command_dict['command_hook'] = hook
                    ch_range = (ch_index, ch_index+len(spelling))
                    break
            # break the outer loop if the command hook is defined
            if self.command_dict['command_hook'] != '':
                break

        # get the premodifier, modifier, and postmodifier
        for mod in self.MODIFIERS[self.command_dict['command_hook']]:
            # these are the modifiers associated with the previously parsed command hook
            for spelling in self.MODIFIERS[self.command_dict['command_hook'][mod]]:
                # these are the spellings of the modifier
                mod_index = command.find(spelling)
                if mod_index == -1:
                    # the spelling is not in the command
                    # if theres no modifier treat everything after the command hook as premodifier
                    self.command_dict['premodifier'] = command[ch_range[1]:]
                    continue
                else:
                    self.command_dict['modifier'] = mod
                    self.command_dict['premodifier'] = command[ch_range[1]:mod_index]
                    self.command_dict['postmodifier'] = command[mod_index+len(spelling):]
                    break
            if self.command_dict['modifier'] != '':
                # break the outer loop if modifier is identified
                break

    def frame_data(self):
        '''
        Load the pickled dictionary of visual information produced by Watcher
        :return: dict(frame_data)
        '''
        frame_data_path = [DATA_DIR, 'public_pickles', 'frame_data.p']
        try:
            frame_data = pickle.load(open(os.path.join('', *frame_data_path), 'rb'))
        except FileNotFoundError:
            frame_data = None
        return frame_data

    def listener(self):
        '''
        Load the pickled listener object for use or modification
        :return: object listener
        '''
        listener_path = [DATA_DIR, 'public_pickles', 'listener.p']
        try:
            listener = pickle.load(open(os.path.join('', *listener_path)), 'rb')
        except FileNotFoundError:
            listener = None
        return listener

    # provide a name to overwrite for inter-plugin design symmetry
    def update_plugin(self, args=None):
        pass

    # provide a name to overwrite for inter-plugin design symmetry
    def function_handler(self, args=None):
        pass
