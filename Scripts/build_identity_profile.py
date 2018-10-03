# Specify path to a directory of facial images of one person
# --ex) python3 build_identity_profile.py --path ~/data/Seaton_Ullberg

# -- ex) Seaton_Ullberg/
#                      --> image00.jpg
#                      --> image01.jpg
#                      --> image02.jpg
#                      --> image03.jpg
#                      --> image04.jpg

# Directory name will be used as the name of the profile
# Underscores are interpreted as spaces when constructing the profile: Seaton_Ullberg/ ==> name: Seaton Ullberg

# Preprocess the images and write them to /IdentityProfiles/<dir_name>/images/
# Write /IdentityProfiles/<dir_name>/profile.yaml
# -- name: <dir name>
# -- id: <len(os.listdir(/IdentityProfiles/))>

# Train recognition model with all images in all IdentityProfile directories
# pickle the model to /FacialRecognition/model.p

# Use model.p in a recognition service which WatcherService will monitor with a thread
import argparse
import os
import cv2
from utils import identity_profile_utils
from FacialRecognition import model


def preprocess(input_path):
    """
    Preprocesses images in input_path for facial recognition
    :param input_path: (str) absolute path to a directory of facial images
    """
    # load cascade file
    pyppa_dir = os.path.dirname(__file__)
    pyppa_dir = os.path.dirname(pyppa_dir)
    casc_path = os.path.join(pyppa_dir, "bin", "frontal_face_cascade.xml")
    face_cascade = cv2.CascadeClassifier(casc_path)

    # iterate through images
    for fname in os.listdir(input_path):
        image_path = os.path.join(input_path, fname)
        image = cv2.imread(image_path)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # convert to gray scale
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=20,
            minSize=(100, 100)
        )

        if len(faces) != 1:  # only accept single face images
            continue

        for (x, y, w, h) in faces:
            # crop image around area of face to (100x100)
            crop = gray[y:y + h, x:x + w]
            crop = cv2.resize(crop,
                              dsize=(100, 100),
                              interpolation=cv2.INTER_CUBIC)

            # TODO: Rotate crop so that the eyes are aligned

            # generate path in /IdentityProfiles/
            dir_name = os.path.basename(input_path)
            outdir = os.path.join(pyppa_dir,
                                  "IdentityProfiles",
                                  dir_name,
                                  "images")
            # make dir if not exists
            if not os.path.isdir(outdir):
                os.makedirs(outdir)
            # save file
            outfile = os.path.join(outdir, fname)
            cv2.imwrite(filename=outfile, img=crop)


def main(path=None):
    if path is None:
        parser = argparse.ArgumentParser()
        parser.add_argument('--path',
                            default=None,
                            help="Path to directory containing face images")
        args = parser.parse_args()
        if args.path is None:
            raise argparse.ArgumentError("--path is a required argument")
        path = args.path
    preprocess(path)  # preprocess the images in the supplied path
    name = os.path.basename(path)  # use the supplied directory name as the name of the profile
    profile = identity_profile_utils.new_profile(name)  # make a new profile
    model.build()
    print("Completed IdentityProfile construction of {}".format(profile['name']))


if __name__ == "__main__":
    p = "/home/seaton/Pictures/Seaton_Ullberg"
    main(p)
