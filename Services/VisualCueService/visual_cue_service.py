import datetime
from base_service import BaseService
from threading import Thread
import pickle
import os


class VisualCueService(BaseService):

    def __init__(self):
        self.greeting_times = {}
        self.analysis_thread = None
        self.name = "VisualCueService"
        self.input_filename = 'visual_cue_service.in'
        self.output_filename = 'visual_cue_service.out'
        self.delay = 0
        super().__init__(name=self.name,
                         input_filename=self.input_filename,
                         output_filename=self.output_filename,
                         delay=self.delay)

    def default(self):
        if self.analysis_thread is None:
            self.analysis_thread = Thread(target=self.threader)
            self.analysis_thread.start()

    def threader(self):
        # access the frame data the long way around
        frame_data_file = self.config_obj.services['WatcherService']['output_filename']
        while True:
            try:
                frame_data = pickle.load(open(frame_data_file, 'rb'))
            except FileNotFoundError:
                continue
            except EOFError:
                continue
            except pickle.UnpicklingError:
                continue
            else:
                # add more functions later
                Thread(target=self.greet, args=([frame_data])).start()

    def greet(self, frame_data):
        if frame_data['face_names'] is None:
            return

        for name in frame_data['face_names']:
            try:
                self.greeting_times[name]
            except KeyError:
                # if the face has not been greeted yet, add an entry with current time and greet
                self.greeting_times[name] = datetime.datetime.now()
                self.vocalize("Hello {}".format(name))
            else:
                delta = datetime.datetime.now() - self.greeting_times[name]
                m = divmod(delta.total_seconds(), 60)
                # greet again if an hour has passed
                if m[0] > 60:
                    self.greeting_times[name] = datetime.datetime.now()
                    self.vocalize("Hello {}".format(name))

    def vocalize(self, text):
        # access the speaker service the long way around
        speaker_service_signal = self.config_obj.services['SpeakerService']['input_filename']
        with open(speaker_service_signal, 'w') as f:
            f.write(text)
        while os.path.isfile(speaker_service_signal):
            continue
