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
    #print(request) #<Request 'http://localhost:3030/insertLookInfo?uid=1' [GET]>
    #print("\n",request.form,"\n") #무조건 body에 담긴것만 가지고 오나보지,,?
    #print(request.args,"\n") # get으로 받았을 때 ImmutableMultiDict([('uid', '1'), ('dd', '2')])

    '''
    sql = "select * from closetdb.history where uid=%s"
    cursor.execute(sql, uid)
    result = cursor.fetchall()

    df = pd.DataFrame(result)  # result(uid의 history)를 데이터프레임으로 만듦.
    df['look_name'] = df.look_name.str.split(',')  # lookname의 값들을 콤마로 구분하여 나눠줌.
    df_with_lookname = df.copy(deep=True)  # df랑 같음 현재는..
    print("================\n",df,"=============\n")
    print("================\n", df['look_name'] , "=============\n")
    '''

    sql1 = "select look_name from closetdb.history where uid=%s"
    cursor.execute(sql1, uid)
    result = cursor.fetchall()
    #print("================\n")
    look_name_lists = []

    for ind in range(len(result)):
        #print(result[ind].get("look_name"))
        look_name_lists.append((result[ind].get("look_name")).split(','))

    #print(look_name_lists,"\n")

    '''
    x = []
    for index, row in df.iterrows():
        # print("indxe",index)
        # print("row",row)
        x.append(index)  # list x에 열번호를 추가?,,한다는거겠지,,

        for lookname in row['look_name']:  # 각 행의 lookname 개별적으로 돌면서
            df_with_lookname.at[index, lookname] = 1  # 거기에 있는 lookname의 값은 1로 해준다고..

    df_with_lookname = df_with_lookname.fillna(0)  # NaN인 거 0으로.
    print(df_with_lookname, "\n\n")
    
    office1 = 0
    casual = 0
    romantic = 0
    campus = 0
    daily = 0
    lovely = 0

    for i in range(len(df_with_lookname)):
        if (df_with_lookname.at[i, "office"] == 1):
            office1 += 1
        if (df_with_lookname.at[i, "casual"] == 1):
            casual += 1
        if (df_with_lookname.at[i, "romantic"] == 1):
            romantic += 1
        if (df_with_lookname.at[i, "campus"] == 1):
            campus+= 1
        if (df_with_lookname.at[i, "daily"] == 1):
            daily += 1
        if (df_with_lookname.at[i, "lovely"] == 1):
            lovely += 1
  
    check_uid = "select * from closetdb.lookTable where uid = %s"
    cursor.execute(check_uid, uid)
    checkUidResult = cursor.fetchall()
    #print(checkUidResult)

    if (len(checkUidResult) != 0):  # lookTable에 해당 uid가 있으면 update해줌.
        # update

        # updateLookRow = "UPDATE closetdb.lookTable SET cool = cool+1 WHERE closetdb.history look_name = cool "
        updateLookRow = "UPDATE closetdb.lookTable SET cool=%s,romantic=%s,casual=%s,office=%s,lovely=%s,daily=%s WHERE lookTable.uid = %s "
        cursor.execute(updateLookRow, (cool, romantic, casual, office1, lovely, daily, uid))
        result = cursor.fetchall()
        print("updateLookRow result", result)

    else:
        # insert
        insertLookRow = "INSERT INTO closetdb.lookTable (uid,cool,romantic,casual,office,lovely,daily) VALUES (%s,%s,%s,%s,%s,%s,%s)"
        cursor.execute(insertLookRow, (uid, cool, romantic, casual, office1, lovely, daily))
        result = cursor.fetchall()  # fetch는 안되는 이유 논문써오기 ! !
        print(result)
    '''
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

    # looTable에서 history table보고 user마다 look개수 구해서 저장하는데
    # if(history table의 uid == lookTable의 uid) then lovely +=1, casual+!...
    # 방금 코디가 등록된 uid를 안드에서 보내면서 request를 보낸거지 db update해달라고!

    #return 어떻게 할건지?

# data set을 바탕으로 유클리드 거리 계산 식을 이용하여 분류할 대상과 분류범주와의 거리구함
# 그 후 가까운 거리에 있는 순으로 오름차순 정렬한 후 어떤 카테고리에 가까운지 분류

@app.route('/recommendByUserInfo',methods=['GET'])
def RecAgeSex(): # 나랑 같은 나이와 성별을 가진 uid들을 구해서 그 uid들의 코디를 보여줌
    uid = request.args['uid']
    get_user_agesex = "SELECT age,sex FROM closetdb.user where uid =%s"
    cursor.execute(get_user_agesex,uid)
    result_get_user_age = cursor.fetchall() # 현재 사용자 age, sex


    if(result_get_user_age[0].get("age")//10==1): # 10대
        if(result_get_user_age[0].get("sex")==0): # 10대 여자
            get_others_uid = "select uid from closetdb.user where age>=10 and age <=19 and sex =0 and uid !=%s"
            cursor.execute(get_others_uid,uid)
            result_get_others_uid=cursor.fetchall()
        else: # 10대 남자
            get_others_uid = "select uid from closetdb.user where age>=10 and age <=19 and sex =1 and uid !=%s"
            cursor.execute(get_others_uid,uid)
            result_get_others_uid = cursor.fetchall()
    if (result_get_user_age[0].get("age") // 10 == 2):  # 20대
        if (result_get_user_age[0].get("sex") == 0):  # 20대 여자
            get_others_uid = "select uid from closetdb.user where age>=20 and age <=29 and sex =0 and uid !=%s"
            cursor.execute(get_others_uid,uid)
            result_get_others_uid = cursor.fetchall()
        else:  # 10대 남자
            get_others_uid = "select uid from closetdb.user where age>=20 and age <=29 and sex =1 and uid !=%s"
            cursor.execute(get_others_uid,uid)
            result_get_others_uid = cursor.fetchall()
    if (result_get_user_age[0].get("age") // 10 == 3):  # 30대
        if (result_get_user_age[0].get("sex") == 0):  # 30대 여자
            get_others_uid = "select uid from closetdb.user where age>=30 and age <=39 and sex =0 and uid !=%s"
            cursor.execute(get_others_uid,uid)
            result_get_others_uid = cursor.fetchall()
        else:  # 10대 남자
            get_others_uid = "select uid from closetdb.user where age>=30 and age <=39 and sex =1 and uid !=%s"
            cursor.execute(get_others_uid,uid)
            result_get_others_uid = cursor.fetchall()

    list_get_others_uid =[]
    recommend_list = []

    if(list_get_others_uid != None ): #1211 수빈 추가 
        for i in result_get_others_uid:
            list_get_others_uid.append(i.get("uid"))
        #print(list_get_others_uid) #이게 해당 유저와 같은 나잇대, 성별들의 user id들임

        
        #######uid 별로 history table에서 코디가져오기(hid)###########
        for i in list_get_others_uid:
            showlook = "select * from closetdb.history where uid = %s"
            cursor.execute(showlook,i)
            result_showlook = cursor.fetchall()
            if(result_showlook != ()):
                recommend_list.append(result_showlook[0])

    '''
    [{'hid': 21, 'uid': 5, 'like': 6, 'outer_cid': 0, 'up_cid': 26, 'down_cid': 27, 'look_name': 'casual,lovely', 'photo_look': None}, {'hid': 53, 'uid': 14, 'like': 0, 'outer_cid': 19, 'up_cid': 25, 'down_cid': 27, 'look_name': 'casual', 'photo_look': None}]
    json.dumps(recommend_list) 해도 값은 똑같음.. 
    '''
    response = {}
    response['status'] = 200
    response['message']="successfully recommened"
    response['result']= recommend_list
    return response

def orderByLookGarbage():
    #####################받아온 uid들의 스타일들을 lookTable에서 가져와서 각look들의 평균값내서 오름차순 배열
    campus = 0
    romantic = 0
    casual = 0
    office = 0
    lovely = 0
    daily = 0
    list_get_others_uid = []
    for j in list_get_others_uid:
        get_campus = "select campus from closetdb.lookTable JOIN closetdb.user on lookTable.uid = user.uid where lookTable.uid =%s"
        cursor.execute(get_campus, j)
        result_get_campus = cursor.fetchall()
        if (result_get_campus == ()):
            campus = campus + 0
        else:
            campus = campus + result_get_campus[0].get("campus")

        get_romantic = "select romantic from closetdb.lookTable JOIN closetdb.user on lookTable.uid = user.uid where lookTable.uid =%s"
        cursor.execute(get_romantic, j)
        result_get_romantic = cursor.fetchall()
        if (result_get_romantic == ()):
            romantic = romantic + 0
        else:
            romantic += result_get_romantic[0].get("romantic")

        get_casual = "select casual from closetdb.lookTable JOIN closetdb.user on lookTable.uid = user.uid where lookTable.uid =%s"
        cursor.execute(get_casual, j)
        result_get_casual = cursor.fetchall()
        if (result_get_casual == ()):
            casual = casual + 0
        else:
            casual += result_get_casual[0].get("casual")

        get_office = "select office from closetdb.lookTable JOIN closetdb.user on lookTable.uid = user.uid where lookTable.uid =%s"
        cursor.execute(get_office, j)
        result_get_office = cursor.fetchall()
        if (result_get_office == ()):
            office = office + 0
        else:
            office += result_get_office[0].get("office")

        get_lovely = "select lovely from closetdb.lookTable JOIN closetdb.user on lookTable.uid = user.uid where lookTable.uid =%s"
        cursor.execute(get_lovely, j)
        result_get_lovely = cursor.fetchall()
        if (result_get_lovely == ()):
            lovely = lovely + 0
        else:
            lovely += result_get_lovely[0].get("lovely")

        get_daily = "select daily from closetdb.lookTable JOIN closetdb.user on lookTable.uid = user.uid where lookTable.uid =%s"
        cursor.execute(get_daily, j)
        result_get_daily = cursor.fetchall()
        if (result_get_daily == ()):
            daily = daily + 0
        else:
            daily += result_get_daily[0].get("daily")
    campus = campus // 6
    romantic = romantic // 6
    casual = casual // 6
    office = office // 6
    lovely = lovely // 6
    daily = daily // 6
    looklist_sort = [campus, romantic, casual, office, lovely, daily]

    list_get_max_look = []
    max_look_idx = 0
    max_looklist_sort = max(looklist_sort)
    for i in range(len(looklist_sort)):
        if (max_looklist_sort <= looklist_sort[i]):
            max_look_idx = i
    for j in list_get_others_uid:
        if (max_look_idx == 0):
            get_max_look = 'select * from closetdb.history join closetdb.lookTable on history.uid = lookTable.uid where history.uid = %s and look_name like %s'
            cursor.execute(get_max_look, (j, ("%campus%")))
            result_get_max_look = cursor.fetchall()
            print(result_get_max_look)
            list_get_max_look.append(result_get_max_look.get("hid"))
        if (max_look_idx == 1):
            get_max_look = 'select * from closetdb.history join closetdb.lookTable on history.uid = lookTable.uid where history.uid = %s and look_name like %s'
            cursor.execute(get_max_look, (j, ("%romantic%")))
            result_get_max_look = cursor.fetchall()
            print(result_get_max_look)
            list_get_max_look.append(result_get_max_look.get("hid"))
        if (max_look_idx == 2):
            get_max_look = 'select * from closetdb.history join closetdb.lookTable on history.uid = lookTable.uid where history.uid = %s and look_name like %s'
            cursor.execute(get_max_look, (j, ("%casual%")))
            result_get_max_look = cursor.fetchall()
            print(result_get_max_look)
            list_get_max_look.append(result_get_max_look.get("hid"))
        if (max_look_idx == 3):
            get_max_look = 'select * from closetdb.history join closetdb.lookTable on history.uid = lookTable.uid where history.uid = %s and look_name like %s'
            cursor.execute(get_max_look, (j, ("%office%")))
            result_get_max_look = cursor.fetchall()
            print(result_get_max_look)
            list_get_max_look.append(result_get_max_look.get("hid"))
        if (max_look_idx == 4):
            get_max_look = 'select * from closetdb.history join closetdb.lookTable on history.uid = lookTable.uid where history.uid = %s and look_name like %s'
            cursor.execute(get_max_look, (j, ("%lovely%")))
            result_get_max_look = cursor.fetchall()
            print(result_get_max_look)
            list_get_max_look.append(result_get_max_look.get("hid"))
        if (max_look_idx == 5):
            get_max_look = 'select * from closetdb.history join closetdb.lookTable on history.uid = lookTable.uid where history.uid = %s and look_name like %s'
            cursor.execute(get_max_look, (j, ("%daily%")))
            result_get_max_look = cursor.fetchall()
            print(result_get_max_look)
            list_get_max_look.append(result_get_max_look.get("hid"))
    '''
    list_cos_hid = []
    for i in orderly_uid:
        cos_get_hid = "select hid from closetdb.history where uid = %s"
        cursor.execute(cos_get_hid, i)
        result_cos_get_hid = cursor.fetchall()
        print(result_cos_get_hid)
        for j in result_cos_get_hid:
            list_cos_hid.append(j.get("hid"))
    print(list_cos_hid)
    '''
    print(result_get_max_look)

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
    # acl = s3.get_bucket_acl(Bucket=bucket)
    # s3.put_bucket_acl(Bucket=bucket, AccessControlPolicy=acl)
    # s3.put_object( ACL="public-read")
    s3.upload_file(Bucket=bucket, Filename=os.path.abspath(file_path), Key=filestr, ExtraArgs={'ACL': 'public-read'})
    # s3.upload_file(os.path.abspath(file_path),bucket,filename)
    # location = boto3.client('s3').get_bucket_location(Bucket=bucket)['LocationConstraint']
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

    #print("routing response",response)
    os.remove(filestr)

    if(response != None): #insert성공
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
    #saveClothingNetworking(request,url)
    response = None
    #print(connection.insert_id())
    if(connection.insert_id() !=  None):
        response = {"status":201,"message":"successfully saved your clothing",
                    "colorR":rgb[0],"colorG":rgb[1],"colorB":rgb[2],
                    "color":colorStr,"label":labelStr,
                    "url":url}
    return response

if __name__ == "__main__":
    app.run(host='0.0.0.0',port=3030,debug=False,threaded=False)
