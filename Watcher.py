import face_recognition
import cv2
import os
from private_config import DATA_DIR
import pickle
from threading import Thread
# interface with the plugin to execute actionable commands
# send a string command directly to be executed upon realization of visual cue
# from Plugins.WatcherPlugin.watcher_plugin import PyPPA_WatcherPlugin


class BackgroundWatcher(object):

    def __init__(self):
        pass

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
                self.threader(rgb_small_frame)
                # Find all the faces and face encodings in the current frame of video
                face_locations = face_recognition.face_locations(rgb_small_frame)
                face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

                face_names = []
                profile_dict = FacialProfile().__dict__()
                for face_encoding in face_encodings:
                    name = "Unknown"
                    for key in profile_dict:
                        # Compare known embeddings to new embedding
                        matches = face_recognition.compare_faces([profile_dict[key][1]], face_encoding)
                        if True in matches:
                            name = profile_dict[key][0]
                            break
                    face_names.append(name)

            process_this_frame = not process_this_frame

            # Display the results
            for (top, right, bottom, left), name in zip(face_locations, face_names):
                # Scale back up face locations since the frame we detected in was scaled to 1/4 size
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4

                # Draw a box around the face
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

                # Draw a label with a name below the face
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

            # Display the resulting image
            cv2.imshow('PyPPA Vision', frame)

            # Hit 'q' on the keyboard to quit!
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # Release handle to the webcam
        video_capture.release()
        cv2.destroyAllWindows()

    def threader(self, frame):
        # add other analysis functions later
        for analyze in [self.archive_faces]:
            Thread(target=analyze, args=[frame]).start()

    def archive_faces(self, frame):
        '''
        Pickle a list of images of faces, their embeddings, and names if known for scan_faces to pull from
        :param frame: Video freeze frame from cv2 VideoCapture
        :return: None (produce a pickle file)
        '''
        face_locations = []
        face_encodings = []
        faces = []
        face_locations = face_recognition.face_locations(frame)
        face_encodings = face_recognition.face_encodings(frame, face_locations)
        profile_dict = FacialProfile().__dict__()
        # the face locations are a tuple of (top, right, bottom, left)
        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            name = None
            # resize the location box
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4
            image = frame[bottom:top, left:right]
            for key in profile_dict:
                # Compare known encodings to new encodings
                matches = face_recognition.compare_faces([profile_dict[key][1]], face_encoding)
                if True in matches:
                    name = profile_dict[key][0]
                    break
            faces.append({'name': name,
                          'encoding': face_encoding,
                          'image': image})
        archived_faces_path = [DATA_DIR, 'facial_profiles', 'archived_faces.p']
        pickle.dump(faces, open(os.path.join('', *archived_faces_path), 'wb'))
        # from the pickled list, the scan_faces command can make a blank FacialProfile for encodings where name is None
        # the image portion gets saved to .jpg with the FacialProfile _id as an identifier


class FacialProfile(object):
    '''
    Object used to define the identity of a facial image embedding.
    Produces a text file which can be manually edited to produce rich identities.
    A blank profile object contains:
        int(id) -unique identifier number
        array(image) -pixel array of image containing the face
        array(embedding) -embedding array used for unique identification
    Other attributes can also be defined:
        tuple(name) -first and last name
        list(subroutines) -functions to execute upon recognition of the face
    '''

    def __init__(self):
        pass

    def __dict__(self):
        # creates a smooth way of returning information about ALL FacialProfiles
        # str(_id) keys and tuple(name, embedding) values
        pairings = []
        for fname in os.listdir(os.path.join(DATA_DIR, 'facial_profiles')):
            # do not iterate over the embedding files
            if fname.endswith('.txt'):
                # add the id
                pairings.append([fname.split('_')[0]])
                with open(os.path.join(DATA_DIR, 'facial_profiles', fname), 'r') as f:
                    lines = f.readlines()
                    for i, l in enumerate(lines):
                        if l.startswith('name'):
                            name = lines[i + 1][1:-1]
                            pairings[-1].append(name)
                            break
                encoding_path = [DATA_DIR, 'facial_profiles', '{}_encoding.p'.format(fname.split('_')[0])]
                encoding = pickle.load(open(os.path.join('', *encoding_path), 'rb'))
                pairings[-1].append(encoding)
        d = {p[0]: (p[1], p[2]) for p in pairings}
        return d

    def write_profile(self, data):
        profile_list = os.listdir(os.path.join(DATA_DIR, 'facial_profiles'))
        profile_list = [p for p in profile_list if not p.endswith('.p')]
        if len(profile_list) == 0:
            file_index = 0
        else:
            indices = [fname.split('_')[0] for fname in profile_list]
            file_index = max([int(i) for i in indices])+1
        profile_path = [DATA_DIR, 'facial_profiles', '{}_profile.txt'.format(file_index)]
        with open(os.path.join('', *profile_path), 'w') as f:
            for key in data:
                if key == 'encoding':
                    encoding_path = [DATA_DIR, 'facial_profiles', '{}_encoding.p'.format(file_index)]
                    pickle.dump(data[key], open(os.path.join('', *encoding_path), 'wb'))
                elif key == 'image':
                    image_path = [DATA_DIR, 'facial_profiles', '{}_image.jpg'.format(file_index)]
                    cv2.imwrite(os.path.join('', *image_path), data[key])
                else:
                    f.write('{}:\n'.format(key))
                    f.write('\t' + str(data[key]) + '\n')

    def read_profile(self, _id):
        profile = open(os.path.join(DATA_DIR, 'facial_profiles', '{}_profile.txt'.format(_id)), 'r').readlines()
        encoding = pickle.load(open(os.path.join(DATA_DIR, 'facial_profiles', '{}_encoding.p'.format(_id)), 'rb'))
        pairings = []
        for line in profile:
            if line.endswith(':\n'):
                pairings.append(line[:-1])
            elif line.startswith('\t'):
                # remove the initial tab and ending newline
                pairings[-1] = (pairings[-1], line[1:-1])
            else:
                continue
        profile = {p[0]: p[1] for p in pairings}
        return profile, encoding
