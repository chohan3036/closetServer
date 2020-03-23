var express = require('express');
var router = express.Router();
const pool = require('../../config/dbPool.js'); //프로미스 객체 반환. 
const async = require('async');
const upload = require('../../config/multer.js')
//var pool2 = await pool; //여기다가 놔도 되나?

router.post('/storeClothing', upload.single('photo'), async (req, res, next) => {
    var photo = null;
    //console.log(req);
    console.log(req.file);
    //console.log(req.file.location);
    var pool2 = await pool;
    if (req.file != undefined) {
        photo = req.file.location;
        //console.log(photo)
    }

    var uid = req.body.uid;
    var colorName = req.body.name;
    var colorR = req.body.colorR;
    var colorG = req.body.colorG;
    var colorB = req.body.colorB;
   var category = req.body.category;
    var description = req.body.description;

    var connection;

    try {
         connection = await pool2.getConnection();
        /*let getCurrentClosetIdQuery= "select closet_id from closetdb.closet";
        let getCurrentClosetId = await connection.query(getCurrentClosetIdQuery) || null;

        if(getCurrentClosetId != null)
            console.log(getCurrentClosetId);
*/
        let storeClothingQuery = "INSERT INTO closetdb.closet (uid,color_name,category,color_r,color_g,color_b,description,photo) VALUES(?,?,?,?,?,?,?,?)";
        let storeClothing = await connection.query(storeClothingQuery, [uid, colorName, colorR, colorG, colorB, category, description, photo]) || null;

        if (storeClothing != null) {
            res.status(201).send({
                status: 201,
                msg: "Successfully stored",
                Cid: storeClothing.insertId
            });
        } else {
            res.status(400).send({
                status: 400,
                msg: "Bad Request"
            });
        }

    } catch (err) {
        console.log(err)
    } finally {
        pool2.releaseConnection(connection);
    }

})

router.delete('/deleteClothing', async (req, res, next) => {
    var uid = req.body.uid;
    var cid = req.body.cid;
    var pool2 = await pool;
    try {
        connection = await pool2.getConnection();
        let deleteClothQuery = "DELETE FROM closetdb.closet WHERE closet_id = ? ";
        let deleteCloth = await connection.query(deleteClothQuery, cid) || null;
        console.log(deleteCloth);

        if (deleteCloth != null) {
            res.status(201).send({
                statsu: 201,
                message: "Successfully deleted"
            })
        }

    } catch (err) {
        next(err);
    } finally {
        pool2.releaseConnection(connection);
    }
})
module.exports = router;
