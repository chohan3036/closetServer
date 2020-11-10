    # 이미지에 포함된 색상을 K=5 클러스터링 하는 코드
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import cv2
from sklearn.cluster import KMeans
import webcolors

def color(filestr):
    # 이미지 불러와서 RGB로 색상 변환 및 FLATTEN
    img = cv2.imread(filestr)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = img.reshape((img.shape[1] * img.shape[0], 3))

    # K를 5로 설정하고 이미지에 fit
    kmeans = KMeans(n_clusters=5)
    s = kmeans.fit(img)

    # 비율 계산을 위해 모든 픽셀의 라벨을 사용
    labels = kmeans.labels_
    labels = list(labels)

    # 클러스터링 된 결과를 저장
    centroid = kmeans.cluster_centers_

    # 모든 라벨 중 현재 색상에 해당하는 라벨이 몇 개 인지 계산
    percent = []
    for i in range(len(centroid)):
      j = labels.count(i)
      j = j / (len(labels))
      percent.append(j)

    # 가장 비율이 높은 색상의 RGB 값을 반환
    r, g, b = map(int, centroid[percent.index(max(percent))])

    # 이후 webcolors 라이브러리 사용하여 RGB 값에 대한 색상이름을 문자열로 반환
    def closest_colour(requested_colour):
        min_colours = {}
        for key, name in webcolors.css3_hex_to_names.items():
            r_c, g_c, b_c = webcolors.hex_to_rgb(key)
            rd = (r_c - requested_colour[0]) ** 2
            gd = (g_c - requested_colour[1]) ** 2
            bd = (b_c - requested_colour[2]) ** 2
            min_colours[(rd + gd + bd)] = name
        return min_colours[min(min_colours.keys())]

    def get_colour_name(requested_colour):
        try:
            closest_name = actual_name = webcolors.rgb_to_name(requested_colour)
        except ValueError:
            closest_name = closest_colour(requested_colour)
            actual_name = None
        return actual_name, closest_name

    requested_colour = (r, g, b)
    actual_name, closest_name = get_colour_name(requested_colour)

    return closest_name
