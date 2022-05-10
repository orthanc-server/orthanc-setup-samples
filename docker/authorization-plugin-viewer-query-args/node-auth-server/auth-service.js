var http = require('http');


function grantAccess(response, authKey, authToken, resourceLevel, orthancId) {

  var granted = false;

  if (authKey == "Authorization" && authToken.startsWith("Bearer "))
  {
    authToken = authToken.substr("Bearer ".length);
  }

  if (authToken == 'good-token')  // allow access to everything
  {
  	granted = true;
  }
  else if (authToken == 'bad-token') // forbid access to everything
  {
  	granted = false;
  }
  else if (authToken == 'restricted-token') // grant access to patient 1 only
  {
  	if (resourceLevel == 'patient' && orthancId == '5c627243-c9c2acd8-6ad85563-2521e933-2394df24')
  	{
  		granted = true;
  	}	
  }

  console.log('granted: ', granted);
  
  var answer = {
    granted: granted,
    validity: 5 // the validity information returned is valid for 5 seconds (the Orthanc plugin will cache it for 5 seconds)
  }

  response.writeHead(200, { 'Content-Type' : 'application/json' });
  response.end(JSON.stringify(answer));
}


var server = http.createServer(function(request, response) {
  
  if (request.method == 'POST') { // any POST request received by this server is considered to be an auth-request coming from Orthanc
    var body = '';

    request.on('data', function (data) {
      body += data;
    });

    request.on('end', function () {
      console.log('Received authorization request: ' + body);
      console.log('HTTP headers: ' + JSON.stringify(request.headers));

      var authQuery = JSON.parse(body);

      grantAccess(response, authQuery["token-key"], authQuery["token-value"], authQuery["level"], authQuery["orthanc-id"]);
    });
    
  } else {
  
    response.writeHead(405);
    response.end();
  }
});


console.log('The auth-server demo has started');
server.listen(8000);