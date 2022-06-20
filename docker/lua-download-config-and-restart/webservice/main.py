from os import system
from typing import Union
import datetime

from fastapi import FastAPI

app = FastAPI()


@app.get("/configs/{system_id}")
def read_item(system_id: int, current_config_version: Union[int, None] = None):
    now_version = datetime.datetime.now().minute  # version of the file changes every minute
    
    print(f"{current_config_version} - {now_version}")
    if current_config_version == now_version:
        print("client already has the right config version")
        return {}
    
    print("new config version available")

    config = {
        "ConfigVersion": now_version,
        "Name": f"ORTHANC {system_id} v{now_version}"
    }
    
    return config