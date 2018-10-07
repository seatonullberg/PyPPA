import dlib
import os
import numpy as np
from multiprocessing import Process
from utils import path_utils
from utils import identity_profile_utils


class FacialRecognitionModel(Process):
    """
    Uses precalculated facial embeddings to recognize
    the identity of faces in a frame of video
    """
    def __init__(self, queue):
        """
        Loads the pretrained objects
        :param queue: (utils.parallelization_utils.TwoWayQueue) enable two way communication
        """
        # init the Thread
        super().__init__()
        # load local paths for convenience
        self.local_paths = path_utils.LocalPaths()
        # process args
        self.queue = queue
        # load all the facial descriptors
        self.trained_facial_descriptors = identity_profile_utils.load_all_face_descriptors()
        # load the dlib pretrained models
        self.detector = dlib.get_frontal_face_detector()
        shape_predictor_path = os.path.join(self.local_paths.bin, "shape_predictor_5_face_landmarks.dat")
        self.shape_predictor = dlib.shape_predictor(shape_predictor_path)
        face_recognition_model_path = os.path.join(self.local_paths.bin, "dlib_face_recognition_resnet_model_v1.dat")
        self.face_recognition_model = dlib.face_recognition_model_v1(face_recognition_model_path)

    def run(self):
        """
        Extracts the face locations and identities from a frame of video
        :return: frame_data (list) list of dicts of information corresponding to located faces
        """
        while True:
            # check queue for a new frame
            if self.queue.server_empty():
                continue
            else:
                frame = self.queue.server_get()

            # extract and process faces
            frame_data = []
            detections = self.detector(frame)
            for det in detections:
                shape = self.shape_predictor(frame, det)
                face_descriptor = self.face_recognition_model.compute_face_descriptor(frame, shape)
                final_dist = np.inf
                final_name = None
                for k, v in self.trained_facial_descriptors.items():
                    dist = np.linalg.norm(v-face_descriptor)
                    if dist < final_dist:
                        final_dist = dist
                        final_name = k

                # prepare information to put in frame_data
                location = {'left': det.left(),
                            'right': det.right(),
                            'top': det.top(),
                            'bottom': det.bottom()}
                data = {'name': final_name,
                        'distance': final_dist,
                        'location': location}
                frame_data.append(data)
            # lastly, put the data back in the queue
            self.queue.client_put(frame_data)
