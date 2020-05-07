import cv2, face_recognition, os


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


def check_folder(folder):
    face_cascade = cv2.CascadeClassifier(
        "resources/haarcascade_frontalface_default.xml"
    )
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
                                crop_img = img[y : (y + h), x : (x + w)]
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
