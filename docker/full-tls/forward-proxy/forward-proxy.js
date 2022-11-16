var http = require('http');
var fs = require('fs'); 
var https = require('https'); 

var server = http.createServer(function(request, response) {
  
  if (request.method == 'POST') { // any POST request received by this server is forwarded to the external-web-service
    var incomingRequestBody = '';

    request.on('data', function (data) {
      incomingRequestBody += data;
    });

    request.on('end', function () {
      var remoteResponseBody = '';

      console.log('Received a request whose body is: ' + incomingRequestBody);
      console.log('HTTP headers: ' + JSON.stringify(request.headers));
      console.log('forwarding to external-web-service');

      var options = { 
          hostname: 'external-web-service', 
          port: 8000, 
          path: '/', 
          method: 'POST', 
          key: fs.readFileSync('/usr/tls/orthanc-b-client-key.pem'), 
          cert: fs.readFileSync('/usr/tls/orthanc-b-client-crt.pem'), 
          ca: fs.readFileSync('/usr/tls/ca-crt.pem') }; 

      var req = https.request(options, function(res) { 
          res.on('data', function(data) { 
            remoteResponseBody += data;
          }); 
          res.on('end', function() {
            // forward the response to orthanc
            response.writeHead(res.statusCode);
            response.end(remoteResponseBody);
          })
      }); 
      req.end(); 


      req.on('error', function(e) { 
          console.error(e); 
      });

    });
    
  } else {
  
    response.writeHead(405);
    response.end();
  }
});


console.log('The forward-proxy has started');
server.listen(8000);


