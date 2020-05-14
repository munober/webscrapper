# This script predicts who is in the picture

from numpy import expand_dims
from matplotlib import pyplot
from keras_vggface.vggface import VGGFace
from keras_vggface.utils import decode_predictions

pixels = pyplot.imread("export_preprocessing/224_224/seth_meyer/2cc497f6831.jpg")
pixels = pixels.astype("float32")
samples = expand_dims(pixels, axis=0)
model = VGGFace(model="resnet50")
yhat = model.predict(samples)
results = decode_predictions(yhat)
for result in results[0]:
    print("%s: %.3f%%" % (result[0], result[1] * 100))
