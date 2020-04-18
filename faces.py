from os.path import isdir
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import mtcnn
import os
from os.path import isdir
from numpy import savez_compressed

# Folder paths
folder = 'dataset/images/'
dataset_file = 'dataset/numpy_dataset.npz'

def extract_face(filename, required_size=(160, 160)):
	image = Image.open(filename)
	# Dataset already is RGB, only use if that's not the case
	# image = image.convert('RGB')
	results = mtcnn.MTCNN().detect_faces(np.asarray(image))
	x1, y1, width, height = results[0]['box']
	x1, y1 = abs(x1), abs(y1) # prevents these from being negative
	x2, y2 = x1 + width, y1 + height
	face = np.asarray(image)[y1:y2, x1:x2]
	image = Image.fromarray(face)
	image = image.resize(required_size)
	face_array = np.asarray(image)
	return face_array

def load_faces(directory): # Loads all faces in a directory
	faces = list()
	# enumerate files
	for filename in os.listdir(directory):
		path = directory + filename
		face = extract_face(path)
		faces.append(face)
	return faces

def load_dataset(directory): # Loads all different face folders in a bigger folder
	X, y = list(), list()
	for subdir in os.listdir(directory):
		path = directory + subdir + '/'
		if not isdir(path):
			continue
		faces = load_faces(path)
		labels = [subdir for _ in range(len(faces))]
		# summarize progress
		print('>loaded %d examples for class: %s' % (len(faces), subdir))
		for label in labels:
			print (label)
		X.extend(faces)
		y.extend(labels)
	return np.asarray(X), np.asarray(y) # return faces and labels in this order

faces, labels = load_dataset(folder)
print('Data set size: ', faces.shape, labels.shape)
# savez_compressed(dataset_file, faces, labels)
iterator = 1
for face in faces:
	img = Image.fromarray(face, 'RGB')
	plt.subplot(4, 15, iterator)
	plt.axis('off')
	plt.imshow(face)
	iterator += 1
	if not os.path.exists('dataset/cropped/'):
		os.makedirs('dataset/cropped/')
	img = img.save('dataset/cropped/' + '/' + str(labels[iterator]) + '_' + str(iterator) + '.jpg')
plt.show()