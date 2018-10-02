import os
import cv2


def process(input_path):
    """
    Preprocesses images in input_path for facial recognition
    :param input_path: (str) absolute path to a directory of facial images
    """
    # load cascade file
    pyppa_dir = os.path.dirname(__file__)
    pyppa_dir = os.path.dirname(pyppa_dir)
    casc_path = os.path.join(pyppa_dir, "bin", "frontal_face_cascade.xml")
    face_cascade = cv2.CascadeClassifier(casc_path)

    # iterate through images
    for fname in os.listdir(input_path):
        image_path = os.path.join(input_path, fname)
        image = cv2.imread(image_path)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # convert to gray scale
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=20,
            minSize=(100, 100)
        )

        if len(faces) != 1:  # only accept single face images
            continue

        for (x, y, w, h) in faces:
            # crop image around area of face to (100x100)
            crop = gray[y:y + h, x:x + w]
            crop = cv2.resize(crop,
                              dsize=(100, 100),
                              interpolation=cv2.INTER_CUBIC)

            # TODO: Rotate crop so that the eyes are aligned

            # generate path in /IdentityProfiles/
            dir_name = os.path.basename(input_path)
            outdir = os.path.join(pyppa_dir,
                                  "IdentityProfiles",
                                  dir_name)
            # make dir if not exists
            if not os.path.isdir(outdir):
                os.makedirs(outdir)
            # save file
            outfile = os.path.join(outdir, fname)
            cv2.imwrite(filename=outfile, img=crop)
