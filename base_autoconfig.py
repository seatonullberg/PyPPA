import yaml
import os


class AutoConfig(object):

    def __init__(self, target_dict, is_environment_variable):
        assert type(target_dict) == dict
        assert type(is_environment_variable) == bool
        self.target_dict = target_dict
        self.is_environment_variable = is_environment_variable

    @property
    def package_name(self):
        # name of the plugin or service which this autoconfig applies to
        # based on file location
        path = os.path.dirname(__file__)
        name = os.path.basename(path)
        return name

    @property
    def configuration_path(self):
        filename = 'configuration.yaml'
        path = os.path.dirname(__file__)
        if not self.is_environment_variable:
            path = os.path.join(path, filename)
            return path
        else:
            path = os.path.dirname(path)
            path = os.path.join(path, filename)
            return path

    def configure(self):
        # iterate through target_dict to execute all desired functions
        for k, v in self.target_dict:
            if self.is_environment_variable:
                # place the generated value in the configuration
                ev_value = v()
                self._modify_configuration(k, ev_value)
            else:
                # let the script run to modify the resource
                v()

    def _modify_configuration(self, key, value):
        # open the configuration and fill in entries
        # only used when environment_variable=False
        user_config = yaml.load(stream=open(self.configuration_path, 'r'))
        current_value = user_config['ENVIRONMENT_VARIABLES'][key]
        if current_value == '':
            user_config['ENVIRONMENT_VARIABLES'][key] = value
