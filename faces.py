import cv2


def check_folder():
    img = cv2.imread('dataset/images_imdb/Leonardo_Dicaprio/9f551d6bb1.jpg')
    check_image(img)

def check_image(img):
    face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    if len(faces) == 0:
        print(f'No faces found')
    for (x, y, w, h) in faces:
        cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
    cv2.imshow('img', img)
    cv2.waitKey()

check_folder()