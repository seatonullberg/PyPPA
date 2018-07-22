import face_recognition
import cv2
import os
import pickle
from threading import Thread
from facial_profile import FacialProfile
import numpy as np
import pyautogui
from queue import Queue


# TODO: Figure out how to better incorporate video playback
class BackgroundWatcher(object):

    def __init__(self):
        self.frame_data = {}

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
        queue = Queue()
        t1 = Thread(target=self.get_face_names, args=(queue, self.frame_data))
        t2 = Thread(target=self.get_cursor_centers, args=(queue, self.frame_data))
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        while not queue.empty():
            data = queue.get()
            self.frame_data[data[0]] = data[1]
        # pickle the dict so that external plugins can work with visual data
        # SUPER IMPORTANT FILE FOR OTHER PLUGINS THAT USE VISUAL CUES
        frame_data_path = ['public_pickles', 'frame_data.p']
        pickle.dump(self.frame_data, open(os.path.join('', *frame_data_path), 'wb'))

    def get_face_names(self, q, frame_dict):
        face_names = []
        profile_dict = FacialProfile().__dict__()
        for face_encoding in frame_dict['face_encodings']:
            name = "Unknown"
            for key in profile_dict:
                # Compare known embeddings to new embedding
                matches = face_recognition.compare_faces([profile_dict[key][1]], face_encoding)
                if True in matches:
                    name = profile_dict[key][0]
                    break
            face_names.append(name)
        # put a key and value in the queue for the analyzer to add to dict
        q.put(('face_names', face_names))

    # TODO: use eye control instead
    def get_cursor_centers(self, q, frame_dict):
        # get 'cursor' locations from frame
        hsv = cv2.cvtColor(frame_dict['frame'], cv2.COLOR_BGR2HSV)
        lower_green = np.array([50, 50, 70])
        upper_green = np.array([80, 255, 255])
        mask = cv2.inRange(hsv, lower_green, upper_green)
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)
        cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
                                cv2.CHAIN_APPROX_SIMPLE)[-2]
        # this if will cause errors but I'm leaving it since the whole thing will change soon
        if len(cnts) == 2:
            # 2 points are needed for easy 'click' functionality
            centers = []
            for c in cnts:
                m = cv2.moments(c)
                center = (int((m['m10'] / m['m00'])), int((m['m01'] / m['m00'])))
                centers.append(center)

            # get x and y midpoint of the 2 color blobs
            mid_x = np.median([centers[0][0], centers[1][0]])
            mid_y = np.median([centers[0][1], centers[1][1]])
            # get display dimensions
            screen_width, screen_height = pyautogui.size()
            # scale movement from OpenCV display to full display
            scaled_x = (screen_width / hsv.shape[0]) * mid_x
            scaled_y = (screen_height / hsv.shape[1]) * mid_y
            # invert lateral movement so the cursor moves naturally
            scaled_x = screen_width - scaled_x
            pyautogui.moveTo(x=scaled_x, y=scaled_y)

            from scipy.spatial.distance import euclidean
            if euclidean(u=centers[0], v=centers[1]) < 30:
                pyautogui.click(x=mid_x, y=mid_y)

            q.put(('cursor_centers', centers))
