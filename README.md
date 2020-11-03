# 옷장 관리 애플리케이션 'Handy Closet'


### 진행 기간 : 2019.09 ~ 2019.12
###   목  적  :
####  1) 옷장 관리를 체계적으로 하기 힘들었던 현대인들의 고충을 덜어주기
####  2) 머신러닝, 이미지 분석 등의 신기술 경험을 위해
### 기술 스택 : Java, Python, Javascript, MySQL, NodeJS, Flask, Tensorflow, Keras, AWS

### 폴더 구성
#### - 크게 루트에 위치한 Javascript 코드와 pythonServer 안의 Python 코드로 구성
#### - grabCut.py : grabCut 알고리즘을 input 이미지에 적용, 배경 제거한 결과를 반환
#### - transparent.py : 제거된 배경 채널을 alpha로 변경, 투명하게 만들어 반환
#### - classify.py : 학습해놓은 모델을 불러와 input 이미지의 종류를 반환
#### - color.py : input 이미지의 색을 반환
#### - getRGB.py : 해당 색에 가장 가까운 webColor 찾아서 문자열로 반환
#### - recommend.py : 애플리케이션과의 네트워크 구현, input 이미지를 dataStream 객체로 받아 위 작업을 수행

### 작업 순서
#### 1. input 이미지의 배경을 제거하고 투명화 한 뒤, AWS S3 버킷에 저장
#### 2. input 이미지의 옷 종류와 색을 판단, 문자열 형태로 이미지의 URL과 함께 
