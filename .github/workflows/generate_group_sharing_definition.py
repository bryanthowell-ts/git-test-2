import os
import requests.exceptions
import csv
import json
import time

from thoughtspot_rest_api import *

gh_action_none = "{None}"
#
# Values passed into ENV from Workflow file, using GitHub Secrets and Workflow Variables
#

# Secrets
server = os.environ.get('TS_SERVER') 
username = os.environ.get('TS_USERNAME')
secret_key = os.environ.get('TS_SECRET_KEY')

org_id = os.environ.get('ORG_ID') # Set via retrieve_org_id_from_org_name.py setting environment

# Define how you like (repo level variable)
share_definition_filename = 'groups_sharing.json'

ts: TSRestApiV2 = TSRestApiV2(server_url=server)

try:
    auth_resp = ts.auth_token_full(username=username, secret_key=secret_key,
                                    validity_time_in_sec=3000, org_id=org_id)
    ts.bearer_token = auth_resp['token']
except requests.exceptions.HTTPError as e:
    print(e)
    print(e.response.content)
    exit()

# Retrieve all object types with the Tag or Author that specifies what is "part of the release"
# Needed for building GUID: obj_id map

# Retrieve Sharing Permissions to the set of Groups specified by Prefix / Postfix
# or
# Look at set of Tags that will "transform into groups"

# JSON format will look like:
# {'groupName' : [obj_ids]}