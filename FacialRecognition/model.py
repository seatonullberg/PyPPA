import os
import pickle
import cv2
import numpy as np
from scipy.misc import imread
from utils import identity_profile_utils
from sklearn.decomposition import PCA
from sklearn.neural_network import MLPClassifier
# TODO: add evaluation function to determine model performance


def build():
    """
    Creates a new facial recognition model and saves it as model.p in /FacialRecognition/
    """
    X, y = _load_images()
    _train(X, y)


def load():
    """
    Loads the pickled facial recognition model and PCA kernel
    :return: (sklearn.neural_network.MLPClassifier), (sklearn.decomposition.PCA)
    """
    local_path = os.path.dirname(__file__)
    pickle_path = os.path.join(local_path, "{}")
    with open(pickle_path.format("model.p"), 'rb') as stream:
        model = pickle.load(stream)
    with open(pickle_path.format("pca.p"), 'rb') as stream:
        pca = pickle.load(stream)
    return model, pca


def _load_images():
    """
    Loads images from /IdentityProfiles/ into an array with class labels
    :return X, y: (numpy.ndarray) array of all images, (numpy.ndarray) array of class labels
    """
    _x = []  # list of flattened images
    _y = []  # list of face_ids

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
        image_files = os.listdir(os.path.join(identity_profiles_path, profile_dir))
        image_files.remove("profile.yaml")
        for image_file in image_files:
            image_path = os.path.join(profile_dir, image_file)
            image = imread(image_path)
            image = image.flatten()
            print(image.shape)
            _x.append(image)
            _y.append(face_id)

    X = np.vstack(_x)  # array of all flattened images
    y = np.array(_y)  # array of corresponding image classes (face_ids)

    return X, y


def _train(X, y):
    """
    Trains and saves a NeuralNetwork classifier on the images
    - follows the Eigenfaces implementation
    :param X: (numpy.ndarray) array of all flattened images
    :param y: (numpy.ndarray) array of corresponding class labels
    """
    # Compute a PCA
    pca = PCA(whiten=True)
    pca.fit(X)

    # apply PCA transformation
    X_pca = pca.transform(X)

    # train a neural network classifier
    clf = MLPClassifier(hidden_layer_sizes=(1024,),
                        batch_size=256,
                        verbose=True,
                        early_stopping=True)
    clf.fit(X_pca, y)

    # generate path into FacialRecognition/
    pyppa_path = os.path.dirname(__file__)
    pyppa_path = os.path.dirname(pyppa_path)
    pickle_path = os.path.join(pyppa_path,
                               "FacialRecognition",
                               "{}")

    # save classifier to pickle file
    with open(pickle_path.format("model.p"), 'wb') as stream:
        pickle.dump(clf, stream)

    # save PCA kernel to pickle file
    with open(pickle_path.format("pca.p"), 'wb') as stream:
        pickle.dump(pca, stream)


class FacialRecognitionModel(object):
    """
    Wraps the MLPClassifier and PCA kernel to recognize the identity of a face in a frame
    """

    def __init__(self, model=None, pca=None):
        """
        Loads a pretrained model/kernel or uses one passed in
        :param model: alternative classifier object
        :param pca: alternative PCA kernel
        """
        # process args
        self.model = None
        self.pca = None

        if model is not None:
            self.model = model
        if pca is not None:
            self.pca = pca

        _model, _pca = load()
        if self.model is None:
            self.model = _model
        if self.pca is None:
            self.pca = _pca

        # load all of the identity profiles for quick recall
        profiles = identity_profile_utils.load_all()
        profile_dict = {}  # face_id keys and profile values
        for profile in profiles:
            profile_dict[profile['face_id']] = profile

        self.profile_dict = profile_dict

    def analyze(self, frame):
        """
        Applies the facial recognition model to an image array
        - input array should contain only a single face
        :param frame: (numpy.ndarray)
        :return: (str) name - name of detected identity
                 (float) prob - probalility of prediction
        """
        frame = self._preprocess(frame)
        pred_face_id = self.model.predict(frame)
        assert len(pred_face_id) == 1  # if this fails the frame contains multiple faces
        pred_face_id = pred_face_id[0]
        prob = self.model.predict_proba(frame)
        prob = prob[0][0]
        name = self.profile_dict[pred_face_id]['name']
        return name, prob

    def _preprocess(self, frame):
        """
        Transforms image array into proper format for classification
        :param frame: (numpy.ndarray)
        :return: frame (numpy.ndarray)
        """
        frame = cv2.resize(frame,
                           dsize=(100, 100),
                           interpolation=cv2.INTER_CUBIC)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame = frame.flatten()
        frame = frame.reshape(1, -1)
        frame = self.pca.transform(frame)
        return frame
