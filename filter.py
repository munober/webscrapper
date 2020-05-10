import os, errno
from faces import check_folder, preprocess_image, second_filter

target_path_imdb = "./dataset/images_imdb"
target_path_google = "./dataset/images_google"
target_path_dataset = "./dataset"
target_path_export = "./export_preprocessing/cropped"
imdb_list = "dataset/imdbactors.txt"


def run_filter():
    print(
        "Entering filter mode: will delete all non-face images and add a cropped folder for each actor"
    )
    try:
        os.makedirs(target_path_dataset)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
        pass

    if os.listdir(target_path_dataset):
        check_folder(target_path_dataset)
        second_filter(target_path_export)
    else:
        print("ERROR: You first need to fill up the dataset folder")


def run_preprocesses(width, height, grayscale):
    if width != 0 and height != 0:
        str = " "
        if grayscale:
            str = "and convert to grayscale"
        print(f"Entering pre-processing mode: will change image size {str}")

        try:
            os.makedirs(target_path_dataset)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
            pass

        if not os.listdir(target_path_dataset):
            print("[ERROR]: Need images to process in the the dataset folder")
            return

        try:
            preprocess_image(
                folder=target_path_export,
                width=width,
                height=height,
                grayscale=grayscale,
            )
        except Exception as e:
            print("Failed to preprocess images: {}".format(e))
    else:
        print("You have to set the width and height arguments first")
