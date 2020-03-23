var express = require('express');
var router = express.Router();
const pool = require('../../config/dbPool.js'); //프로미스 객체 반환. 
const async = require('async');

router.get('/getAvatar/:uid', async (req, res, next) => {
    var pool2 = await pool;
    let uid = req.params.uid;
    connection = await pool2.getConnection();
    photo = null;

    let getAvatarQuery = 'SELECT avatar.photo, RShoulder,LShoulder,RWrist,LWrist,LKnee FROM closetdb.avatar where uid = ? ORDER BY avatar_id DESC limit 1;';
    let getAvatar = await connection.query(getAvatarQuery, uid);

    console.log(getAvatar);
    if(getAvatar[0].photo == undefined)
        res.starus(400).send({
            message :"No avatar Info"
        })  

    if(getAvatar[0].photo != null)
        photo = getAvatar[0].photo;

    res.status(200).send({
        message:"successfully show avatar image",
        photo : photo,
        Rshoulder :getAvatar[0].RShoulder,
        LShoulder : getAvatar[0].LShoulder,
        RWrist : getAvatar[0].RWrist,
        LWrist : getAvatar[0].LWrist,
        LKnee : getAvatar[0].LKnee
    });

    pool2.releaseConnection(connection);

})
router.get('/personalHistory/:uid', async (req, res, next) => {
    var pool2 = await pool;
    let uid = req.params.uid;

    connection = await pool2.getConnection();

    let getHistoryInfoQuery = 'SELECT * FROM closetdb.history WHERE uid = ?';
    let getHistoryInfo = await connection.query(getHistoryInfoQuery, uid);

    var resultArray = new Array();
    var result; //= {}; //or new Object()

    for (i = 0; i < getHistoryInfo.length; i++) {
        result = {};
        result.hid = getHistoryInfo[i].hid;
        result.like = getHistoryInfo[i].like;
        result.outer_cid = getHistoryInfo[i].outer_cid;
        result.up_cid = getHistoryInfo[i].up_cid;
        result.down_cid = getHistoryInfo[i].down_cid;
        result.look_name = getHistoryInfo[i].look_name;
        result.photo_look = getHistoryInfo[i].photo_look;
        resultArray.push(result);
    }

    pool2.releaseConnection(connection);

    if (result != undefined) {
        res.status(200).send({
            message: "successfully get history",
            result: resultArray
        });
    } else {
        res.status(400).send({
            message: "getting history is failed"
        })
    }


})
router.get('/personalCloset', async (req, res, next) => {
    //parameter방식
    //category별 return하는것도 구현하기!!!!! - 그냥 개인별 모든 옷은 category null로 넣어주기
    var pool2 = await pool;

    /*
    /personalCloset/:uid/:category'
    let uid = req.params.uid;
    let category = req.params.category;
    let color = req.query.color;
    undefined

    */
    let uid = req.query.uid;
    let getClothesInfoQuery;
    let getClothesInfo;
    let option;
    if (req.query.category == undefined) {
        option = req.query.color;
        getClothesInfoQuery = "SELECT * FROM closetdb.closet WHERE uid = ? AND color_name = ?";
    } else if (req.query.color == undefined) {
        option = req.query.category;
        getClothesInfoQuery = "SELECT * FROM closetdb.closet WHERE uid = ? AND category = ?";
    }

    try {
        connection = await pool2.getConnection()

        //안드에서 null 어떻게 들어오는지 확인하기.문자열로 들어오는것 같기도,,?
        //object? String? postman에서는 string으로
        if (option == undefined) {
            //해당 유저에게 있는 옷 다 return.
            getClothesInfoQuery = "SELECT * FROM closetdb.closet WHERE uid = ?";
            getClothesInfo = await connection.query(getClothesInfoQuery, uid);
        } else {
            getClothesInfo = await connection.query(getClothesInfoQuery, [uid, option]);
        }

        var resultArray = new Array();
        var result; //= {}; //or new Object()

        for (i = 0; i < getClothesInfo.length; i++) {
            result = {};
            result.cid = getClothesInfo[i].closet_id;
            result.color_name = getClothesInfo[i].color_name;
            result.color_r = getClothesInfo[i].color_r;
            result.color_g = getClothesInfo[i].color_g;
            result.color_b = getClothesInfo[i].color_b;
            result.category = getClothesInfo[i].category;
            result.description = getClothesInfo[i].description;
            result.photo = getClothesInfo[i].photo;
            resultArray.push(result);
        }

        //console.log(resultArray);
        if (resultArray != null) { //[]는 null이 아님. length로 확인해야 할듯. 
            res.status(200).send({
                status: 200,
                message: "personal closet 반환",
                result: resultArray
            }); //아무것도 없을 때는 []로 반환됨. isempty?
        } else {
            res.status(400).send({
                status: 400,
                message: "Request Failed"
            });
        }
    } catch (err) {
        console.log(err);

    } finally {
        pool2.releaseConnection(connection);
    }
});

module.exports = router;