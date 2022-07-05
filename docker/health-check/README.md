# Purpose

This is a sample setup to demonstrate how to monitor an Orthanc instance and restart it in case it is locked e.g in a 
Lua callback


# Description

This demo contains:

- an `autoheal` container that monitors other containers and restart them if they are unresponsive
- an Orthanc container with a health-check configured.  If the health-check fails, it will retry a few
  times and if all retries fails, the `autoheal` container will restart Orthanc. 

# Starting the setup

To start the setup, type: `docker-compose up`

# demo

- Connect to the orthanc UI to check it is alive on [http://localhost:8042](http://localhost:8042) (login/pwd: demo/demo).
- Trigger Lua code that will block orthanc for 2 minutes by sending this command: `curl http://demo:demo@localhost:8042/tools/execute-script -d "os.execute("sleep 120")"`
- Connect to the orthanc UI right after that, it shall be unresponsive.
- Given the health-check policy, after 2 retries at 3 seconds interval with a 2 seconds timeout (total = 10 seconds), Orthanc should 
  restart and the UI shall become responsive again.

