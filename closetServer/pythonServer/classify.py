from keras.preprocessing.image import img_to_array
from keras.models import load_model
import tensorflow as tf
import numpy as np
import imutils
import pickle
import cv2

def label(filestr):
    # 사진 불러오기
    image = cv2.imread(filestr)
    output = imutils.resize(image, width=400)

    # 이미지 전처리
    image = cv2.resize(image, (96, 96))
    image = image.astype("float") / 255.0
    image = img_to_array(image)
    image = np.expand_dims(image, axis=0)

    # 모델 불러오기
    print("[INFO] loading network...")
    model = load_model('/home/ubuntu/server/closetServer/pythonServer/fashion.h5')
    mlb = pickle.loads(open('/home/ubuntu/server/closetServer/pythonServer/mlb.pickle', "rb").read())

    # 분류하기
    print("[INFO] classifying image...")
    proba = model.predict(image)[0]
    idxs = np.argsort(proba)[::-1][:4]

   # 제일 유사한 CLASS 찾기
    for (i, j) in enumerate(idxs):
        label = "{}: {:.2f}%".format(mlb.classes_[j], proba[j] * 100)
        cv2.putText(output, label, (10, (i * 30) + 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    # 'N' CLASS 지워주고
    proba[proba.argmax()] = 0

    print(mlb.classes_[proba.argmax()])
    return mlb.classes_[proba.argmax()]
