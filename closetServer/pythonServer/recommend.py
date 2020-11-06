import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from flask import Flask , request
import requests
import json
from pose import pose
import werkzeug
import boto3 #s3
import cv2
import time
import os
from dbPool import getConnection #.dbPool 로 해야 할 수도
from s3_config import ACCESS_KEY,SECRET_KEY
import grabcut
import getRGB
import color
import classify
import transparent

connection = getConnection()
app = Flask(__name__)


# history에 코디 하나씩 추가될때마다 uid랑 lookname을 받아서 추천알고리즘 업데이트
cursor = connection.cursor()
@app.route('/weather',methods= ['GET']) #parameter어떻게 전송하지,,?
def weather():
    lat = request.args.get("lat")
    lng = request.args.get('lng')
    #print(lat,lng)
    params = {"version": 1, "lat": lat , "lon":lng}
    headers = {"appKey": "1a0deeb4-c656-4f74-b760-c0097c46809b"}
    r = requests.get("https://apis.openapi.sk.com/weather/current/hourly", params=params, headers=headers)
    #print(r)
    #print('=================')
    #print(r.json())

    # json -> python 객체로 변환
    data = json.loads(r.text)
    weather = data["weather"]["hourly"]

    return str(weather[0])


@app.route('/recommendByLookTable', methods=['GET'])
def cos_sim():
    # 안에 들어갈거 고르고 계산하고
    # 본인 style vs. 나머지 user들의 style을 cos_sim으로 해서
    # 배열이나, 리스트, 튜플같은거에 담아서 sorted() 해서 차례대로 안드로 response해주기.
    uid = request.args['uid']
    cos_dir = {}
    other_uids_Query = "select uid from closetdb.lookTable"
    cursor.execute(other_uids_Query)
    countUidResult = cursor.fetchall()

    other_uids = []

    for i in countUidResult:
        other_uids.append(i.get("uid"))
    get_lookTable_uid = "select campus, romantic, casual, office, lovely, daily from closetdb.lookTable where uid = %s"
    get_lookTable_uid_result = cursor.execute(get_lookTable_uid, uid)
    lookTableResult = cursor.fetchall()
    user_lookTable_list = []
    for i in lookTableResult[0]:
        user_lookTable_list.append(lookTableResult[0].get(i))
    user_lookTable_list = np.array(user_lookTable_list)

    for i in other_uids:
        if (i != uid):
            get_lookTable_others = "select campus, romantic, casual, office, lovely, daily from closetdb.lookTable where uid = %s"
            lookTable_others = cursor.execute(get_lookTable_others, i)
            lookTable_others_result = cursor.fetchall()

            other_lookTable_list = []

            for j in lookTableResult[0]:
                other_lookTable_list.append(lookTable_others_result[0].get(j))

            other_lookTable_list = np.array(other_lookTable_list)
            c1 = user_lookTable_list.reshape(1, 6)
            c2 = other_lookTable_list.reshape(1, 6)
            coss = cosine_similarity(c1, c2)

            # arr.append(coss[0][0])
            cos_dir[i] = coss[0][0]
    # arr.sort()

    uid_list = (sorted(cos_dir.items(), key=lambda t: t[1], reverse=True))
    orderly_uid = []

    for i in uid_list:
        orderly_uid.append(i[0])
    # 이용해서 response로 이에 해당하는 코디들의 정보들을 보내줘야함. 근데 이거는 js에서 해줘도되구,, 여기서 해줘도되고, ,ㅇ ㅕ기서 사진 처리가 가능할 지 모르겠음..
    # => cos sim을 사용해서 유사도 측정 성공 ~!!!

    # db에서 룩개수,,상의 색,하의색평균..?max(RGB값-가장큰게 1,0,0)받아서 계산 || 나이 성별 좋아요(?)
    # outer 처리,,,-history에,,
    # 어떤사용자의 style을 구하는거. recommend를 위해서.. LookTable의 각 look들이 weight가 되고
    # 각 look안에 각 옷들이 있잖아,, 상의,,하의같은게 있고
    # reshape = 기존 데이터는 유지하고 차원과 형상을 바꾸는데 사용.

    cos_get_hid = "select hid from closetdb.history where uid = %s"
    cursor.execute(cos_get_hid, orderly_uid[0])
    result_cos_get_hid = cursor.fetchall()

    list_cos_hid = []
    result_dict={}
    for i in orderly_uid:
        cos_get_hid = "select * from closetdb.history where uid = %s"
        cursor.execute(cos_get_hid, i)
        result_cos_get_hid = cursor.fetchall()
        if (result_cos_get_hid != ()):
            for j in result_cos_get_hid:
                list_cos_hid.append(j)

    response = {}
    response['status'] = 200
    response['message'] = "successfully recommenedByLook"
    response['result'] = list_cos_hid
    return response


@app.route('/storeHistory',methods=['GET','POST']) #post로 보내야하넴...?
def storeHistory():
    #사진 처리 해야함..
    #print(request.form) #ImmutableMultiDict([('uid', '3'), ('like', '0'), ('ohter_cid', '23')])
    #print(request.form['uid']) #==print(request.form.get('uid')) #like는 어짜피 0으로 들어가게 하면 됨.
    imagefile = request.files['photo']
    filename = 'User_Look_'
    filestr = filename + time.strftime("%Y%m%d-%H%M%S") + '.png'
    imagefile.save(filestr)
    bucket = "closetsook"
    region = "ap-northeast-2"
    s3 = boto3.client('s3', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY, region_name=region)
    s3.upload_file(Bucket=bucket, Filename=os.path.abspath(filestr), Key=filestr, ExtraArgs={'ACL': 'public-read'})
    url = "https://%s.s3.%s.amazonaws.com/%s" % (bucket, region, filestr)
    os.remove(filestr)

    uid = request.form['uid']
    #outer_cid = request.form['outer_cid']
    #up_cid = request.form['up_cid']
    #down_cid = request.form['down_cid']
    look_name = request.form['look_name']

    #insertHistoryQuery = "INSERT INTO closetdb.history(uid,up_cid,down_cid,look_name) VALUES (%s,%s,%s,%s)"
    insertHistoryQuery = "INSERT INTO closetdb.history(uid,look_name,photo_look) VALUES (%s,%s,%s)"
    #photo_look 추가
    #cursor.execute(insertHistoryQuery, (uid, up_cid, down_cid, look_name))
    cursor.execute(insertHistoryQuery, (uid, look_name,url))

    hid = connection.insert_id()
    makeLookTable(uid)
    response = {}
    status = 400
    # result["OkPacket"] 찍어보기
    if(connection.insert_id() != None):
        response = {'status':201,"message":"successfully stored","hid":hid}
        status = 201
    return response,status


def makeLookTable(uid):
    sql1 = "select look_name from closetdb.history where uid=%s"
    cursor.execute(sql1, uid)
    result = cursor.fetchall()
    look_name_lists = []

    for ind in range(len(result)):
        #print(result[ind].get("look_name"))
        look_name_lists.append((result[ind].get("look_name")).split(','))
        
    look_calcul = {'office': 0, 'daily': 0, 'campus': 0, 'casual': 0, 'lovely': 0, 'romantic': 0}
    for lookname in look_name_lists:
        for each_name in lookname:
            look_calcul[each_name] += 1

    check_uid = "select * from closetdb.lookTable where uid = %s"
    cursor.execute(check_uid, uid)
    checkUidResult = cursor.fetchall()
    #print(checkUidResult)

    if (len(checkUidResult) != 0):  # lookTable에 해당 uid가 있으면 update해줌.
        # update
        # updateLookRow = "UPDATE closetdb.lookTable SET campus = campus+1 WHERE closetdb.history look_name = campus "
        updateLookRow = "UPDATE closetdb.lookTable SET campus=%s,romantic=%s,casual=%s,office=%s,lovely=%s,daily=%s WHERE lookTable.uid = %s "
        cursor.execute(updateLookRow,(look_calcul.get("campus"),look_calcul.get("romantic"), look_calcul.get("casual"), look_calcul.get("office"),look_calcul.get("lovely"), look_calcul.get("daily"), uid))

    else:
        # insert
        insertLookRow = "INSERT INTO closetdb.lookTable (uid,campus,romantic,casual,office,lovely,daily) VALUES (%s,%s,%s,%s,%s,%s,%s)"
        cursor.execute(insertLookRow, (uid,look_calcul.get("campus"),look_calcul.get("romantic"), look_calcul.get("casual"), look_calcul.get("office"),look_calcul.get("lovely"), look_calcul.get("daily")))
    
    result = cursor.fetchall() 
    #print(result)

    
    
###############################  
### 아래부터 Flask 네트워크 ###
###############################

@app.route('/dbsaveClothes', methods = ['POST'])
def saveClothingNetworking():
    uid = request.form['uid']
    color_name =request.form['color']
    colorR = request.form['colorR']
    colorG = request.form['colorG']
    colorB = request.form['colorB']
    category = request.form['category']
    description = request.form['description']
    url = request.form['url']
    storeClothingQuery = "INSERT INTO closetdb.closet (uid,color_name,category,color_r,color_g,color_b,description,photo) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)";
    storeClothing = cursor.execute(storeClothingQuery,(uid,color_name,category,colorR,colorG,colorB,description,url))

    return "DB에 옷 정보가 정상적으로 저장되었습니다."


def savePhoto(filestr):
    result = grabcut.grabCut(filestr)
    result = transparent.transparent(result)
    
    file_path = 'grabcuted-' + filestr
    cv2.imwrite(file_path, result)
    
    bucket = "closetsook"
    region = "ap-northeast-2"
    s3 = boto3.client('s3', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY, region_name=region)
    s3.upload_file(Bucket=bucket, Filename=os.path.abspath(file_path), Key=filestr, ExtraArgs={'ACL': 'public-read'})
    url = "https://%s.s3.%s.amazonaws.com/%s" % (bucket, region, filestr)
    
    os.remove(file_path)
    return url


@app.route('/saveAvatar',methods=['POST'])
def save_avatar():
    print(request.files['photo'])
    print(request.form['uid'])
    imagefile = request.files['photo']
    filename = 'User_Avatar_'
    filestr = filename + time.strftime("%Y%m%d-%H%M%S") + '.png'
    imagefile.save(filestr)

    url = savePhoto(filestr)
    response = pose(request.form['uid'],filestr,url)

    os.remove(filestr)
    
    # insert 성공
    if(response != None): 
        return ({"message":"good","status":201,"result":str(response)},201)
    else:
        return {"message":"faiiled"}

    
@app.route('/saveClothes', methods = ['GET', 'POST'])
def save_clohtes():
    imagefile = request.files['photo']
    filename = 'User_Clothes_'
    filestr = filename + time.strftime("%Y%m%d-%H%M%S") + '.png'
    imagefile.save(filestr)

    url = savePhoto(filestr)
    rgb = getRGB.rgb(filestr)
    colorStr = color.color(filestr)
    print(colorStr)
    labelStr = classify.label(filestr)
    print(labelStr)
    
    os.remove(filestr)
    
    response = None
    if(connection.insert_id() !=  None):
        response = {"status":201,"message":"successfully saved your clothing",
                    "colorR":rgb[0],"colorG":rgb[1],"colorB":rgb[2],
                    "color":colorStr,"label":labelStr,
                    "url":url}
    return response


if __name__ == "__main__":
    app.run(host='0.0.0.0',port=3030,debug=False,threaded=False)
