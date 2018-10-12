import os


class LocalPaths(object):
    """
    Convenience object to return absolute paths to all directories
    """
    def __init__(self):
        pass

    @property
    def pyppa(self):
        path = os.path.dirname(__file__)
        path = os.path.dirname(path)
        return path

    @property
    def bin(self):
        path = os.path.join(self.pyppa, 'bin')
        return path

    @property
    def configuration(self):
        path = os.path.join(self.pyppa, 'Configuration')
        return path

    @property
    def facial_recognition(self):
        path = os.path.join(self.pyppa, 'FacialRecognition')
        return path

    @property
    def identity_profiles(self):
        path = os.path.join(self.pyppa, 'IdentityProfiles')
        return path

    @property
    def plugins(self):
        path = os.path.join(self.pyppa, 'Plugins')
        return path

    @property
    def scripts(self):
        path = os.path.join(self.pyppa, 'Scripts')
        return path

    @property
    def services(self):
        path = os.path.join(self.pyppa, 'Services')
        return path

    @property
    def tmp(self):
        path = os.path.join(self.pyppa, 'tmp')
        return path

    @property
    def utils(self):
        path = os.path.join(self.pyppa, 'utils')
        return path
