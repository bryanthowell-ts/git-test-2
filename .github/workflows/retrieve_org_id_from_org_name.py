import os
import requests.exceptions
import json
import time

from thoughtspot_rest_api import *

#
# Values passed into ENV from Workflow file, using GitHub Secrets and Workflow Variables
#
server = os.environ.get('TS_SERVER') 
username = os.environ.get('TS_USERNAME')
secret_key = os.environ.get('TS_SECRET_KEY')
org_name = os.environ.get('TS_ORG_NAME')

ts: TSRestApiV2 = TSRestApiV2(server_url=server)

# First get Org_Id: 0 to request orgs list
try:
    auth_token_response = ts.auth_token_full(username=username, secret_key=secret_key,
                                               validity_time_in_sec=3000, org_id=0)
    ts.bearer_token = auth_token_response['token']
except requests.exceptions.HTTPError as e:
    print(e)
    print(e.response.content)
    exit()

# Get token for the specified org_name
try:
    # print("Searching for org_id for {}".format(org_name))
    org_search_req = {
        "org_identifier": org_name
    }
    search_resp = ts.orgs_search(request=org_search_req)
except requests.exceptions.HTTPError as e:
    print(e)
    print(e.response.content)
    exit(1)

# If org_id is found, set environment variable to retrieve in the shell
if len(search_resp) == 1:
    org_id = search_resp[0]['id']
    print("ORG_ID={}".format(org_id))
    # os.environ['ORG_ID'] = "{}".format(org_id)
else:
    exit(1)