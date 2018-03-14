import pyttsx3


def vocalize(input_string):
    '''
    :param input_string: (str) string to be read off in computer voice
    :return: None
    '''
    engine = pyttsx3.init()
    engine.say(str(input_string))
    engine.runAndWait()
    engine.stop()
