import datetime
import os
import pickle
import time


class Clock(object):

    def __init__(self):
        self._since_init = datetime.datetime.now()
        self._since_active = None
        self._since_output = None

    def update(self, flag):
        if flag == 'active':
            self._since_active = datetime.datetime.now()
        elif flag == 'output':
            self._since_output = datetime.datetime.now()
        else:
            raise ValueError("flag must be 'active' or 'output'")

    @property
    def since_init(self):
        delta = datetime.datetime.now() - self._since_init
        return delta.total_seconds()

    @property
    def since_active(self):
        if self._since_active is None:
            return -1
        else:
            delta = datetime.datetime.now() - self._since_active
            return delta.total_seconds()

    @property
    def since_output(self):
        if self._since_output is None:
            return -1
        else:
            delta = datetime.datetime.now() - self._since_output
            return delta.total_seconds()


class BaseService(object):

    def __init__(self,
                 name,
                 input_filename,
                 output_filename,
                 delay):
        self.name = name
        input_path = [os.getcwd(), 'tmp', input_filename]
        input_filename = os.path.join('', input_path)
        self.input_filename = input_filename
        output_path = [os.getcwd(), 'tmp', output_filename]
        output_filename = os.path.join('', output_path)
        self.output_filename = output_filename
        self.delay = delay
        self.clock = Clock()

    def mainloop(self):
        # keep the service running continuously
        while True:
            if os.path.isfile(self.input_filename):
                # wait for any desired response delay
                # TODO: do this without delays
                # it currently exists because some files
                # can trigger True before the content is ready
                time.sleep(self.delay)
                self.active()
                # clean up to prevent perpetual active loop
                os.remove(self.input_filename)
            else:
                self.default()

    def default(self):
        # to be overwritten by subclass (or remain null action)
        # define the behavior of the service when no signal is detected
        pass

    def active(self):
        # to be overwritten by subclass (or remain null action)
        # define the behavior of the service when no signal is detected
        self.clock.update(flag='active')

    def output(self, data):
        if self.output_filename.endswith('.p'):
            # pickle the data
            pickle.dump(data, open(self.output_filename, 'wb'))
        else:
            # write as text file
            with open(self.output_filename, 'w') as outfile:
                outfile.write(data)
        self.clock.update(flag='output')
