var express = require('express');
var router = express.Router();

/* GET home page. */
router.get('/', function(req, res, next) {
  res.render('index', { title: 'Express' });
});


router.use('/user',require('./user/index.js'));
router.use('/closet',require("./closet/index.js"));
module.exports = router;
