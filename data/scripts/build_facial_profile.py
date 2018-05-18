'''
Script used to manually create facial profiles by supplying name and image
'''

import argparse
import face_recognition
import cv2
import os
import pickle


def write_profile(data, data_dir):
    DATA_DIR = data_dir
    profile_list = os.listdir(os.path.join(DATA_DIR, 'facial_profiles'))
    profile_list = [p for p in profile_list if not p.endswith('.p')]
    if len(profile_list) == 0:
        file_index = 0
    else:
        indices = [fname.split('_')[0] for fname in profile_list]
        file_index = max([int(i) for i in indices]) + 1
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--image_path', default=None, help='Path to image to create embedding')
    parser.add_argument('--name', default=None, help='Name to associate with the profile')
    parser.add_argument('--data_dir', default=None, help='Path to directory containing the facial profiles directory')
    args = parser.parse_args()
    image = face_recognition.load_image_file(args.image_path)
    # only use pictures with one face in them
    face_encoding = face_recognition.face_encodings(image)[0]
    write_profile({'name': args.name,
                   'encoding': face_encoding},
                  data_dir=args.data_dir)


if __name__ == "__main__":
    main()
