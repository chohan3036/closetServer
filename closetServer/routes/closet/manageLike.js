var express = require('express');
var router = express.Router();
const pool = require('../../config/dbPool.js'); //프로미스 객체 반환. 
const async = require('async');
const upload = require('../../config/multer.js')

//history보여주기 = python. 

//좋아요 누르기한거 반영, 취소  , 좋아요 수로 많은거 순서대로 return. 

router.get('/myLikeList/:uid',async(req,res,next)=>{
    uid = req.params.uid;

     var pool2 = await pool;
     connection = await pool2.getConnection();
     let getLikeQuery = "SELECT hid FROM closetdb.like_table where uid = ?;"
     let getLike = await connection.query(getLikeQuery,uid) || null;

     result = new Array();
     for (i =0 ; i<getLike.length; i++){
        result.push(getLike[i].hid);
     }
     if(getLike != null){
        res.status(200).send({
            message : "like list 반환 성공",
            result : result
        });
     }else {
     res.status(400).send({
        message : "like List 반환 불가"
     });
     }



})

router.post('/makeLike', async (req, res, next) => {
    uid = req.body.uid;
    hid = req.body.hid;

    var pool2 = await pool;
    try {
        connection = await pool2.getConnection();

        let checkMakeStatusQuery = 'SELECT COUNT(likeId) as id FROM closetdb.like_table WHERE uid = ? AND hid =?';
        let checKMakeStatus = await connection.query(checkMakeStatusQuery, [uid, hid]);
        //console.log(checKMakeStatus); //[ RowDataPacket { id: 1 } ] 없으면 0


        if (checKMakeStatus[0].id == 0) //처음 좋아요 누를 때
        {
            let makeLikeQuery = 'INSERT INTO closetdb.like_table (uid,hid) values (?,?)';
            let makeLike = await connection.query(makeLikeQuery, [uid, hid]) || null;

         let updateLikeInHistoryQuery = 'UPDATE closetdb.history as history SET history.like=history.like+1 WHERE hid =?';
             let updateLikeInHistory = await connection.query(updateLikeInHistoryQuery, hid);

            //console.log(makeLike); // uid- hid에 unique Key걸려 있음.
            // unique key걸려있어서 같은 조합으로 하면 안됨.. 하기전에 검사를 하던가 status 값을 넣어줘서 바꿔주는걸로 해야하릇..

            if (makeLike.affectedRows == 1) {
                res.status(200).send({
         status: 201,
         like_status :1,
                    message: "successfully made a like"
                });
            } else {
                res.status(400).send({
                    status: 400,
                    message: "failed to make a like"
                })
            }
        } else {
            let cancelLikeQuery= "DELETE FROM closetdb.like_table where uid = ? and hid =? ;"
            let cancelLike = await connection.query(cancelLikeQuery,[uid,hid]);
            res.status(201).send({
                status:201,
                like_status: 0,
                message :"cancel the like hid ="+hid+"   uid = "+uid
            });
        }

    } catch (err) {

    } finally {

        pool2.releaseConnection(connection);
    }

});

router.delete('/cancelLike', async (req, res, next) => {

});

router.get('/recommendByLike', async (req, res, next) => {
    //argument받을 필요 없음.
    var pool2 = await pool;
    try {
        connection = await pool2.getConnection();
        orderedByLikeQuery = 'SELECT hid,uid,history.like,look_name,photo_look FROM closetdb.history ORDER BY history.like DESC '; //내림차순 정렬
        orderedByLike = await connection.query(orderedByLikeQuery);

        var resultArray = new Array();
        var result; //= {}; //or new Object()

        for (i = 0; i < orderedByLike.length; i++) {
            result = {};
            result.hid = orderedByLike[i].hid;
            result.uid = orderedByLike[i].uid;
            result.like = orderedByLike[i].like;
            result.look_name = orderedByLike[i].look_name;
            result.photo_look = orderedByLike[i].photo_look;
            resultArray.push(result);
        }

        //console.log(resultArray);

        if (resultArray != undefined) { //흠 이거 어떻게 처리할까,,
            res.status(200).send({
                message: "successfully selected",
                result: resultArray
            });
        } else {
            res.status(400).send({
                message: "failed to select"
            });
        }
    } catch (err) {

    } finally {
        pool2.releaseConnection(connection);
    }
});

module.exports = router;