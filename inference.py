# This script predicts who is in the picture

import os
from numpy import expand_dims
from matplotlib import pyplot
from keras_vggface.vggface import VGGFace
from keras_vggface.utils import decode_predictions

target = "export_preprocessing/224_224"


def detect(path):
    pixels = pyplot.imread(path)
    pixels = pixels.astype("float32")
    samples = expand_dims(pixels, axis=0)
    model = VGGFace(model="resnet50")
    yhat = model.predict(samples)
    results = decode_predictions(yhat)
    for result in results[0]:
        print(result[0], ": ", result[1] * 100)


for person in os.listdir(target):
    for face in os.listdir(f"{target}/{person}"):
        print(f"Expecting {person}:")
        detect(f"{target}/{person}/{face}")