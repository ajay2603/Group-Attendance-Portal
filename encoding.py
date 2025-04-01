import cv2
import numpy as np
import face_recognition
import os

ENCODING_FILE = "encodings.npy"
CLASSNAMES_FILE = "classnames.npy"
TRAINING_PATH = "Training_images"

def load_training_images():
    images = []
    classNames = []
    myList = os.listdir(TRAINING_PATH)
    print("Training Images:", myList)
    
    for cl in myList:
        curImg = cv2.imread(f"{TRAINING_PATH}/{cl}")
        images.append(curImg)
        classNames.append(os.path.splitext(cl)[0])

    return images, classNames

def find_encodings(images):
    encodeList = []
    for img in images:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(img)
        if encodings:  # Ensure at least one face is found
            encodeList.append(encodings[0])
    return encodeList

if __name__ == "__main__":
    print("Generating face encodings...")

    images, classNames = load_training_images()
    encodeListKnown = find_encodings(images)

    np.save(ENCODING_FILE, encodeListKnown)
    np.save(CLASSNAMES_FILE, classNames)

    print("Encoding process completed")
    print(f"Encodings saved to {ENCODING_FILE}")
