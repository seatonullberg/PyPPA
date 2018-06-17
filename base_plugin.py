import pickle
import os
import socketserver
import socket
import time
import copy
import multiprocessing
from threading import Thread


class BasePlugin(object):

    def __init__(self, command_hook_dict, modifiers, name):
        self.COMMAND_HOOK_DICT = command_hook_dict
        self.MODIFIERS = modifiers
        self.name = name
        self.command_dict = {'command_hook': '',
                             'premodifier': '',
                             'modifier': '',
                             'postmodifier': ''}
        # can be used by other functions as a test
        self.acceptsCommand = False
        # inform the plugin of its active status
        self.isActive = False
        # store server to be able to shut it down
        self.server = None
        # store any commands coming by message here to access in mainloop
        self.incoming_command = None

    '''
    -------------------------------------------------
    General use functions for normal Plugin operation
    -------------------------------------------------
    '''
    def mainloop(self, cmd=None):
        '''
        The loop which keeps the plugin alive until an explicit termination call is made
        through self.pass_and_terminate()
        * call every time a new plugin is initialized
            - make sure this is only called once over the life of the process
        * note that while every plugin must be initialized with this function
          plugins are free to control calls to the function handler themselves
          this just sets a standard for basic control
        :param cmd: initial input command to use for direct execution of prerecorded command
        :return: None
        '''
        while True:
            self.reset_command_dict()
            if self.isActive:
                if cmd is None:
                    cmd = self.listener.listen_and_convert()
                if self.incoming_command is not None:
                    cmd = copy.deepcopy(self.incoming_command)
                    self.incoming_command = None
                print("mainloop cmd={}".format(cmd))
                self.command_parser(cmd)
                self.function_handler()
            else:
                time.sleep(0.5)
            # reset if there was an initial cmd so as not to repeat the same command
            cmd = None

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

        # if command contains a recognized command hook then the command is considered acceptable
        if self.command_dict['command_hook'] == '':
            self.acceptsCommand = False
            return
        else:
            self.acceptsCommand = True

        # get the premodifier, modifier, and postmodifier
        for mod in self.MODIFIERS[self.command_dict['command_hook']]:
            # these are the modifiers associated with the previously parsed command hook
            for spelling in self.MODIFIERS[self.command_dict['command_hook']][mod]:
                # these are the spellings of the modifier
                mod_index = command.find(spelling)
                if mod_index == -1:
                    # the spelling is not in the command
                    continue
                else:
                    self.command_dict['modifier'] = mod
                    self.command_dict['premodifier'] = command[ch_range[1]+1:mod_index]
                    self.command_dict['postmodifier'] = command[mod_index+len(spelling)+1:]
                    # the +1 is to cover the inevitable space after word
                    break
            if self.command_dict['modifier'] != '':
                # break the outer loop if modifier is identified
                break

        # if there is no modifier detected, use everything after the command hook as premodifier
        if self.command_dict['modifier'] == '':
            self.command_dict['premodifier'] = command[ch_range[1]+1:]

    def function_handler(self, args=None):
        # use args in special use cases where this general behavior needs to be overwritten
        print("finction_handler command_dict={}".format(self.command_dict))
        if self.command_dict['command_hook'] in dir(self):
            func = getattr(self, self.command_dict['command_hook'])
            # run the collected function with no args
            func()
            # if function is available return error code 0
            err_code = 0
        else:
            # if the function is not available return error code 1
            err_code = 1
        return err_code

    def reset_command_dict(self):
        # call this between the processing of multiple commands
        self.command_dict = {'command_hook': '',
                             'premodifier': '',
                             'modifier': '',
                             'postmodifier': ''}
        self.acceptsCommand = None

    def make_active(self):
        # prepares the plugin for active use
        self.isActive = True
        # start a server only if one does not exist yet
        if self.server is None:
            # start server on own port
            _port = self.config_obj.port_map[self.name]
            thread_name = "{}_server_thread".format(self.name)
            Thread(target=self.start_server, args=(_port,), name=thread_name).start()

    # provide namespace to overwrite for design symmetry
    def update_plugin(self, args=None):
        pass

    '''
    ----------------------------------------------
    Client and Server threads for message handling
    ----------------------------------------------
    '''

    def send_message(self, data, port, host='localhost'):
        '''
        Call with data whenever a message needs to be sent out to a server
        :param port: int() TCP Port to send message to (get from config port_map)
        :param host: str() default 'localhost' for TCP connection
        :param data: str() the message being sent
        :return: None
        '''
        # Create a socket (SOCK_STREAM means a TCP socket)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            # Connect to server and send data
            sock.connect((host, port))
            sock.sendall(bytes(data, "utf-8"))
            sock.close()
        print("send_message sent data={}".format(data))

    def start_server(self, port, host='localhost'):
        '''
        Creates the listening server socket for the plugin to get messages
        :param port: int() TCP Port to serve (get from config port_map)
        :param host: str() default 'localhost' for TCP connection
        :return: None (redirects messages to self.handle_server_message)
        '''
        tcps = TCPServer(host, port, TCPHandler)
        with tcps as server:
            # grant access to server from entire class (allow shutdown outside thread)
            self.server = server
            # add reference to plugin for handler
            server.plugin = self
            # Activate the server; run until explicit shutdown
            server.serve_forever()

    def handle_server_message(self, data):
        # messages are formatted as follows:
        # clientA sends -> "b_plugin$this is a command" -> to serverB
        data = data.decode("utf-8")
        name, comm = data.split('$')
        if name == self.name:
            # make self ready for activity and let mainloop process the command
            self.incoming_command = comm
            self.make_active()
        print("handle_server_message data={}".format(data))
    '''
    ---------------------------------------------------------
    Methods for gracefully shifting control to another plugin
    ---------------------------------------------------------
    '''
    def pass_and_remain(self, name, cmd):
        # issue control to another plugin but remain active in background
        self.isActive = False
        port = self.config_obj.port_map[name]
        message_str = "{n}${c}".format(n=name,
                                       c=cmd)
        self.send_message(data=message_str,
                          port=port)

    def pass_and_terminate(self, name, cmd):
        # issue control to another plugin and self terminate subsequently
        self.isActive = False
        port = self.config_obj.port_map[name]
        message_str = "{n}${c}".format(n=name,
                                       c=cmd)
        self.send_message(data=message_str,
                          port=port)
        # kill the server
        if self.server is not None:
            self.server.shutdown()
        # kill the process
        print(multiprocessing.current_process())
        multiprocessing.current_process().terminate()
        print('successful process termination')

    '''
    -------------------------------------------------------------------------
    Properties used to conveniently load the configuration and public pickles
    -------------------------------------------------------------------------
    '''
    @property
    def config_obj(self):
        '''
        Load the configuration data into a convenient dict
        :return: dict(config_dict)
        '''
        try:
            # load the configuration pickle
            config_pickle_path = [os.getcwd(), 'public_pickles', 'configuration.p']
            config_pickle_path = os.path.join('', *config_pickle_path)
            c_obj = pickle.load(open(config_pickle_path, 'rb'))
        except FileNotFoundError:
            print("Unable to load a configuration")
            raise

        return c_obj

    @property
    def frame_data(self):
        '''
        Load the pickled dictionary of visual information produced by Watcher
        :return: dict(frame_data)
        '''
        frame_data_path = [os.getcwd(), 'public_pickles', 'frame_data.p']
        try:
            frame_data = pickle.load(open(os.path.join('', *frame_data_path), 'rb'))
        except FileNotFoundError:
            print('The frame_data.p file has not been generated or is not located at: {}'.format(
                os.path.join('', *frame_data_path)
                )
            )
            raise
        else:
            return frame_data

    @property
    def listener(self):
        '''
        Load the pickled listener object for use or modification
        :return: object listener
        '''
        listener_path = [os.getcwd(), 'public_pickles', 'listener.p']
        try:
            listener = pickle.load(open(os.path.join('', *listener_path), 'rb'))
        except FileNotFoundError:
            print('The listener.p file has not been generated or is not located at: {}'.format(
                os.path.join('', *listener_path)
                )
            )
            raise
        else:
            return listener


'''
------------------------------------------------------
Classes required to initiate a SocketServer connection
------------------------------------------------------
'''


class TCPServer(socketserver.TCPServer):

    def __init__(self, host, port, handler):
        super().__init__(RequestHandlerClass=handler,
                         server_address=(host, port))


class TCPHandler(socketserver.BaseRequestHandler):
    """
    The request handler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """

    def handle(self):
        # self.request is the TCP socket connected to the client
        data = self.request.recv(1024).strip()
        self.server.plugin.handle_server_message(data)
