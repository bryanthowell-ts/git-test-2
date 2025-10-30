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

org_id = os.environ.get('ORG_ID')  # Set via retrieve_org_id_from_org_name.py setting environment

# Define the directory names to link to the workflow 
# If you don't use 's', fix em up here
directories_for_objects = {
    "CONNECTION": ["connections"],
    "DATA": ["tables", "models", "sql_views", "views"],
    "LIVEBOARD": ["liveboards"],
    "ANSWER" : ["answers"]
}

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
data_object_search_request = {
    "metadata": [
    {
      "type": "LOGICAL_TABLE"
    }
  ],
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

def retrieve_objects(request, record_size_override=-1): 
    request["record_size"] = record_size_override

    print("Requesting object listing")
    try:
        objs = ts.metadata_search(request=request)
    except requests.exceptions.HTTPError as e:
        print(e)
        print(e.response.content)
        exit()

    print("{} objects retrieved from API".format(len(objs)))
    return objs

# Perform metadata/search to get all the objects in the org
objs_in_org = {}

objs_in_org['LIVEBOARD'] = retrieve_objects(request=obj_type_select['LIVEBOARD'])
objs_in_org['ANSWER'] = retrieve_objects(request=obj_type_select['ANSWER'])
objs_in_org['CONNECTION'] = retrieve_objects(request=obj_type_select['CONNECTION'])
objs_in_org['DATA'] = retrieve_objects(request=obj_type_select['DATA'])
 
# Compile all obj_ids into easy list
all_obj_ids = []
for obj_type in objs_in_org:
    for o in objs_in_org[obj_type]:
        if o['metadata_obj_id'] is not None:
            all_obj_ids.append(o['metadata_obj_id'])

files_without_objects_in_org = []

for object_type in obj_type_select:
    print("Getting directories for {}".format(object_type))
    directories_to_import = directories_for_objects[object_type]

    for dir in directories_to_import:
        try:
            files_in_dir = os.listdir(dir)
            # print("These files in directory {}:".format(dir))
            # print(files_in_dir)
            for filename in files_in_dir:
                # Skip files that aren't .tml
                if filename.find(".tml") != -1:
                    full_file_path = "{}/{}".format(dir, filename)

                    # Break out obj_id from filename
                    fn_split = filename.split('.')[0]
                    # Remove the last two, which should be obj_type and tml
                    fn_slice = fn_split[0:-2]
                    file_obj_id = '.'.join(fn_slice)

                    # See if it exist in the 
                    if file_obj_id in all_obj_ids:
                        continue
                    else:
                        files_without_objects_in_org.append(full_file_path)

        except FileNotFoundError as e:
            print("Directory doesn't exist, skipping")
            print(e)

print("Files that no longer have matching object in ThoughtSpot Org:")
print(json.dumps(files_without_objects_in_org, indent=2))