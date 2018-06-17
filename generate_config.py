import os
import pickle
import copy

class ConfigurationGenerator(object):

    def __init__(self):
        self.base_path = os.getcwd()
        # this will become an object
        self.configuration = None

    '''
    File name properties
    '''
    @property
    def config_fn(self):
        return 'configuration.txt'

    @property
    def config_tmp_fn(self):
        return 'configuration.tmp'

    @property
    def environment_tmp_fn(self):
        return 'environment.tmp'

    @property
    def plugin_tmp_fn(self):
        return 'plugin.tmp'

    @property
    def background_tmp_fn(self):
        return 'background.tmp'

    def make(self):
        '''
        Construct a configuration.txt file and tests it for viability
        :return: None (writes configuration.txt)
        '''
        self._scan_base_environ()
        self._scan_plugins()
        self._scan_background_tasks()
        # generate the blacklist header for plugins and background tasks
        # use 'w' since this is the first reference to the file and it needs to be overwritten if exists
        with open(os.path.join(self.base_path, self.config_tmp_fn), 'w') as config_tmp:
            config_tmp.write('__BLACKLIST__\n')

        '''
        Handle Environment Variables tmp
        '''
        with open(os.path.join(self.base_path, self.environment_tmp_fn), 'r') as ev_tmp:
            lines = ev_tmp.read().splitlines()
            lines = [l for l in lines if l != '']
        with open(os.path.join(self.base_path, self.config_tmp_fn), 'a') as config_tmp:
            # add environment header to the tmp config
            config_tmp.write('\n__ENVIRONMENT_VARIABLES__\n')
            # iterate over parsed keys and write to tmp config
            for k in lines:
                config_tmp.write(k+'\n')

        '''
        Handle Plugins tmp
        '''
        with open(os.path.join(self.base_path, self.plugin_tmp_fn), 'r') as plugin_tmp:
            lines = plugin_tmp.read().splitlines()
            lines = [l for l in lines if l != '']
        with open(os.path.join(self.base_path, self.config_tmp_fn), 'a') as config_tmp:
            # add plugin header to config tmp
            config_tmp.write('\n__PLUGINS__\n')
            # iterate over plugins and their betas
            for k in lines:
                config_tmp.write(k+'\n')

        '''
        Handle Background Tasks tmp
        '''
        with open(os.path.join(self.base_path, self.background_tmp_fn), 'r') as background_tmp:
            lines = background_tmp.read().splitlines()
            lines = [l for l in lines if l != '']
        with open(os.path.join(self.base_path, self.config_tmp_fn), 'a') as config_tmp:
            # add background header to config tmp
            config_tmp.write('\n__BACKGROUND_TASKS__\n')
            # iterate over background tasks
            for k in lines:
                config_tmp.write(k+'\n')

        '''
        Run tests and raise errors
        '''
        results = self._run_tests()
        # raise errors if exist
        for err in results['environment_errors']:
            print('EnvironmentVariableError:')
            print(err)
        for err in results['plugin_errors']:
            print('PluginError:')
            print(err)
        for err in results['background_errors']:
            print('BackgroundTaskError:')
            print(err)
        # exit after errors are raised to allow user input
        for k in results:
            # the config dict does not contain errors so exclude it
            if len(results[k]) > 0 and k != 'config_dict':
                exit()
        # delete configuration.tmp if errors do not cause an exit
        os.remove(os.path.join(self.base_path, self.config_tmp_fn))

        '''
        Write configuration.txt from config_dict data
        '''
        config_dict = results['config_dict']
        with open(os.path.join(self.base_path, self.config_fn), 'w') as final_config:
            # fill out the blacklist
            final_config.write('__BLACKLIST__\n')
            for b in config_dict['blacklist']:
                final_config.write(b+'\n')

            # fill out the environment variables
            final_config.write('\n__ENVIRONMENT_VARIABLES__\n')
            for header in config_dict['environment_variables']:
                final_config.write(header+'\n')
                for ev in config_dict['environment_variables'][header]:
                    final_config.write(ev+'\n')

            # fill out the plugins
            final_config.write('\n__PLUGINS__\n')
            for header in config_dict['plugins']:
                final_config.write(header+'\n')
                for p in config_dict['plugins'][header]:
                    final_config.write(p+'\n')

            # fill out the background tasks
            final_config.write('\n__BACKGROUND_TASKS__\n')
            for header in config_dict['background_tasks']:
                final_config.write(header+'\n')
                for bt in config_dict['background_tasks'][header]:
                    final_config.write(bt+'\n')

        '''
        Construct picklable configuration object from config_dict data
        '''
        config_obj = Configuration(config_dict)
        # pickle the object
        config_pickle_path = [os.getcwd(), 'public_pickles', 'configuration.p']
        config_pickle_path = os.path.join('', *config_pickle_path)
        pickle.dump(config_obj, open(config_pickle_path, 'wb'))

    def _scan_base_environ(self):
        '''
        Read the base environment.txt file to collect the base environment variables
        :return: None (writes to self.environment_tmp_fn)
        '''
        # read ev from base ev file
        base_environment_file = os.path.join(self.base_path, 'environment.txt')
        with open(base_environment_file, 'r') as ev_file:
            e_vars = ev_file.readlines()
        # add base ev to the temp ev file
        with open(os.path.join(self.base_path, self.environment_tmp_fn), 'a') as ev_tmp:
            ev_tmp.write('__BASE__\n')
            for ev in e_vars:
                ev_tmp.write(ev)
            ev_tmp.write('\n')

    def _scan_plugins(self):
        '''
        Scan Plugin directory to collect plugin names and their specific environment variables
        :return: None (writes to self.environment_tmp.fn and self.plugin_tmp.fn)
        '''
        plugin_path = os.path.join(self.base_path, 'Plugins')
        plugin_directories = [os.path.join(plugin_path, d) for d in os.listdir(plugin_path)]
        plugin_directories = [pd for pd in plugin_directories if os.path.isdir(pd)]
        for pd in plugin_directories:
            # write in the headers to the tmp files
            dir_name = os.path.split(pd)[-1]
            if dir_name == '__pycache__':
                continue
            with open(os.path.join(self.base_path, self.environment_tmp_fn), 'a') as ev_tmp:
                ev_tmp.write('__{}__\n'.format(dir_name))
            with open(os.path.join(self.base_path, self.plugin_tmp_fn), 'a') as plugin_tmp:
                plugin_tmp.write('__{}__\n'.format(dir_name))
            # iterate over files in dir
            files = [os.path.join(pd, f) for f in os.listdir(pd)]
            files = [f for f in files if os.path.isfile(f)]
            for f in files:
                fname = os.path.split(f)[-1]
                if fname == "environment.txt":
                    # read the environment variable requirements
                    with open(f, 'r') as ev_file:
                        e_vars = ev_file.readlines()
                    # write the requirements to tmp file under their heading
                    with open(os.path.join(self.base_path, self.environment_tmp_fn), 'a') as ev_tmp:
                        for ev in e_vars:
                            ev_tmp.write(ev)
                        ev_tmp.write('\n')
                elif fname.endswith("_plugin.py") or fname.endswith("_beta.py"):
                    # open the plugin tmp file to record the found plugin or beta under its heading
                    with open(os.path.join(self.base_path, self.plugin_tmp_fn), 'a') as plugin_tmp:
                        plugin_tmp.write(fname+'\n')
                else:
                    pass

    def _scan_background_tasks(self):
        '''
        Scan BackgroundTasks directory to collect background task names and their specific environment variables
        :return: None (writes to self.environment_tmp_fn and self.background_tmp_fn)
        '''
        background_path = os.path.join(self.base_path, 'BackgroundTasks')
        background_directories = [os.path.join(background_path, d) for d in os.listdir(background_path)]
        background_directories = [bd for bd in background_directories if os.path.isdir(bd)]
        for bd in background_directories:
            # write in the headers to the tmp files
            dir_name = os.path.split(bd)[-1]
            if dir_name == '__pycache__':
                continue
            with open(os.path.join(self.base_path, self.environment_tmp_fn), 'a') as ev_tmp:
                ev_tmp.write('__{}__\n'.format(dir_name))
            with open(os.path.join(self.base_path, self.background_tmp_fn), 'a') as background_tmp:
                background_tmp.write('__{}__\n'.format(dir_name))

            # iterate over files in dir
            files = [os.path.join(bd, f) for f in os.listdir(bd)]
            files = [f for f in files if os.path.isfile(f)]
            for f in files:
                fname = os.path.split(f)[-1]
                if fname == "environment.txt":
                    # read the environment variable requirements
                    with open(f, 'r') as ev_file:
                        e_vars = ev_file.readlines()
                    # write the requirements to tmp file under their heading
                    with open(os.path.join(self.base_path, self.environment_tmp_fn), 'a') as ev_tmp:
                        for ev in e_vars:
                            ev_tmp.write(ev)
                        ev_tmp.write('\n')
                elif fname.endswith("_tasks.py"):
                    # open the background tmp file to record the found background tasks under its heading
                    with open(os.path.join(self.base_path, self.background_tmp_fn), 'a') as background_tmp:
                        background_tmp.write(fname + '\n')
                else:
                    pass

    def _run_tests(self):
        '''
        Compile the .tmp files into a configuration.tmp and check its compatibility with configuration.txt
        :return: dict() containing all the collected errors and final config_dict
        '''

        # read the .tmp config file
        config_tmp_dict = self._read_config(fname=os.path.join(self.base_path, self.config_tmp_fn))
        if os.path.isfile(os.path.join(self.base_path, self.config_fn)):
            config_dict = self._read_config(fname=os.path.join(self.base_path, self.config_fn))
        else:
            # rename the tmp file as the template, delete all .tmp files and throw empty config error
            _src = os.path.join(self.base_path, self.config_tmp_fn)
            _dst = os.path.join(self.base_path, self.config_fn)
            os.rename(src=_src, dst=_dst)
            raise ValueError("Blank Configuration File")
        # delete environment .tmp
        os.remove(os.path.join(self.base_path, self.environment_tmp_fn))
        # delete plugin .tmp
        os.remove(os.path.join(self.base_path, self.plugin_tmp_fn))
        # delete background .tmp
        os.remove(os.path.join(self.base_path, self.background_tmp_fn))

        '''
        Check Environment Variables
        '''
        environment_errors = []
        # use explicit list to force copy of keys
        # https://stackoverflow.com/questions/11941817/how-to-avoid-runtimeerror-dictionary-changed-size-during-iteration-error
        for k_tmp, k in zip(list(config_tmp_dict['environment_variables']),
                            list(config_dict['environment_variables'])):
            # check configuration itself to make sure all variables are defined
            # ignore all the headers blacklisted in config
            if k not in config_dict['blacklist']:
                for ev in config_dict['environment_variables'][k]:
                    if len(ev.split('=')) > 2:
                        environment_errors.append("Malformed definition (too many '='): {ev} in {k}\n".format(ev=ev,
                                                                                                              k=k))
                    elif len(ev.split('=')) == 1:
                        environment_errors.append("Undefined environment variable {ev} in {k}\n".format(ev=ev,
                                                                                                        k=k))
                    else:
                        # the definition has a '='
                        if ev.split('=')[1] == '':
                            environment_errors.append("Undefined environment variable {ev} in {k}\n".format(ev=ev,
                                                                                                            k=k))

            # compare config to config_tmp
            if k_tmp not in config_dict['blacklist']:
                try:
                    # find what environment variables are in config_tmp but not in config
                    config_tmp_ev = [ev.split('=')[0] for ev in config_tmp_dict['environment_variables'][k_tmp]]
                    config_ev = [ev.split('=')[0] for ev in config_dict['environment_variables'][k_tmp]]
                    deltas = [ev for ev in config_tmp_ev if
                              ev not in config_ev]
                except KeyError:
                    # the config dict does not have the heading that is in config_tmp
                    # add the entire set of environment variables with header to config
                    config_dict['environment_variables'][k_tmp] = config_tmp_dict['environment_variables'][k_tmp]
                    environment_errors.append("All environment variables from {} are undefined\n".format(k_tmp))
                else:
                    # append only the new environment variables to config
                    for d in deltas:
                        config_dict['environment_variables'][k_tmp].append(d)
                        environment_errors.append("The environment variable {ev} in {k_tmp} is undefined\n".format(ev=d,
                                                                                                                   k_tmp=k_tmp))

        '''
        Check Plugins
        '''
        plugin_errors = []
        for k_tmp, k in zip(list(config_tmp_dict['plugins']),
                            list(config_dict['plugins'])):
            if k not in config_dict['blacklist']:
                # ensure each plugin header contains a _plugin.py file
                containsPlugin = False
                for fname in config_dict['plugins'][k]:
                    if fname.endswith('_plugin.py'):
                        containsPlugin = True
                if not containsPlugin:
                    plugin_errors.append("Unable to find plugin file in {}\n".format(k))

                # check if config has plugins not found in config_tmp
                try:
                    bad_deltas = [p for p in config_dict['plugins'][k] if
                                  p not in config_tmp_dict['plugins'][k]]
                except KeyError:
                    # the entire header is miossing from config_tmp
                    plugin_errors.append("Plugin {} present in configuration.txt is not found in directory\n".format(k))
                else:
                    # throw specific errors for missing files
                    for bd in bad_deltas:
                        plugin_errors.append("Plugin or beta file {} present in configuration.txt not found in directory\n".format(bd))

            if k_tmp not in config_dict['blacklist']:
                try:
                    deltas = [p for p in config_tmp_dict['plugins'][k_tmp] if
                              p not in config_dict['plugins'][k_tmp]]
                except KeyError:
                    # the config dict does not have the heading that is in config_tmp
                    # add the entire set of plugin/betas with header to config
                    config_dict['plugins'][k_tmp] = config_tmp_dict['plugins'][k_tmp]
                else:
                    # append only the plugin or betas to config
                    for d in deltas:
                        config_dict['plugins'][k_tmp].append(d)

        '''
        Check Background Tasks
        '''
        # auto add if background task found in tmp but not in config
        # -- if not blacklisted
        background_errors = []
        for k_tmp, k in zip(list(config_tmp_dict['background_tasks']),
                            list(config_dict['background_tasks'])):
            if k not in config_dict['blacklist']:
                # ensure each background header contains a _tasks.py file
                containsTasks = False
                for fname in config_dict['background_tasks'][k]:
                    if fname.endswith('_tasks.py'):
                        containsTasks = True
                if not containsTasks:
                    background_errors.append("Unable to find tasks file in {}\n".format(k))

                # check if config has tasks not found in config_tmp
                try:
                    bad_deltas = [bt for bt in config_dict['background_tasks'][k] if
                                  bt not in config_tmp_dict['background_tasks'][k]]
                except KeyError:
                    # the entire header is missing from config_tmp
                    background_errors.append("BackgroundTask {} present in configuration.txt is not found in directory\n".format(k))
                else:
                    # throw specific errors for missing files
                    for bd in bad_deltas:
                        plugin_errors.append(
                            "BackgroundTask {} present in configuration.txt not found in directory\n".format(bd))

            if k_tmp not in config_dict['blacklist']:
                try:
                    deltas = [bt for bt in config_tmp_dict['background_tasks'][k_tmp] if
                              bt not in config_dict['background_tasks'][k_tmp]]
                except KeyError:
                    # the config dict does not have the heading that is in config_tmp
                    # add the entire set of background tasks with header to config
                    config_dict['background_tasks'][k_tmp] = config_tmp_dict['background_tasks'][k_tmp]
                else:
                    # append only the task files to config
                    for d in deltas:
                        config_dict['background_tasks'][k_tmp].append(d)

        return {'environment_errors': environment_errors,
                'plugin_errors': plugin_errors,
                'background_errors': background_errors,
                'config_dict': config_dict}

    def _read_config(self, fname):
        # read either the .txt or .tmp files and return a dict of info
        '''
        Clarity method to break out from the testing code and generate easy to analyze dicts
        :param fname: filename of the configuration to parse
        :return: d dict() contains the parsed configuration information
        '''
        d = {}
        d['blacklist'] = []
        d['environment_variables'] = {}
        d['plugins'] = {}
        d['background_tasks'] = {}

        with open(os.path.join(self.base_path, fname), 'r') as config:
            config_data = config.read().splitlines()
            config_data = [cd for cd in config_data if cd != '']

        # fill in the config dict
        for i, cd in enumerate(config_data):
            # get blacklisted plugins and background tasks
            if cd == '__BLACKLIST__':
                # stop when the next header is reached
                for data in config_data[i+1:]:
                    if data in ['__ENVIRONMENT_VARIABLES__', '__PLUGINS__', '__BACKGROUND_TASKS__']:
                        break
                    else:
                        d['blacklist'].append(data)
            # map environment variables to their heading
            elif cd == '__ENVIRONMENT_VARIABLES__':
                header = None
                for data in config_data[i+1:]:
                    if data in ['__PLUGINS__', '__BACKGROUND_TASKS__', '__BLACKLIST__']:
                        break
                    # make the sub header a key to hold environment variables
                    elif data.startswith('__') and data.endswith('__'):
                        header = data
                        d['environment_variables'][header] = []
                    else:
                        d['environment_variables'][header].append(data)

            # match plugins and beta plugins
            elif cd == '__PLUGINS__':
                header = None
                for data in config_data[i+1:]:
                    if data in ['__BACKGROUND_TASKS__', '__BLACKLIST__', '__ENVIRONMENT_VARIABLES__']:
                        break
                    elif data.startswith('__') and data.endswith('__'):
                        header = data
                        d['plugins'][header] = []
                    elif data.endswith('_plugin.py') or data.endswith('_beta.py'):
                        d['plugins'][header].append(data)

            # map background tasks to headings
            elif cd == '__BACKGROUND_TASKS__':
                header = None
                for data in config_data[i+1:]:
                    if data in ['__BLACKLIST__', '__ENVIRONMENT_VARIABLES__', '__PLUGINS__']:
                        break
                    elif data.startswith('__') and data.endswith('__'):
                        header = data
                        d['background_tasks'][header] = []
                    else:
                        d['background_tasks'][header].append(data)

            # for non interesting lines
            else:
                pass

        return d


class Configuration(object):

    def __init__(self, config_dict):
        self.config_dict = config_dict

    @property
    def port_map(self, start=5555):
        # start is the port number at which mapping begins
        # map all plugins and betas to a port for client server connections
        pmap = {}
        for key, val in self.plugins.items():
            pmap[key] = start
            start += 1
            for v in val:
                pmap[v] = start
                start += 1
        return pmap

    @property
    def environment_variables(self):
        # nested dict of environment variables by header
        env_dict = {}
        # since environment variables are unique only to a plugin folder (not individual betas)
        # use headers as keys rather than filenames without extensions such as in plugins
        # i realize this is not ideal...
        for key, val in self.config_dict['environment_variables'].items():
            env_dict[key] = {}
            for v in val:
                v = v.split('=')
                var_name = v[0]
                var_value = v[1]
                env_dict[key][var_name] = var_value
        return env_dict

    @property
    def plugins(self):
        plugins_dict = {}
        for header in self.config_dict['plugins']:
            plugin = None
            betas = []
            command_hook_dict = None
            modifiers = None
            for fname in self.config_dict['plugins'][header]:
                name = fname.replace('.py', '')
                # extract command hook dict and modifiers to add to the config
                command_hook_dict, modifiers = self._extract_chd_and_m(name=name)
                if name.endswith('_plugin'):
                    plugin = name
                elif name.endswith('_beta'):
                    betas.append(name)
            plugins_dict[plugin] = {}
            plugins_dict[plugin]['betas'] = betas
            plugins_dict[plugin]['command_hook_dict'] = command_hook_dict
            plugins_dict[plugin]['modifiers'] = modifiers
        return plugins_dict

    @property
    def background_tasks(self):
        # list of background tasks
        background_list = []
        for key, val in self.config_dict['background_tasks'].items():
            # the headers are essentially redundant for background tasks at this stage in their development
            for v in val:
                background_list.append(v)
        return background_list

    def rebuild(self):
        '''
        Rebuild the configuration object to reflect any changes made to the directory or config file
        :return: None
        '''
        cg = ConfigurationGenerator()
        cg.make()

    def _extract_chd_and_m(self, name):
        '''
        import the command hook dict and modifiers from a temporary instance of the plugin or beta passed in
        :param name: str() name of the plugin or beta to extract from
        :return: dict() command_hook_dict, dict() modifiers
        '''
        # convert name to class name
        assert type(name) == str()
        plugin_class_name = name.split('_')
        plugin_class_name = [p.capitalize() for p in plugin_class_name]
        plugin_class_name = ''.join(plugin_class_name)
        _path = "Plugins.{}".format(name)
        obj_plugin = None
        import_str = "from {_path} import {_class} as obj_plugin".format(_path=_path,
                                                                         _class=plugin_class_name)
        # import the plugin class to obj_plugin
        exec(import_str)
        # tooltips says 'uncallable' because it doesn't know obj_plugin is a class
        obj_plugin = obj_plugin()
        chd = copy.deepcopy(obj_plugin.COMMAND_HOOK_DICT)
        m = copy.deepcopy(obj_plugin.MODIFIERS)
        # force delete to ensure no floating plugin objects taking up memory
        del obj_plugin
        return chd, m


if __name__ == "__main__":
    cg = ConfigurationGenerator()
    cg.make()
