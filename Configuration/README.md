**Configuration**

The Configuration object in this directory is intended to automate the process of
configuring this software as much as possible. Users should be expected to edit 
the configuration.yaml file with information that **only** they know (e.g. passwords,
local file paths, and API keys). All other information should be accounted for by developers.

**Environment Variables**

When a developer creates a new Plugin or Service, they may find it necessary to get 
user input. The way this configuration is structured, user input can be processed through the use of an Environment Variable. Note that this Environment Variable is **not**
a typical system wide variable. The scope is limited to this software package, but the idea is 
much the same. Developers can require user input through the use of these Environment Variables
so long as the data they require can be represented as a string (support for other data types may
be built in later if demand is high enough). In order to request this data, the developer must
provide keys in an environment.txt file that will be associated with the user input. 

**environment.txt files**

In order to enable the automatic configuration behavior, it is required that developers 
include an environment.txt file in their packages (even if it is empty). It should go without saying that
the name of the file **must** be environment.txt. The file should contain only the keys
of the environment variables which a package needs in order to function. Do not include
comments or values of any other sort in this file. Examples can be found in all of the 
Plugin and Service packages.

**autoconfig.py files**

To further automate the configuration process, developers may include an autoconfig.py
file in their package. This file is not required, but may be used to automate the configuration
of variables which are tedious for users to input. Once again, the file **must** be named
autoconfig.py. The file must also contain functions which have names corresponding to the 
Environment Variables which they aim to configure. For example, if a developer requires that
a data directory be created prior to the use of their functionality, they could write a function 
in their autoconfig.py file named DATA_DIRECTORY() which produces a directory on the user's system
and returns the path to that directory as the value of the Environment Variable 'DATA_DIRECTORY'.
These autoconfig.py files will be executed automatically for any Environment Variables that are not 
defined in the configuration.yaml file. It should be noted that a user supplied definition to an
Environment Variable will always override the autoconfig.py behavior.