'''
This file is to remain in /bin so that the resources can be properly configured on init
'''

import os
import sys
import stat
from base_autoconfig import AutoConfig


def mimic():
    # make the mimic script executable
    mimic_path = os.path.join(os.getcwd(), 'mimic', 'mimic')
    st = os.stat(mimic_path)
    os.chmod(mimic_path, st.st_mode | stat.S_IEXEC)


def chromedriver():
    # make the chromedriver script executable
    driver_path = os.path.join(os.getcwd(), 'chromedriver', 'chromedriver')
    st = os.stat(driver_path)
    os.chmod(driver_path, st.st_mode | stat.S_IEXEC)


def python():
    # make sure python has access to the dependencies
    # sys.path.append(os.getcwd())
    pass


if __name__ == "__main__":
    # initialize an AutoConfig object to modify the resources
    _dict = {'mimic': mimic,
             'chromedriver': chromedriver,
             'python3.6.5': python}
    ac = AutoConfig(target_dict=_dict,
                    is_environment_variable=False)
    ac.configure()
