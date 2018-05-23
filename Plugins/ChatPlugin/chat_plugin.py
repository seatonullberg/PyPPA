'''
No longer works as underlying model undergoes some experimentation
'''

from utils.nlp_utils import convert_sentence_to_matrix
import scipy.spatial as sp
from private_config import DATA_DIR
from mannerisms import Mannerisms
from Speaker import vocalize
import os
import numpy as np
from Plugins.base_plugin import BasePlugin
import pickle
import sqlite3


class PyPPA_ChatPlugin(BasePlugin):

    def __init__(self, command):
        self.COMMAND_HOOK_DICT = {'chat': ['chat with me', 'talk to me',
                                           'let us chat', 'let us talk',
                                           "let's chat", "let's talk"]}
        self.MODIFIERS = {'chat': {}}
        self.FUNCTION_KEY_DICT = {'stop': ['exit chat', 'stop talking']}
        super().__init__(command=command,
                         command_hook_dict=self.COMMAND_HOOK_DICT,
                         modifiers=self.MODIFIERS)

    def function_handler(self, args=None):
        # the command hook initiates a chat session in a blocking loop to prevent other commands from being interpreted
        # during normal speech
        self.start_chat_session()

    def start_chat_session(self):
        stop_tokens = ['exit chat', 'stop talking']
        while True:
            # get the user's input
            chat_text = self.listener().listen_and_convert()
            print('User: {}'.format(chat_text))
            # see if user wants to stop chat
            for st in stop_tokens:
                if chat_text == st:
                    print('Ending session.')
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
        # pulling at random one of the highest frequency would seem more natural
        conn = sqlite3.connect(DATA_DIR+'/conversational_text/conversational_text.db')
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT * FROM {} ORDER BY frequency DESC'.format(table_name))
        except sqlite3.OperationalError:
            # if none table gets passed in this will happen
            return 'I could not understand that'
        result = cursor.fetchall()

        # allow for some randomness when there are multiple frequent responses
        top_responses = []
        if len(result) == 1:
            top_responses.append(result[0][0])
        else:
            for i, r in enumerate(result):
                # compare frequency count and stop when a lower frequency is hit
                # prevent indexing issue
                if i == 0:
                    top_responses.append(r[0])
                elif r[1] < result[i-1][1]:
                    break
                else:
                    top_responses.append(r[0])

        seed = np.random.randint(0, len(top_responses))
        response = top_responses[seed]
        conn.commit()
        cursor.close()
        conn.close()
        print(top_responses)
        print('PyPPA: '+response)
        return response

    def end_chat_session(self):
        # could use this later to store some info on prior chats
        self.isBlocking = False

