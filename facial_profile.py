import os
import pickle
from private_config import DATA_DIR
import cv2


class FacialProfile(object):
    '''
    Object used to define the identity of a facial image embedding.
    Produces a text file which can be manually edited to produce rich identities.
    A blank profile object contains:
        int(id) -unique identifier number
        array(image) -pixel array of image containing the face
        array(embedding) -embedding array used for unique identification
    Other attributes can also be defined:
        tuple(name) -first and last name
        list(subroutines) -functions to execute upon recognition of the face
    '''

    def __init__(self):
        pass

    # TODO: this doesn't do what i thought it did
    def __dict__(self):
        # creates a smooth way of returning information about ALL FacialProfiles
        # str(_id) keys and tuple(name, embedding) values
        pairings = []
        for fname in os.listdir(os.path.join(DATA_DIR, 'facial_profiles')):
            # do not iterate over the embedding files
            if fname.endswith('.txt'):
                # add the id
                pairings.append([fname.split('_')[0]])
                with open(os.path.join(DATA_DIR, 'facial_profiles', fname), 'r') as f:
                    lines = f.readlines()
                    for i, l in enumerate(lines):
                        if l.startswith('name'):
                            name = lines[i + 1][1:-1]
                            pairings[-1].append(name)
                            break
                encoding_path = [DATA_DIR, 'facial_profiles', '{}_encoding.p'.format(fname.split('_')[0])]
                encoding = pickle.load(open(os.path.join('', *encoding_path), 'rb'))
                pairings[-1].append(encoding)
        d = {p[0]: (p[1], p[2]) for p in pairings}
        return d

    def write_profile(self, data):
        profile_list = os.listdir(os.path.join(DATA_DIR, 'facial_profiles'))
        profile_list = [p for p in profile_list if p.endswith('.txt')]
        if len(profile_list) == 0:
            file_index = 0
        else:
            indices = [fname.split('_')[0] for fname in profile_list]
            file_index = max([int(i) for i in indices])+1
        profile_path = [DATA_DIR, 'facial_profiles', '{}_profile.txt'.format(file_index)]
        with open(os.path.join('', *profile_path), 'w') as f:
            for key in data:
                if key == 'encoding':
                    encoding_path = [DATA_DIR, 'facial_profiles', '{}_encoding.p'.format(file_index)]
                    pickle.dump(data[key], open(os.path.join('', *encoding_path), 'wb'))
                elif key == 'image':
                    image_path = [DATA_DIR, 'facial_profiles', '{}_image.jpg'.format(file_index)]
                    cv2.imwrite(os.path.join('', *image_path), data[key])
                else:
                    f.write('{}:\n'.format(key))
                    f.write('\t' + str(data[key]) + '\n')

    def read_profile(self, _id):
        profile = open(os.path.join(DATA_DIR, 'facial_profiles', '{}_profile.txt'.format(_id)), 'r').readlines()
        encoding = pickle.load(open(os.path.join(DATA_DIR, 'facial_profiles', '{}_encoding.p'.format(_id)), 'rb'))
        pairings = []
        for line in profile:
            if line.endswith(':\n'):
                pairings.append(line[:-1])
            elif line.startswith('\t'):
                # remove the initial tab and ending newline
                pairings[-1] = (pairings[-1], line[1:-1])
            else:
                continue
        profile = {p[0]: p[1] for p in pairings}
        return profile, encoding
