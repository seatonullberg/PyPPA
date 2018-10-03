import os
import pickle
import cv2
import numpy as np
from scipy.misc import imread
from scipy.spatial.distance import cdist
from utils import identity_profile_utils
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from threading import Thread
# TODO: add evaluation function to determine model performance


def build():
    """
    Creates a new facial recognition model and saves it as model.p in /FacialRecognition/
    """
    x, y = _load_images()
    _train(x, y)


def load():
    """
    Loads the pickled tSNE, PCA, and KDE kernels
    :return: pca (sklearn.decomposition.PCA),
             normlaizer (sklearn.preprocessing.StandardScaler)
             submatrices (dict) - enumerates submatrix of each profile by face_id
    """
    local_path = os.path.dirname(__file__)
    pickle_path = os.path.join(local_path, "{}")

    # load pca
    with open(pickle_path.format("pca.p"), 'rb') as stream:
        pca = pickle.load(stream)
    # load normalizer
    with open(pickle_path.format("normalizer.p"), 'rb') as stream:
        normalizer = pickle.load(stream)
    # load submatrices
    submatrices = identity_profile_utils.load_all_kdes()

    return pca, normalizer, submatrices


def _load_images():
    """
    Loads images from /IdentityProfiles/ into an array with class labels
    :return: x (numpy.ndarray) array of all images,
             y (numpy.ndarray) array of class labels,
             z (dict) enumerates all images by face_id
    """
    _x = []  # list of all flattened images
    _y = {}  # dict {face_id: [flattened_iamge,]}

    # generate path to profiles
    pyppa_path = os.path.dirname(__file__)
    pyppa_path = os.path.dirname(pyppa_path)
    identity_profiles_path = os.path.join(pyppa_path, "IdentityProfiles")
    profile_dirs = os.listdir(identity_profiles_path)
    profile_dirs.remove("README.md")
    profile_dirs = [os.path.join(identity_profiles_path, pds) for pds in profile_dirs]

    # iterate over profiles
    for profile_dir in profile_dirs:
        profile = identity_profile_utils.load_profile(profile_dir)
        face_id = profile['face_id']
        image_files = os.listdir(os.path.join(identity_profiles_path, profile_dir, "images"))
        _y[face_id] = []
        for image_file in image_files:
            image_path = os.path.join(profile_dir, "images", image_file)
            image = imread(image_path)
            image = image.flatten()
            _x.append(image)
            _y[face_id].append(image)

    x = np.vstack(_x)  # array of all flattened images
    y = {k: np.vstack(v) for k, v in _y.items()}  # enumeration of sub arrays

    return x, y


def _train(x, y):
    """
    Trains and saves a NeuralNetwork classifier on the images
    - follows the Eigenfaces implementation
    :param x: (numpy.ndarray) array of all flattened images
    :param y: (dict) an enumeration of subarrays by face_id
    """
    # generate path into FacialRecognition/
    pyppa_path = os.path.dirname(__file__)
    pyppa_path = os.path.dirname(pyppa_path)
    pickle_path = os.path.join(pyppa_path,
                               "FacialRecognition",
                               "{}")

    # Normalization
    normalizer = StandardScaler()
    normalizer.fit(x)
    x = normalizer.transform(x)
    # save Normalizer to pickle file
    with open(pickle_path.format("normalizer.p"), 'wb') as stream:
        pickle.dump(normalizer, stream)

    # PCA
    pca = PCA()
    pca.fit(x)
    # save PCA kernel to pickle file
    with open(pickle_path.format("pca.p"), 'wb') as stream:
        pickle.dump(pca, stream)

    # Save dimensional reduction of each submatrix
    identity_profiles_path = os.path.join(pyppa_path, "IdentityProfiles")
    identity_profiles = os.listdir(identity_profiles_path)
    identity_profiles.remove('README.md')
    for name in identity_profiles:
        profile = identity_profile_utils.load_profile(name)
        face_id = profile['face_id']
        submatrix = y[face_id]
        submatrix = normalizer.transform(submatrix)
        submatrix = pca.transform(submatrix)
        pickle_path = os.path.join(identity_profiles_path,
                                   name,
                                   "submatrix.p")
        with open(pickle_path, 'wb') as stream:
            pickle.dump(submatrix, stream)


class FacialRecognitionModel(Thread):
    """
    Wraps the tSNE, PCA, and KDE kernels to recognize the identity of faces in a frame
    """

    def __init__(self, queue, pca=None, normalizer=None, submatrices=None):
        """
        Loads a pretrained model/kernel or uses one passed in
        :param queue: (utils.parallelization_utils.TwoWayQueue) enable two-way data transfer
        :param pca: alternative PCA kernel
        :param normalizer: alternative Normalization kernel
        :param submatrices: alternative dict of submatrices
        """
        super().__init__()

        # process args
        self.queue = queue
        self.pca = None
        self.normalizer = None
        self.submatrices = None

        if pca is not None:
            self.pca = pca
        if normalizer is not None:
            self.normalizer = normalizer
        if submatrices is not None:
            self.submatrices = submatrices

        _pca, _normalizer, _submatrices = load()
        if self.pca is None:
            self.pca = _pca
        if self.normalizer is None:
            self.normalizer = _normalizer
        if self.submatrices is None:
            self.submatrices = _submatrices

        # load all of the identity profiles for quick recall
        profiles = identity_profile_utils.load_all_profiles()
        profile_dict = {}  # face_id keys and profile values
        for profile in profiles:
            profile_dict[profile['face_id']] = profile

        # load the facial cascade file
        casc_path = "/home/seaton/repos/PyPPA/bin/frontal_face_cascade.xml"
        self.cascade_classifier = cv2.CascadeClassifier(casc_path)

        self.profile_dict = profile_dict

    def run(self):
        """
        Overrides base method to call analyze directly
        """
        self.analyze()

    def analyze(self):
        """
        Extracts face locations and identities from a video frame
        :return frame_data: (list) list of dicts of information corresponding to located faces
        """
        while True:
            # check queue for a new frame
            if self.queue.server_queue.empty():
                continue
            else:
                frame = self.queue.server_queue.get()

            # extract and process faces
            frames, locations = self._extract_faces(frame)
            frame_data = []
            for f, l in zip(frames, locations):
                name, confidence = self._analyze(f)
                frame_data.append({'name': name,
                                   'confidence': confidence,
                                   'location': l})
                self.queue.client_queue.put(frame_data)

    def _analyze(self, frame):
        """
        Applies the facial recognition model to an image array
        - input array should contain only a single face
        :param frame: (numpy.ndarray)
        :return: (str) name - name of detected identity
                 (float) highest_prob - probalility of prediction
        """
        frame = self._preprocess(frame)
        lowest_distance = np.inf
        name = None
        all_distances = []
        for k, v in self.submatrices.items():
            # calculate distance between all pairs of points in submatrix to use as n-dimensional boundary radius
            radius = cdist(v, v, 'euclidean')
            radius = radius[radius != 0]  # remove zeros to get accurate mean squared distances
            radius = np.mean(np.sqrt(radius**2))
            radius = radius*0.80  # arbitrary tightening factor

            centroid = np.mean(v, axis=0)  # calculate centroid array

            # calculate distance from centroid
            distance = np.sqrt((frame - centroid)**2)  # rms distance
            distance = distance*self.pca.explained_variance_ratio_  # weight rms by explained variance
            distance = np.sum(distance)
            all_distances.append(distance)

            # determine if new class is better fit
            if distance < lowest_distance:
                lowest_distance = distance
                # determine if frame is within boundary radius
                # outside of the boundary radius is assumed to be an unknown
                if self._within_boundary(point=frame, center=centroid, radius=radius):
                    name = self.profile_dict[k]['name']
                else:
                    name = "Unknown"

        # calculate confidence rating
        all_distances.remove(lowest_distance)  # use max of this to find second lowest
        sec_lowest_distance = min(all_distances)
        confidence = (sec_lowest_distance/lowest_distance)
        confidence = np.log(confidence)
        return name, confidence

    def _preprocess(self, frame):
        """
        Transforms image array into proper format for classification
        :param frame: (numpy.ndarray)
        :return: frame (numpy.ndarray)
        """
        frame = cv2.resize(frame,
                           dsize=(100, 100),
                           interpolation=cv2.INTER_CUBIC)
        # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # make grayscale
        frame = frame.flatten()
        frame = frame.reshape(1, -1)
        frame = self.normalizer.transform(frame)
        frame = self.pca.transform(frame)
        return frame

    def _extract_faces(self, frame):
        """
        Extracts the area around faces in a raw video frame
        :param frame: (numpy.ndarray)
        :return: (list) - smaller frames containing detected faces
        """
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # make grayscale
        faces = self.cascade_classifier.detectMultiScale(
            image=frame,
            scaleFactor=1.1,
            minNeighbors=20,
            minSize=(100, 100)
        )
        frames = []
        locations = []
        for (x, y, w, h) in faces:
            crop = frame[y:y+h, x:x+w]  # crop to area around face
            frames.append(crop)
            locations.append((x, y, w, h))
        return frames, locations

    @staticmethod
    def _within_boundary(point, center, radius):
        """
        Determines if point is within boundary radius of center
        :param point: (numpy.ndarray) point to evaluate
        :param center: (numpy.ndarray) central point to calculate sphere with
        :param radius: (float) boundary radius to use
        :return: (bool)
        """
        dist = np.sum((point - center)**2)
        if dist < radius**2:
            return True
        else:
            return False
