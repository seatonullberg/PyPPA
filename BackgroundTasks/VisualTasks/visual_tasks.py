from base_background_task import BaseBackgroundTask
import datetime


class VisualTasks(BaseBackgroundTask):

    def __init__(self):
        self._name = 'VisualTasks'
        # always be looking for faces to greet
        self.delays = [(self.determine_greeting, 1)]
        self.greeting_times = {}
        super().__init__(delays=self.delays,
                         name=self._name)

    # TODO: make better greetings
    def determine_greeting(self):
        for name in self.frame_data['face_names']:
            try:
                self.greeting_times[name]
            except KeyError:
                # if the face has not been greeted yet, add an entry with current time and greet
                self.greeting_times[name] = datetime.datetime.now()
                self.vocalize("Hello, {}".format(name))
            else:
                delta = datetime.datetime.now() - self.greeting_times[name]
                m = divmod(delta.total_seconds(), 60)
                # greet again if an hour has passed
                if m[0] > 60:
                    self.greeting_times[name] = datetime.datetime.now()
                    self.vocalize("Hello {}".format(name))

    # I have no idea where to put this code right now
    '''
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
    '''