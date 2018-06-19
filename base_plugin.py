import pickle
import os
import socket
from queue import Queue
from threading import Thread
import struct
import time


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
        # establish queues for listening and sending
        self.send_queue = Queue()
        self.listen_queue = Queue()
        self.cs = None  # client server object goes here

    '''
    -------------------------------------------------
    General use functions for normal Plugin operation
    -------------------------------------------------
    '''
    def initialize(self, cmd=None):
        # call this as target of a new process for smooth transition
        self.make_active()
        self.mainloop(cmd)

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
            # check the queue for messages from server
            if not self.listen_queue.empty():
                msg = self.listen_queue.get()
                msg = msg.decode()
                name, cmd = msg.split('$')
                if self.name == name:
                    self.make_active()
            if self.isActive:
                print('{} is active'.format(self.name))
                if cmd is None:
                    cmd = self.listener.listen_and_convert()
                self.command_parser(cmd)
                self.function_handler()
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
        # test server availability
        # use args in special use cases where this general behavior needs to be overwritten
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
        self.isActive = True
        if self.cs is None:
            _port = self.config_obj.port_map[self.name]
            # this port list is lazy because it assumes all plugins are connected which is not likely to happen
            # UDP makes it easy to do this way
            _port_list = [v for k, v in self.config_obj.port_map.items()]
            self.cs = ClientServer(port=_port,
                                   port_list=_port_list,
                                   send_queue=self.send_queue,
                                   listen_queue=self.listen_queue)

            Thread(target=self.cs.listen).start()
            Thread(target=self.cs.send).start()

    # provide namespace to overwrite for design symmetry
    def update_plugin(self, args=None):
        pass

    '''
    ---------------------------------------------------------
    Methods for gracefully shifting control to another plugin
    ---------------------------------------------------------
    '''

    def pass_and_remain(self, name, cmd):
        '''
        send message to new plugin and remain in background
        :param name: name of plugin message is going to
        :param cmd: command sent to that plugin
        :return: None
        '''
        self.isActive = False
        message_str = "{}${}".format(name, cmd)
        self.send_queue.put(message_str)

    def pass_and_terminate(self, name, cmd):
        '''
        send message to new plugin and terminate subsequently
        :param name: name of plugin message is going to
        :param cmd: command sent to that plugin
        :return: None
        '''
        self.isActive = False
        message_str = "{}${}".format(name, cmd)
        self.send_queue.put(message_str)
        time.sleep(.5)  # not ideal
        self.send_queue.put('quit')
        time.sleep(.5)  # not ideal
        os.kill(os.getpid(), 9)

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
------------------------------------------
UDP messaging class to synchronize plugins
------------------------------------------
'''


class ClientServer(object):

    def __init__(self,
                 port,
                 port_list,
                 send_queue,
                 listen_queue,
                 group='224.3.29.71'):
        self.port = port
        self.port_list = port_list
        self.send_queue = send_queue
        self.listen_queue = listen_queue
        self.group = group

    def send(self):
        # Create the datagram socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Set a timeout so the socket does not block indefinitely when trying
        # to receive data.
        sock.settimeout(0.25)
        # Set the time-to-live for messages to 1 so they do not go past the
        # local network segment.
        ttl = struct.pack('b', 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

        while True:
            # get message to send from the q
            if not self.send_queue.empty():
                message = self.send_queue.get()
                if message == 'quit':
                    break
            else:
                continue
            for p in self.port_list:
                #print('{} sending {} to {}'.format(self.port,
                #                                   message,
                #                                   p))
                sock.sendto(message.encode(), (self.group, p))
                '''
                ------------------------------------------------------------------
                If I wanted to do a response based check this is how it would work

                # Look for responses from all recipients
                while True:
                    try:
                        data, server = sock.recvfrom(16)
                    except socket.timeout:
                        break
                    else:
                        print(' {} received {} from {}'.format(self.port,
                                                               data,
                                                               server))
                ------------------------------------------------------------------
                '''

    def listen(self):
        server_address = ('', self.port)
        # Create the socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Bind to the server address
        sock.bind(server_address)
        # Tell the operating system to add the socket to the multicast group
        # on all interfaces.
        group = socket.inet_aton(self.group)
        mreq = struct.pack('4sL', group, socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        # Receive/respond loop
        while True:
            data, address = sock.recvfrom(1024)
            self.listen_queue.put(data)
            #print(' {} received {} bytes from {}'.format(self.port,
            #                                             len(data),
            #                                             address))

            '''
            ---------------------------------------------------------------------
            If I wanted to use acknowledgement messages this is how I would do it

            print(' {} sending acknowledgement to {}'.format(self.port,
                                                             address))
            sock.sendto('ack'.encode(), address)
            ---------------------------------------------------------------------
            '''