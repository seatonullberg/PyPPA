import Listener
'''
use this file to organize initialization such as threading across multiple sensory inputs
--when others are added
'''


if __name__ == "__main__":
    listen = Listener.InitializeBackgroundListening()
    listen.startup()
