import face_recognition
import cv2
import datetime
import os
from private_config import DATA_DIR
import pickle
from threading import Thread
from facial_profile import FacialProfile
# interface with the plugin to execute actionable commands
# send a string command directly to be executed upon realization of visual cue
from Plugins.WatcherPlugin.watcher_plugin import PyPPA_WatcherPlugin


# TODO: Improve greeting and possibly add object detection?
class BackgroundWatcher(object):

    def __init__(self):
        # initialize empty plugin to use its commands
        self.plugin = PyPPA_WatcherPlugin('')
        self.frame_data = {}
        self.greeting_times = {}

    def startup(self):
        # Get a reference to webcam #0 (the default one)
        video_capture = cv2.VideoCapture(0)
        face_locations = []
        face_encodings = []
        face_names = []
        process_this_frame = True
        while True:
            # Grab a single frame of video
            ret, frame = video_capture.read()
            # Resize frame of video to 1/4 size for faster face recognition processing
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
            rgb_small_frame = small_frame[:, :, ::-1]
            # Only process every other frame of video to save time
            if process_this_frame:
                # collect general data for use in additional functions
                self.analyze_frame(frame=frame, rgb_small_frame=rgb_small_frame)
                # then distribute tasks among multiple threads
                self.threader()
            process_this_frame = not process_this_frame

            # Display the results
            for (top, right, bottom, left), name in zip(self.frame_data['face_locations'],
                                                        self.frame_data['face_names']):
                # Scale back up face locations since the frame we detected in was scaled to 1/4 size
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4

                # Draw a box around the face
                cv2.rectangle(self.frame_data['frame'], (left, top), (right, bottom), (0, 0, 255), 2)

                # Draw a label with a name below the face
                cv2.rectangle(self.frame_data['frame'], (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(self.frame_data['frame'], name, (left + 6, bottom - 6), font, 0.75, (255, 255, 255), 1)

            # Display the resulting image
            cv2.imshow('PyPPA Vision', self.frame_data['frame'])

            # Hit 'q' on the keyboard to quit!
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # Release handle to the webcam
        video_capture.release()
        cv2.destroyAllWindows()

    # collect general data from the captured frame
    def analyze_frame(self, frame, rgb_small_frame):
        self.frame_data['frame'] = frame
        self.frame_data['rgb_small_frame'] = rgb_small_frame
        self.frame_data['face_locations'] = face_recognition.face_locations(rgb_small_frame)
        self.frame_data['face_encodings'] = face_recognition.face_encodings(rgb_small_frame,
                                                                            self.frame_data['face_locations'])
        face_names = []
        profile_dict = FacialProfile().__dict__()
        for face_encoding in self.frame_data['face_encodings']:
            name = "Unknown"
            for key in profile_dict:
                # Compare known embeddings to new embedding
                matches = face_recognition.compare_faces([profile_dict[key][1]], face_encoding)
                if True in matches:
                    name = profile_dict[key][0]
                    break
            face_names.append(name)
        self.frame_data['face_names'] = face_names
        # TODO: Figure out how to store the area just around an identified face
        self.frame_data['images'] = [None for n in face_names]
        # pickle the dict so that external plugins can work with visual data
        # SUPER IMPORTANT FILE FOR OTHER PLUGINS THAT WANT VISUAL CUES
        frame_data_path = [DATA_DIR, 'public_pickles', 'frame_data.p']
        pickle.dump(self.frame_data, open(os.path.join('', *frame_data_path), 'wb'))

    def threader(self):
        funcs = dir(BackgroundWatcher)
        funcs = [f for f in funcs if f.startswith('task_')]
        for f in funcs:
            Thread(target=getattr(BackgroundWatcher, f), args=(self,)).start()

    def task_determine_greeting(self):
        for name in self.frame_data['face_names']:
            try:
                self.greeting_times[name]
            except KeyError:
                # if the face has not been greeted yet, add an entry with current time and greet
                self.greeting_times[name] = datetime.datetime.now()
                self.plugin.function_handler(command_hook='greet',
                                             args_dict={'greeting': 'Hello {}!'.format(name)})
            else:
                delta = datetime.datetime.now() - self.greeting_times[name]
                m = divmod(delta.total_seconds(), 60)
                # greet again if an hour has passed
                if m[0] > 60:
                    self.greeting_times[name] = datetime.datetime.now()
                    self.plugin.function_handler(command_hook='greet',
                                                 args_dict={'greeting': 'Hello {}!'.format(name)})
