import os
import requests.exceptions
import json
import time

from thoughtspot_rest_api import *

gh_action_none = "{None}"
#
# Values passed into ENV from Workflow file, using GitHub Secrets and Workflow Variables
#
server = os.environ.get('TS_SERVER') 
username = os.environ.get('TS_USERNAME')
secret_key = os.environ.get('TS_SECRET_KEY')

org_id = os.environ.get('ORG_ID') 

old_obj_id= os.environ.get('OLD_OBJ_ID')
new_obj_id = os.environ.get('NEW_OBJ_ID')

ts: TSRestApiV2 = TSRestApiV2(server_url=server)

try:
    auth_resp = ts.auth_token_full(username=username, secret_key=secret_key,
                                    validity_time_in_sec=3000, org_id=org_id)
    ts.bearer_token = auth_resp['token']
except requests.exceptions.HTTPError as e:
    print(e)
    print(e.response.content)
    exit()

try:
    ts.metadata_update_obj_id(new_obj_id=new_obj_id, current_obj_id=old_obj_id)
except requests.exceptions.HTTPError as e:
    print(e)
    print(e.response.content)
    exit(1)