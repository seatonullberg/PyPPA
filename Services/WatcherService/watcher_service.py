from base_service import BaseService
from queue import Queue
import pickle
from threading import Thread
import cv2
import face_recognition
from facial_profile import FacialProfile


class WatcherService(BaseService):

    def __init__(self):
        # use queue to communicate with thread
        self.queue = Queue()
        # thread to read the video stream continuously
        self.video_read_thread = None

        self.name = 'WatcherService'
        self.input_filename = 'watcher_service.in'
        self.output_filename = 'frame_data.p'
        self.delay = 0.1
        super().__init__(name=self.name,
                         input_filename=self.input_filename,
                         output_filename=self.output_filename,
                         delay=self.delay)

        # branch off a thread to read the video stream continuously
        # if instructions are sent, they will be put in queue for display tio intercept
        # continuously write frame data to outfile

    def default(self):
        if self.video_read_thread is None:
            self.video_read_thread = Thread(target=self.read_frames, args=([self.queue]))
            self.video_read_thread.start()

    def active(self):
        # place instructions into the queue
        instructions = pickle.load(self.input_filename)
        self.queue.put(instructions)
        # update clock
        super().active()

    def read_frames(self, q):
        frame_data = {"frame": None,
                      "face_locations": None,
                      "face_encodings": None,
                      "face_names": None,
                      "rgb_small_frame": None,
                      "cursor_center": None}
        video_capture = cv2.VideoCapture(0)
        process_this_frame = True
        while True:
            ret, frame = video_capture.read()
            if not ret:
                continue
            # Resize frame of video to 1/4 size for faster face recognition processing
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
            rgb_small_frame = small_frame[:, :, ::-1]
            # Only process every other frame of video to save time
            if process_this_frame:
                frame_data["frame"] = frame
                frame_data["rgb_small_frame"] = rgb_small_frame
                frame_data["face_locations"] = face_recognition.face_locations(rgb_small_frame)
                frame_data["face_encodings"] = face_recognition.face_encodings(rgb_small_frame,
                                                                               frame_data["face_locations"])
                # call analysis threads and write data to outfile
                Thread(target=self.analyze_frame, args=([frame_data])).start()

            # display the captured video
            if q.empty():
                instructions = None
            else:
                instructions = q.get
            self.display_video(frame_data=frame_data,
                               instructions=instructions)
            process_this_frame = not process_this_frame

    def display_video(self, frame_data, instructions=None):
        if frame_data['face_locations'] is not None and frame_data['face_names'] is not None:
            for (top, right, bottom, left), name in zip(frame_data['face_locations'],
                                                        frame_data['face_names']):
                # Scale back up face locations since the frame we detected in was scaled to 1/4 size
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4

                # Draw a box around the face
                cv2.rectangle(frame_data['frame'], (left, top), (right, bottom), (0, 0, 255), 2)

                # Draw a label with a name below the face
                cv2.rectangle(frame_data['frame'], (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame_data['frame'], name, (left + 6, bottom - 6), font, 0.75, (255, 255, 255), 1)

        # Display the resulting image
        cv2.imshow('PyPPA Vision', frame_data['frame'])

    def analyze_frame(self, frame_data):
        # spawn multiple analysis threads
        # communicate with another queue
        # write the output from this thread
        queue = Queue()
        self.output(frame_data)
        # call the analysis threads
        # wait to join all
        # assemble the final frame_data dict and pickle it

    def _get_face_names(self):
        pass

    def _get_cursor_center(self):
        pass
