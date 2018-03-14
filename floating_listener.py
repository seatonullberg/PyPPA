import speech_recognition as sr


def listen_and_convert():
    '''
    Listen to the user and convert voice command to string command with no call to process_command
    :return: command (str) vocal command converted to text
    '''
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source)
        print('Speak: ')
        audio = r.listen(source)
    command = ''
    try:
        command = r.recognize_google(audio_data=audio)
    except sr.UnknownValueError:
        print("Could not understand audio")
    except sr.RequestError as e:
        print("Google Cloud error; {0}".format(e))
    return command.lower()
