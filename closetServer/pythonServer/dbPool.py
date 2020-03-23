import pymysql

def getConnection():
    connection = pymysql.connect(host='closet-db.c7ijj9jzxxlp.ap-northeast-2.rds.amazonaws.com', user='admin',
                             password='closetdb', db='closetdb', charset='utf8', autocommit=True,
                             cursorclass=pymysql.cursors.DictCursor)
    return connection
