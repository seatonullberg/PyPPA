import os
import yaml
import pickle


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

    # generate face_id for profile
    entries = os.listdir(identity_profiles_path)
    entries.remove("README.md")
    face_id = len(entries)

    # collect information in dict
    to_yaml = {'name': name,
               'face_id': face_id}

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


def load_submatrix(name):
    """
    Loads the KDE by name
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
                               "submatrix.p")

    # load kde
    with open(pickle_path, 'rb') as stream:
        kde = pickle.load(stream)

    return kde


def load_all_kdes():
    """
    Loads all of the KDEs
    :return kdes: (dict) face_id keys and kde values
    """
    # generate path to IdentityProfiles
    pyppa_path = os.path.dirname(__file__)
    pyppa_path = os.path.dirname(pyppa_path)
    identity_profiles_path = os.path.join(pyppa_path,
                                          "IdentityProfiles")
    identity_profiles = os.listdir(identity_profiles_path)
    identity_profiles.remove("README.md")

    # iterate through directory
    kdes = {}
    for name in identity_profiles:
        profile = load_profile(name)
        face_id = profile['face_id']
        kde = load_submatrix(name)
        kdes[face_id] = kde

    return kdes
