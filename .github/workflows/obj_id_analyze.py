import os
import requests.exceptions
import csv
import json
import time
import re
from urllib import parse

from thoughtspot_rest_api import *

gh_action_none = "{None}"
#
# Values passed into ENV from Workflow file, using GitHub Secrets and Workflow Variables
#

# Secrets
server = os.environ.get('TS_SERVER') 
username = os.environ.get('TS_USERNAME')
secret_key = os.environ.get('TS_SECRET_KEY')

# Variables from the workflow

author_filter = os.environ.get('AUTHOR_FILTER')
tag_filter = os.environ.get('TAG_FILTER')
record_size = os.environ.get('RECORD_SIZE_LIMIT')
object_type = os.environ.get('OBJECT_TYPE')

org_id = os.environ.get('ORG_ID') # Set via retrieve_org_id_from_org_name.py setting environment


# full_access_token = os.environ.get('TS_TOKEN')  #  Tokens are tied to a particular Org, so useful in an environment with only a few Orgs but not single-tenant

ts: TSRestApiV2 = TSRestApiV2(server_url=server)

try:
    auth_resp = ts.auth_token_full(username=username, secret_key=secret_key,
                                    validity_time_in_sec=3000, org_id=org_id)
    ts.bearer_token = auth_resp['token']
except requests.exceptions.HTTPError as e:
    print(e)
    print(e.response.content)
    exit()


order_field = 'MODIFIED'

# Request for LIVEBOARDS
lb_search_request = {
    "metadata": [
    {
      "type": "LIVEBOARD"
    }
  ],
  "sort_options": {
    "field_name": order_field,
    "order": "DESC"
  },
    "record_size" : -1,
    "record_offset": 0
}

# Request for ANSWERS
answer_search_request = {
    "metadata": [
    {
      "type": "ANSWER"
    }
  ],
  "sort_options": {
    "field_name": order_field,
    "order": "DESC"
  },
    "record_size" : -1,
    "record_offset": 0
}

# Request for Data Objects (Tables, Models, etc.)
# Not differentiated in request, all are "LOGICAL_TABLE
# request metadata_details to allow more complex fully-qualified name variations in obj_id generation
data_object_search_request = {
    "metadata": [
    {
      "type": "LOGICAL_TABLE"
    }
  ],
  "include_details": True,
  "sort_options": {
    "field_name": order_field,
    "order": "DESC"
  },
    "record_size" : -1,
    "record_offset": 0
}

connection_search_request = {
    "metadata": [
    {
      "type": "CONNECTION"
    }
  ],
  "sort_options": {
    "field_name": order_field,
    "order": "DESC"
  },
    "record_size" : -1,
    "record_offset": 0
}

obj_type_select = {
    'LIVEBOARD' : lb_search_request,
    'ANSWER' : answer_search_request,
    'DATA' : data_object_search_request,
    'CONNECTION' : connection_search_request
}

# Update if new types appear or you don't use 's' at the end:
data_directories = ['tables', 'models', 'sql_views', 'views']

def retrieve_objects(request, record_size_override=-1): 
    # Add filters if passed from workflow
    if author_filter != gh_action_none:
        request["created_by_user_identifiers"] = [author_filter]
    
    if tag_filter != gh_action_none:
        request["tag_identifiers"] = [tag_filter]

    request["record_size"] = record_size_override

    print("Requesting object listing")
    try:
        objs = ts.metadata_search(request=request)
    except requests.exceptions.HTTPError as e:
        print(e)
        print(e.response.content)
        exit()

    print("{} objects retrieved from API".format(len(objs)))
    print("")
    return objs

# Main function to pull and download the variuos object types
def download_objects():
    all_objs = []
    # Only look at select object_type if not ALL
    if object_type != 'ALL':
        final_obj_type_select = { object_type : obj_type_select[object_type]}
    else:
        final_obj_type_select = obj_type_select
    # Loop does all types on ALL condition
    for type in final_obj_type_select:
        print("Retrieving all objects of type: {}".format(type))
        objs = retrieve_objects(request=obj_type_select[type], record_size_override=record_size)
        all_objs.append(objs)
        print("")
    
    return all_objs

# Create suggestions for null
def suggest_obj_id_for_null(objs):
    final_list = []
    for o in objs:
        obj_id = o['metadata_obj_id']
        guid = o['metadata_id']
        obj_name = o['metadata_name']

        # suggestion = "{}-{}".format(o['metadata_name'], guid[0:8])

        # Special rule for Tables, which don't have much of a name
        # But could be fully qualified or at least have Connection appended at the front

        # This is simple, without special rule for tables
        suggestion = obj_name.replace(" ", "_")   # Need more transformation
        suggestion = parse.quote(obj_name)
        # After parse quoting, there characters are in form %XX , replace with _ or blank space
        suggestion = re.sub(r"%..", "", suggestion)

        

        final_list.append([obj_name, guid, suggestion])
    return final_list

# Simply list the auto-created + GUID (except for Tables?)

def list_auto_created(objs):
    final_list = []
    for o in objs:
        obj_id = o['metadata_obj_id']
        guid = o['metadata_id']
        obj_name = o['metadata_name']
        final_list.append([obj_id, guid, obj_name])
    return final_list

def analyze_obj_ids(obj_resp):
    # Two types of "not ready": objects with null obj_id and those that were auto generated
    null_obj_ids = []
    auto_created_obj_ids = []
    obj_type = None
    for o in obj_resp:
        obj_id = o['metadata_obj_id']
        obj_type = o['metadata_type']


        # Determine if None, objects from before obj_id turned on in instance
        if obj_id is None:
            null_obj_ids.append(o)
        
        else: 
            # Determine if obj_id ends with the -{8 UUID chars from GUID} pattern
            re_pattern_auto_created_obj_id = r"-[0-9a-fA-F]{8}$"
            match = re.search(re_pattern_auto_created_obj_id, obj_id)

            if match:
                auto_created_obj_ids.append(o)
    
    print("Analyzed {} objects of type {}".format(len(obj_resp), obj_type))

    print("{} objects without obj_id".format(len(null_obj_ids)))
    if len(null_obj_ids) > 0:
        print("Objects without obj_id and suggested obj_id:")
        for o in suggest_obj_id_for_null(null_obj_ids):
            print(json.dumps(o))

    print("")

    print("{} objects with auto-created obj_ids".format(len(auto_created_obj_ids)))
    if len(auto_created_obj_ids) > 0:
        print("Objects with auto-created obj_ids:")
        for o in list_auto_created(auto_created_obj_ids):
            print(json.dumps(o))

    print("")



# Run the download routines based on the choices
all_objs_list = download_objects()
for objs in all_objs_list:
    analyze_obj_ids(objs)