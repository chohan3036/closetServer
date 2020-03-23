var express = require('express');
var router = express.Router();

router.use('/',require('./manageClothing.js'));
router.use('/show',require('./show.js'));
router.use('/like',require('./manageLike.js'));

module.exports = router;
