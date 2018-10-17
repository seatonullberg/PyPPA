import dlib
import pickle
import numpy as np
import os
import argparse
from utils import path_utils
from utils import identity_profile_utils


def main(path=None):
    """
    Creates an IdentityProfile
    :param path: (str) absolute path to a directory containing training images
                 - the end of the path should be a directory named after the person
                 - e.g. Seaton_Ullberg
                 - all images in the directory should contain only the face of the target
    """

    # process args
    parser = argparse.ArgumentParser()
    parser.add_argument('--path',
                        default=None,
                        help="Path to directory containing face images")
    args = parser.parse_args()
    if path is None:
        if args.path is None:
            raise argparse.ArgumentError("--path is a required argument")
        else:
            path = args.path

    # load the pretrained dlib models
    local_paths = path_utils.LocalPaths()
    detector = dlib.get_frontal_face_detector()
    shape_predictor_path = os.path.join(local_paths.bin, "shape_predictor_5_face_landmarks.dat")
    shape_predictor = dlib.shape_predictor(shape_predictor_path)
    face_recognition_model_path = os.path.join(local_paths.bin, "dlib_face_recognition_resnet_model_v1.dat")
    face_recognition_model = dlib.face_recognition_model_v1(face_recognition_model_path)

    # iterate through a directory of images to calculate a 128D face description vector
    descriptors = []
    for fname in os.listdir(path):
        img_path = os.path.join(path, fname)
        img = dlib.load_rgb_image(img_path)

        detections = detector(img, 1)
        if len(detections) != 1:  # only use single face images
            continue
        d = detections[0]
        shape = shape_predictor(img, d)
        face_descriptor = face_recognition_model.compute_face_descriptor(img, shape, 10)
        descriptors.append(face_descriptor)
    final_descriptor = np.mean(descriptors, axis=0)

    # generate an IdentityProfile and save the descriptor alongside it
    dir_name = os.path.basename(path)
    pickle_path = os.path.join(local_paths.identity_profiles, dir_name, "{}")

    # make the new profile dir and yaml file
    identity_profile_utils.new_profile(dir_name)

    # save face descriptor as a pickle
    with open(pickle_path.format("face_descriptor.p"), 'wb') as stream:
        pickle.dump(final_descriptor, stream)


if __name__ == "__main__":
    main("/home/seaton/Pictures/Seaton_Ullberg")
