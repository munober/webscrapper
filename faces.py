import cv2, face_recognition, os
from math import floor
from random import randint


def second_filter(path):
    folderpaths = []
    for item in os.listdir(path):
        try:
            folderpaths.append(f"{path}/{item}")
        except Exception as e:
            continue
    for folder in folderpaths:
        for item in os.listdir(folder):
            img_fr = face_recognition.load_image_file(f"{folder}/{item}")
            faces_fr = face_recognition.face_locations(img_fr)
            if len(faces_fr) == 0:
                print(f"DELETED by second face filter: {item}")
                os.remove(f"{folder}/{item}")


def check_folder(folder, xml_file, padding):
    face_cascade = cv2.CascadeClassifier(xml_file)
    folderpaths = []
    for actor in os.listdir(folder):
        try:
            folderpaths.append(f"{folder}/{actor}")
        except Exception as e:
            continue
    for actor in folderpaths:
        if os.path.isdir(actor):
            try:
                for path in os.listdir(actor):
                    path_parsed = f"{actor}/{path}"
                    try:
                        img = cv2.imread(path_parsed)
                        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                        img_fr = face_recognition.load_image_file(path_parsed)
                        faces_fr = face_recognition.face_locations(img_fr)
                        if len(faces) == 0 or len(faces_fr) == 0:
                            print(f"DELETED: no face found in {path_parsed}")
                            os.remove(path_parsed)
                        if len(faces) and len(faces_fr):
                            saved_faces = 0
                            for (x, y, w, h) in faces:
                                side = min(w,h)
                                padding_ratio = padding # percent of side length
                                padding_increment_root = floor(padding_ratio / 100 * side)
                                # difference = floor(0.5 * padding_increment_root) # deprecated
                                padding_increment = []
                                for i in range(4):
                                    # old way of doing it, deprecated
                                    # padding_increment.append(padding_increment_root + randint(-difference,difference))
                                    if i == 0:
                                        random_seed = randint(0, 80)
                                        padding_increment.append(floor(random_seed / 100 * padding_increment_root))
                                        padding_increment.append(floor((100 - random_seed) / 100 * padding_increment_root))
                                    if i == 2:
                                        random_seed = randint(0, 80)
                                        padding_increment.append(floor(random_seed / 100 * padding_increment_root))
                                        padding_increment.append(floor((100 - random_seed) / 100 * padding_increment_root))
                                    print("added this much padding: ", padding_increment[i], " to side ", i)

                                # crop_img = img[y : (y + h), x : (x + w)] # no padding
                                crop_img = img[(y - padding_increment[0]): (y + h + padding_increment[1]), (x - padding_increment[2]): (x + w + padding_increment[3])]
                                if not os.path.exists(
                                    f"./export_preprocessing/cropped/{actor[10:]}/"
                                ):
                                    os.makedirs(
                                        f"./export_preprocessing/cropped/{actor[10:]}/"
                                    )
                                cv2.imwrite(
                                    f"./export_preprocessing/cropped/{actor[10:]}/{path[:-4]}{saved_faces}.jpg",
                                    crop_img,
                                )
                                saved_faces += 1
                                print(
                                    f"SUCCES: saved cropped version of {actor[10:]}/{path}"
                                )
                    except Exception as e:
                        print(f"Could not load {path_parsed} - {e}")
                        continue
            except Exception as e:
                if e.errno != 20:
                    print(f"{actor} not a folder: {e}")
                    continue


def preprocess_image(folder, width, height, grayscale):
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
                    dim = (width, height)
                    resized = cv2.resize(img, dim, interpolation=cv2.INTER_AREA)
                    if grayscale:
                        resized = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
                        if not os.path.exists(
                            f"./export_preprocessing/{width}_{height}_gs/{subfolder[30:]}/"
                        ):
                            os.makedirs(
                                f"./export_preprocessing/{width}_{height}_gs/{subfolder[30:]}/"
                            )
                        cv2.imwrite(
                            f"./export_preprocessing/{width}_{height}_gs/{subfolder[30:]}/{path}",
                            resized,
                        )
                    elif not grayscale:
                        if not os.path.exists(
                            f"./export_preprocessing/{width}_{height}/{subfolder[30:]}/"
                        ):
                            os.makedirs(
                                f"./export_preprocessing/{width}_{height}/{subfolder[30:]}/"
                            )
                        cv2.imwrite(
                            f"./export_preprocessing/{width}_{height}/{subfolder[30:]}/{path}",
                            resized,
                        )

                    print(f"Processed: {subfolder[31:]}/{path}")

                except Exception as e:
                    print(f"Could not load {path_parsed} - {e}")
                    continue
        except Exception as e:
            print(f"Could not load a file - {e}")
            continue
