import cv2
import os
from pathlib import Path
import numpy as np


def check_folder(folder):
    face_cascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
    folderpaths = []
    for actor in os.listdir(folder):
        folderpaths.append(f"{folder}/{actor}")
    for actor in folderpaths:
        for path in os.listdir(actor):
            path_parsed = f"{actor}/{path}"
            try:
                img = cv2.imread(path_parsed)
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                if len(faces) == 0:
                    print(f"DELETED: no face found in {path_parsed}")
                    os.remove(path_parsed)
                else:
                    if not os.path.exists(f"{actor}/cropped/"):
                        os.makedirs(f"{actor}/cropped/")
                    (height, width) = img.shape[:2]
                    for (x, y, w, h) in faces:
                        # cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
                        crop_img = img[y : (y + h), x : (x + w)]
                        cv2.imwrite(f"{actor}/cropped/{path}", crop_img)
                        print(
                            f"SUCCES: saved cropped version of {actor}/cropped/{path}.jpg"
                        )
            except Exception as e:
                print(f"Could not load {path_parsed} - e")
                continue
