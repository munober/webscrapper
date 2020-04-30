import  os
import numpy as np
from matplotlib import pyplot
from PIL import Image

"""
Plots all images in a folder into one single image
"""
folder = "dataset/images_google"
def plot(folder, lines, columns):
    i = 1
    for file in os.listdir(folder):
        img = Image.open(f"{folder}/{file}")
        img = img.convert('RGB')
        pixels = np.asarray(img)
        # image = Image.fromarray(pixels)
        # face_array = np.asarray(image)
        pyplot.subplot(lines, columns, i)
        pyplot.axis('off')
        pyplot.imshow(pixels)
        i += 1
    pyplot.show()

plot(folder, 3, 10)