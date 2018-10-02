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

# Preprocess the images and write them to /IdentityProfiles/<dir_name>/faces/
# Write /IdentityProfiles/<dir_name>/<dir_name>.yaml
# -- name: <dir name>
# -- id: <len(os.listdir(/IdentityProfiles/))>

# Train recognition model with all images in all IdentityProfile directories
# pickle the model to /FacialRecognition/model.p

# Use model.p in a recognition service which WatcherService will monitor with a thread
import argparse
import os
from utils import identity_profile_utils
from FacialRecognition import preprocess
from FacialRecognition import model


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
    preprocess.process(path)  # preprocess the images in the supplied path
    name = os.path.basename(path)  # use the supplied directory name as the name of the profile
    profile = identity_profile_utils.new_profile(name)  # make a new profile
    model.build()
    print("Completed IdentityProfile construction of {}".format(profile['name']))


if __name__ == "__main__":
    p = "/home/seaton/Pictures/Seaton_Ullberg"
    main(p)
