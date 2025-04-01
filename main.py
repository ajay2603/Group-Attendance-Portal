import cv2
import face_recognition
import numpy as np
import os

# Load encodings and class names
ENCODING_FILE = "encodings.npy"
CLASSNAMES_FILE = "classnames.npy"

# Load encodings & class names
if os.path.exists(ENCODING_FILE) and os.path.exists(CLASSNAMES_FILE):
    encodeListKnown = np.load(ENCODING_FILE, allow_pickle=True)
    classNames = np.load(CLASSNAMES_FILE, allow_pickle=True)
    print("Encodings loaded successfully!!!")
else:
    print("Error: Encodings not found. Please run encoding.py first!")
    exit()

def upload_and_recognize(file_bytes):
    """
    Process the image and recognize faces.
    Args:
        file_bytes: Image file bytes (from request.files['file'].read())
    Returns:
        recognized_names: List of recognized names
        processed_image: Processed image with bounding boxes
    """
    # Decode the image from bytes
    img = cv2.imdecode(np.frombuffer(file_bytes, np.uint8), cv2.IMREAD_COLOR)

    # Resize and convert image for processing
    imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

    # Detect faces and encodings
    facesCurFrame = face_recognition.face_locations(imgS)
    encodesCurFrame = face_recognition.face_encodings(imgS, facesCurFrame)

    recognized_names = set()

    for encodeFace, faceLoc in zip(encodesCurFrame, facesCurFrame):
        matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
        faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
        matchIndex = np.argmin(faceDis)

        if matches[matchIndex]:
            name = classNames[matchIndex].upper()
            recognized_names.add(name)
            # Draw rectangle and label on the image
            y1, x2, y2, x1 = faceLoc
            y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.rectangle(img, (x1, y2 - 35), (x2, y2), (0, 255, 0), cv2.FILLED)
            cv2.putText(img, name, (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 0), 2)

    recognized_names = list(recognized_names)
    recognized_names = sorted(recognized_names)
    print("Recognized Names:", recognized_names)
    return recognized_names, img