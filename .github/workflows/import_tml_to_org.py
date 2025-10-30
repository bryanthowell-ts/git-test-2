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

object_type = os.environ.get('OBJECT_TYPE')
object_filename = os.environ.get('OBJECT_FILENAME')
import_policy = os.environ.get('IMPORT_POLICY')

# Define the directory names to link to the workflow 
# If you don't use 's', fix em up here
directories_for_objects = {
    "CONNECTION": ["connections"],
    "DATA_MODEL": ["tables", "models", "sql_views", "views"],
    "TABLE": ["tables"],
    "MODEL": ["models"],
    "LIVEBOARD": ["liveboards"],
    "ANSWER" : ["answers"],
    "CONTENT": ["liveboards", "answers"]
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

# Read the directories for the objects specified
# We will build an upload with ALL of them, and let ThoughtSpot use the 'etags'

# If filename listed, upload just that file
#
# FINISH 
#
#if object_filename != gh_action_none:
    # Assume everything is named {obj_id}.{obj_type}.tml
#    try: 
#        with open(file=object_filename, mode='r') as f:
#            tml_str= f.read()
#    except:
#        pass
# Get all files in a directory 
# else:

print("Getting directories for {}".format(object_type))
directories_to_import = directories_for_objects[object_type]
tml_strings = []
for dir in directories_to_import:
    try:
        files_in_dir = os.listdir(dir)
        print("These files in directory {}:".format(dir))
        print(files_in_dir)
        for filename in files_in_dir:
            # Skip files that aren't .tml
            if filename.find(".tml") != -1:
                full_file_path = "{}/{}".format(dir, filename)
                
                try: 
                    with open(file=full_file_path, mode='r') as f:
                        tml_str= f.read()
                        tml_strings.append(tml_str)
                except:
                    pass
    except FileNotFoundError as e:
        print("Directory doesn't exist, skipping")
        print(e)
    
# Publish the TMLs
# Switch to Async
try:
    if len(tml_strings) == 0:
        print("No TML to import, exiting")
        exit()
    else:
        print("Importing {} TMLs".format(len(tml_strings)))
        results = ts.metadata_tml_import(metadata_tmls=tml_strings, import_policy=import_policy, create_new=False)
        print("Imported with following response:")
        print(json.dumps(results, indent=2))
except requests.exceptions.HTTPError as e:
    print(e)
    print(e.response.content)
    exit()
