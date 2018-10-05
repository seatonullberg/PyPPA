import os
import yaml
import pickle
from utils import path_utils  # TODO


def new_profile(name):
    """
    Makes a yaml file with entries for name and face_id
    :param name: (str) name to associate with the new profile
    :return profile: (dict) profile information
    """
    dirname = name.replace(' ', '_')  # directories should have no spaces
    name = name.replace('_', ' ')  # actual name in profile should have spaces

    # generate path to IdentityProfiles directory
    pyppa_path = os.path.dirname(__file__)
    pyppa_path = os.path.dirname(pyppa_path)
    identity_profiles_path = os.path.join(pyppa_path,
                                          "IdentityProfiles")

    # generate new directory for the new profile
    profile_path = os.path.join(identity_profiles_path, dirname)
    if not os.path.exists(profile_path):
        os.makedirs(profile_path)

    # collect information in dict
    to_yaml = {'name': name}

    # write the yaml file
    yaml_path = os.path.join(profile_path, "profile.yaml")
    with open(yaml_path, 'w') as stream:
        yaml.dump(to_yaml, stream)

    return to_yaml


def load_profile(name):
    """
    Loads an IdentityProfile by name
    :param name: (str) name of the profile to load
    :return profile: (dict) profile information
    """
    # spaces are converted to underscores
    # Seaton_Ullberg is processed just the same as Seaton Ullberg
    name = name.replace(' ', '_')

    # generate path to profile
    pyppa_path = os.path.dirname(__file__)
    pyppa_path = os.path.dirname(pyppa_path)
    yaml_path = os.path.join(pyppa_path,
                             "IdentityProfiles",
                             name,
                             "profile.yaml")

    # load profile
    with open(yaml_path, 'r') as stream:
        profile = yaml.load(stream)

    return profile


def load_all_profiles():
    """
    Loads all of the IdentityProfiles
    :return profiles: (list) list of profiles
    """
    # generate path to IdentityProfiles
    pyppa_path = os.path.dirname(__file__)
    pyppa_path = os.path.dirname(pyppa_path)
    identity_profiles_path = os.path.join(pyppa_path,
                                          "IdentityProfiles")
    identity_profiles = os.listdir(identity_profiles_path)
    identity_profiles.remove("README.md")

    # iterate through directory
    profiles = []
    for name in identity_profiles:
        profile = load_profile(name)
        profiles.append(profile)

    return profiles


def load_face_descriptor(name):
    """
    Loads the face_descriptor by name from pickle file
    :param name: (str) name of the associated profile
    :return: (numpy.ndarray)
    """
    # spaces are converted to underscores
    # Seaton_Ullberg is processed just the same as Seaton Ullberg
    name = name.replace(' ', '_')

    # generate path to profile
    pyppa_path = os.path.dirname(__file__)
    pyppa_path = os.path.dirname(pyppa_path)
    pickle_path = os.path.join(pyppa_path,
                               "IdentityProfiles",
                               name,
                               "face_descriptor.p")

    # load face_descriptor from pickle
    with open(pickle_path, 'rb') as stream:
        face_descriptor = pickle.load(stream)

    return face_descriptor


def load_all_face_descriptors():
    """
    Loads all of the face_descriptors
    :return kdes: (dict) name keys and face_descriptor values
    """
    # generate path to IdentityProfiles
    pyppa_path = os.path.dirname(__file__)
    pyppa_path = os.path.dirname(pyppa_path)
    identity_profiles_path = os.path.join(pyppa_path,
                                          "IdentityProfiles")
    identity_profiles = os.listdir(identity_profiles_path)
    identity_profiles.remove("README.md")

    # iterate through directory
    face_descriptors = {}
    for name in identity_profiles:
        profile = load_profile(name)
        name = profile['name']
        descriptor = load_face_descriptor(name)
        face_descriptors[name] = descriptor

    return face_descriptors
