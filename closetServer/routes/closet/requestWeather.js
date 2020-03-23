//let Parser = require('rss-parser');
//let parser = new Parser();
var url = require('url');
var http = require('http');
var convert = require('xml-js');
var request = require('request');


//var parsedObject = url.parse('http://www.kma.go.kr/weather/forecast/mid-term-rss3.jsp?stnId=109');
//console.log(parsedObject);

//var requestUrl = 'http://www.kma.go.kr/wid/queryDFSRSS.jsp?zone=1159068000'
var requestUrl ='http://www.weather.go.kr/weather/forecast/mid-term-rss3.jsp?stnId=109';

request.get(requestUrl, (err, res, body) => {
	//res = 응답 데이터 body =응답 결과 
    if (err) {
        console.log(err);
    } else {
        if (res.statusCode == 200) {
            //var result = body;
           // console.log(body);//wow body에 다 찍힘 

            var xmlTojs = convert.xml2js(body, {compact: true , spaces:4});
            //console.log(xmlTojs.rss.channel.item.description.body.location);
            
            console.log(xmlTojs.rss.channel.item.description.body.location[0].data,'\n');
            console.log('날짜,시간: ', xmlTojs.rss.channel.item.description.body.location[0].data[0].tmEf._text);
            console.log('text: ', xmlTojs.rss.channel.item.description.body.location[0].data[0].wf);
            //console.log(typeof(xmlTojs)); //xml2json으로 하면 type이 string  

        }
    }
})


/*var feed = parser.parseURL('http://www.kma.go.kr/weather/forecast/mid-term-rss3.jsp?stnId=109');
console.log(feed);//Promise { <pending> }
console.log(feed.title);//undefined 

feed.items.forEach(item => {
		console.log(item.title+':'+item.link);
	});
*/
/*
(async () => {
	console.log('sdasd');
	let feed = await parser.parseURL('http://www.kma.go.kr/weather/forecast/mid-term-rss3.jsp?stnId=109');
	console.log(feed);
	console.log('\n\n');
	console.log(feed.title);

	feed.items.forEach(item => {
		console.log(item.title+':'+item.link);
	});
});
*/

/*
function parsing(){
	let feed = parser.parseURL('http://www.kma.go.kr/weather/forecast/mid-term-rss3.jsp?stnId=109');
	console.log(feed);
	return feed;
}

async function getFeed () {
	let feed = await parsing();
	console.log(type(feed));
}
*/