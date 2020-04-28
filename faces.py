import cv2
import os
from pathlib import Path
import numpy as np


def check_folder(folder):
    face_cascade = cv2.CascadeClassifier("resources/haarcascade_frontalface_default.xml")
    folderpaths = []
    for actor in os.listdir(folder):
        try:
            folderpaths.append(f"{folder}/{actor}")
        except Exception as e:
            continue
    for actor in folderpaths:
        try:
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
                                f"SUCCES: saved cropped version of {actor}/cropped/{path}"
                            )
                except Exception as e:
                    print(f"Could not load {path_parsed} - {e}")
                    continue
        except Exception as e:
            print(f"Could not load a file - {e}")
            continue

def preprocess_image(folder, width, height, grayscale):
    #TODO grayscale
    subfolder_paths = []
    for subfolder in os.listdir(folder):
        try:
            subfolder_paths.append(f"{folder}/{subfolder}")
        except Exception as e:
            print(f"Could not load folder: {subfolder}")
            continue
    for subfolder in subfolder_paths:
        try:
            for path in os.listdir(subfolder):
                path_parsed = f"{subfolder}/{path}"
                try:
                    img = cv2.imread(path_parsed)
                    if not os.path.exists(f"{subfolder}/preprocessed/"):
                        os.makedirs(f"{subfolder}/preprocessed/")
                    # Rescaling with preserved aspect ratio
                    # scale_percent = 60
                    # height = int(img.shape[0] * scale_percent / 100)
                    # width = int(img.shape[1] * scale_percent / 100)
                    dim = (width, height)
                    resized = cv2.resize(img, dim, interpolation=cv2.INTER_AREA)
                    if grayscale:
                        resized = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
                    cv2.imwrite(f"{subfolder}/preprocessed/{path}", resized)
                    print(
                        f"SUCCES: saved resized version of {subfolder}/preprocessed/{path}"
                    )

                except Exception as e:
                    print(f"Could not load {path_parsed} - {e}")
                    continue
        except Exception as e:
            print(f"Could not load a file - {e}")
            continue
