from utils.nlp_utils import convert_sentence_to_matrix
import scipy.spatial as sp
from api_config import DATA_DIR
from mannerisms import Mannerisms
from Speaker import vocalize
import os
import numpy as np
from floating_listener import listen_and_convert
import pickle
import sqlite3


class PyPPA_ChatPlugin(object):

    def __init__(self, command):
        self.command = command
        self.COMMAND_HOOK_DICT = {'chat': ['chat with me', 'talk to me', 'let us chat', 'let us chat',
                                           "let's chat", "let's talk"]}
        self.FUNCTION_KEY_DICT = {'stop': ['exit chat', 'stop talking']}
        self.isBlocking = True

    def update_database(self):
        pass

    def function_handler(self, command_hook, spelling):
        # the command hook initiates a chat session in a blocking loop to prevent other commands from being interpreted
        # during normal speech
        # if one of the function keys is used, exit the session and go back to listening/non-blocking
        self.start_chat_session()

    def start_chat_session(self):
        while True:
            # get the user's input
            chat_text = listen_and_convert()
            print('User: {}'.format(chat_text))
            for func_hooks in self.FUNCTION_KEY_DICT:
                for spellings in self.FUNCTION_KEY_DICT[func_hooks]:
                    if spellings in chat_text:
                        print('Ending session')
                        self.end_chat_session()
                        return
            # convert to matrix
            input_matrix = convert_sentence_to_matrix(s=chat_text)
            sent_len = len(chat_text.split())
            # this use of static 100 is bad but works
            most_similar_matrix_tup = (100, None)
            for matrix_file in os.listdir(DATA_DIR + '/sentence_matrices'):
                if int(matrix_file.split('_')[0]) == sent_len:
                    arch_matrix = pickle.load(open(os.path.join(DATA_DIR+'/sentence_matrices', matrix_file), 'rb'))
                    distance = sp.distance.cdist(input_matrix, arch_matrix, 'cosine')
                    distance = np.nan_to_num(distance, copy=False)
                    cum_dist = 0
                    for i, dm in enumerate(distance):
                        cum_dist += dm[i]
                    # replace greater distance matrix with new closer one
                    if cum_dist < most_similar_matrix_tup[0]:
                        # to get table name cut out the sent_len and .p extension
                        matrix_table_name = matrix_file.split('_')[1]
                        matrix_table_name = matrix_table_name[:-2]
                        most_similar_matrix_tup = (cum_dist, matrix_table_name)
            # access the db to pull a response
            response_text = self.retrieve_response(most_similar_matrix_tup[1])
            vocalize(response_text)

    def retrieve_response(self, table_name):
        conn = sqlite3.connect(DATA_DIR+'/conversational_text/conversational_text.db')
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT response FROM {} ORDER BY frequency DESC'.format(table_name))
        except sqlite3.OperationalError:
            # if none table gets passed in this will happen
            return 'I could not understand that'
        response = cursor.fetchall()
        print(response)
        response = response[0][0]
        conn.commit()
        cursor.close()
        conn.close()
        print(response)
        return response

    def end_chat_session(self):
        # could use this later to store some info on prior chats
        self.isBlocking = False

