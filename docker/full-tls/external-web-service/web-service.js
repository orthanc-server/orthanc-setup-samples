var fs = require('fs'); 
var https = require('https'); 
var options = { 
    key: fs.readFileSync('/usr/tls/external-web-service-key.pem'), 
    cert: fs.readFileSync('/usr/tls/external-web-service-crt.pem'), 
    ca: fs.readFileSync('/usr/tls/ca-crt.pem'), 
    requestCert: true, 
    rejectUnauthorized: true
}; 
var server = https.createServer(options, function (req, res) { 
    console.log(new Date()+' '+ 
        req.connection.remoteAddress+' '+ 
        req.socket.getPeerCertificate().subject.CN+' '+ 
        req.method+' '+req.url); 
    res.writeHead(200); 
    res.end("hello world from external-web-service\n"); 
    console.log("sent response");
});

console.log('The web-service demo has started');
server.listen(8000);