var express = require('express');
var router = express.Router();
const pool = require('../../config/dbPool.js'); //프로미스 객체 반환. 
const async = require('async');

router.post('/signin', async (req, res, next) => {
    //로그인은 get방식으로 하면 아이디,비번 다 공개되니까 post로 
    var id = req.body.id;
    var pwd = req.body.pwd;
    var pool2 = await pool;
    var connection;

    try {
        connection = await pool2.getConnection();
        let loginCheck = 'SELECT * FROM closetdb.user WHERE id = ?';
        var loginCheckResult = await connection.query(loginCheck, id) || null;
        /*
loginCheckResult :
 [ RowDataPacket {
    uid: 7,
    nickname: 'soi',
    age: 24,
    sex: 0,
    pwd: '111',
    id: 'sss11zzs' } ]
    */

        if (loginCheckResult.length === 1) { //아이디 있을 때.
            uid = loginCheckResult[0].uid
            let pwdCheckQuery = 'SELECT pwd FROM closetdb.user WHERE uid= ?'
            let pwdCheck = await connection.query(pwdCheckQuery, uid);
            if (pwdCheck[0].pwd == pwd) {
                res.status(201).send({
                    status: 201,
                    message: "Login success",
                    Uid: uid
                })
            } else {
                res.status(400).send({
                    status: 400,
                    message: "Login Failed (Pwd Error)"
                })
            }
        } else {
            res.status(400).send({
                status: 400,
                message: " Login Failed (Id Error)"
            })
        }

    } catch (err) {
        next(err);
        console.log(err);
    } finally {
        pool2.releaseConnection(connection);

    }


});


router.post('/signup', async (req, res, next) => {
    //console.log(req)
    var id = req.body.id;
    var pwd = req.body.pwd;
    var nickname = req.body.nickname;
    var sex = req.body.sex;
    var age = req.body.age;
    var pool2 = await pool;
    var connection;
    try {

        //uid AI . 
        connection = await pool2.getConnection();
        let checkIdQuery = 'select * from closetdb.user where id = ?';
        //select uid로 하면?
        let checkID = await connection.query(checkIdQuery, id);
        let signUpQuery = 'insert into closetdb.user (uid,nickname,age,sex,pwd,id) values(?,?,?,?,?,?)'; //이거 배열로 넣어야 하나?
        //console.log(checkID)
        /*
    중복아이디 있을 때. 
[ RowDataPacket {
    uid: 0,
    nickname: 'soi',
    age: 24,
    sex: 0,
    pwd: '111',
    id: 'sss11' } ]

    결과 없으면 0
        */
        if (checkID.length === 1) {
            res.status(303).send({
                status: 303,
                message: "이미 존재하는 ID입니다."
            });
        } else {
            let countQuery = "SELECT count(uid) as uid FROM closetdb.user";
            var count = await connection.query(countQuery);
            //[ RowDataPacket { 'count(uid)': 6 } ]
            //console.log(count[0].uid);
            count = count[0].uid

            let signUp = await connection.query(signUpQuery, [count, nickname, age, sex, pwd, id]);
        
            if (signUp.affectedRows == 1) {
                res.status(201).send({
                    status: 201,
                    message: "회원가입 성공",
                    ID: id,
                    Nickname: nickname,
                    Uid: count
                });
            }
        }

    } catch (err) {
        next(err)
    } finally {
        pool2.releaseConnection(connection);
    }
});
module.exports = router;