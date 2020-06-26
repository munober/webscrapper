import os, cv2, face_recognition

xml_file = "resources/haarcascade_frontalface_default.xml"
data_path = "dataset"
width = 150
height = 150
dim = (width, height)
region = 50
grayscale = True
export_path = "export_negatives"
face_cascade = cv2.CascadeClassifier(xml_file)

subfolder_paths = []

for folder in os.listdir(data_path):
    try:
        subfolder_paths.append(f"{data_path}/{folder}/")
    except Exception as e:
        print(f"Could not load folder: {folder}")
        continue

for subfolder in subfolder_paths:
    try:
        for path in os.listdir(subfolder):
            path_parsed = f"{subfolder}/{path}"
            try:
                img = cv2.imread(path_parsed)
                # img = img[0:region, 0:region]
                img_1 = img[0:region, 0:region]
                img_2 = img[-region:, 0:region]
                img_3 = img[-region:, -region:]
                img_4 = img[0:region, :-region]
                images = [img_1, img_2, img_3, img_4]
                counter = 0
                for img in images:
                    counter += 1
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    faces = face_cascade.detectMultiScale(gray, 1.1, 4)

                    resized = cv2.resize(img, dim, interpolation=cv2.INTER_AREA)
                    faces_fr = face_recognition.face_locations(resized)

                    if len(faces) == 0 and len(faces_fr) == 0:
                        if grayscale:
                            resized = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
                            if not os.path.exists(
                                    f"./{export_path}/{width}_{height}_gs/{subfolder[30:]}/"
                            ):
                                os.makedirs(
                                    f"./{export_path}/{width}_{height}_gs/{subfolder[30:]}/"
                                )
                            cv2.imwrite(
                                f"./{export_path}/{width}_{height}_gs/{subfolder[30:]}/{counter}{path}",
                                resized,
                            )
                        elif not grayscale:
                            if not os.path.exists(
                                    f"./{export_path}/{width}_{height}/{subfolder[30:]}/"
                            ):
                                os.makedirs(
                                    f"./{export_path}/{width}_{height}/{subfolder[30:]}/"
                                )
                            cv2.imwrite(
                                f"./{export_path}/{width}_{height}/{subfolder[30:]}/{counter}{path}",
                                resized,
                            )

                    print(f"Processed: {subfolder[31:]}/{path}")

            except Exception as e:
                print(f"Could not load {path_parsed} - {e}")
                continue
    except Exception as e:
        print(f"Could not load a file at {subfolder} - {e}")
        continue