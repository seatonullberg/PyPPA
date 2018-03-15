import speech_recognition as sr
from Speaker import vocalize
from config import LISTENER_ENERGY_THRESHOLD, PLUGIN_LIST
from mannerisms import Mannerisms


def process_command(command):
    '''
    :param command: (str) string form of audio command given by user
    :return: None
    '''
    for plugin in PLUGIN_LIST:
        # check all installed modules
        plugin = plugin(command)
        for command_hook in plugin.COMMAND_HOOK_DICT:
            for spelling in plugin.COMMAND_HOOK_DICT[command_hook]:
                if spelling in command:
                    # carry out request and go back to listening
                    plugin.function_handler(command_hook, spelling)
                    return
    # if all fail
    vocalize(Mannerisms('unknown_command', {'command': command}).final_response)


def update_plugins():
    for plugin in PLUGIN_LIST:
        p = plugin('')
        p.update_database()
    print('Updates Complete')


class InitializeBackgroundListening(object):
    '''
    Class to be used on open or on sleep
    listens silently for an attention trigger with the sphinx listener
    then switches to the google cloud listener for actual command interpretation
    '''

    def __init__(self):
        self.triggers = ['hey', 'auto', 'Auto', 'wake', 'up']
        self.r = sr.Recognizer()
        self.r.dynamic_energy_threshold = False
        self.r.energy_threshold = LISTENER_ENERGY_THRESHOLD
        update_plugins()
        self.call_to_attention()

    def call_to_attention(self):
        while True:
            with sr.Microphone() as source:
                self.r.adjust_for_ambient_noise(source)
                try:
                    audio = self.r.listen(source, timeout=2)
                except sr.WaitTimeoutError:
                    print('timeout')
                else:
                    try:
                        command = self.r.recognize_google(audio_data=audio)
                    except sr.UnknownValueError:
                        print('unknown value error')
                    else:
                        print('background_listener heard: ' + command)
                        for trigger in self.triggers:
                            if trigger in command:
                                vocalize(Mannerisms('await_command', None).final_response)
                                self.collect_command()
                                return

    def collect_command(self):
        with sr.Microphone() as source:
            self.r.adjust_for_ambient_noise(source)
            print('Speak a command: ')
            audio = self.r.listen(source, timeout=5)
            try:
                command = self.r.recognize_google(audio_data=audio)
            except sr.UnknownValueError:
                vocalize(Mannerisms('unknown_audio', None).final_response)
            except sr.RequestError as e:
                vocalize(Mannerisms('error', None).final_response)
                print("Google Cloud Error; {0}".format(e))
            else:
                print('passed command: ' + command.lower())
                process_command(command.lower())


if __name__ == "__main__":
    InitializeBackgroundListening()
