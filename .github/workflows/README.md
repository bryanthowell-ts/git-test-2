# ThoughtSpot SDLC GitHub Actions

This directory contains example GitHub Workflow .yml files and Python scripts to implement Actions to assist in do SDLC with ThoughtSpot TML files.

Basic concepts these scripts support:

1. Export (Download) TML from an Org to a Branch
2. Import TML from a Branch to an Org
3. Release Branch: branch representing intentional subset of dev content to be deployed to other branches 
4. Deployment Branches: Receive Pull Requests / Merges from "Release Branch", where Import TML actions occur to their linked Org
5. Version Control Branches: Branches meant for All Content to be Downloaded, to provide version control of all content in a linked Org

Each Org that will import the content from "release" will have a '{orgName}_deploy' branch to contain the most recent TML from the "release" branch that has been imported into the linked Org.

Pull requests / merges are made from 'release' branch into the "{}_deploy" branches, then the Import TML is used.

Alternatively, you can use the Import TML Actions to Deploy from the "release" branch to any other Org - with the loss of the pull request / merge history provided by the "{}_deploy" branches.

In a Single Tenant Deployment (a "prod Org per Customer" or otherwise), the "Import TML - Single Tenant Deployment Matrix" Action can be used to import to each of the "prod Orgs" in a single action run from the "prod_deploy" branch.



## Prereqs in ThoughtSpot
Modern SDLC uses some newer ThoughtSpot features to make version control and deployment smooth across Orgs and instances.

### Enable obj_id and Publishing
Best practice for ThoughtSpot Cloud deployments involves setting the 'obj_id' property of every object, as well as using Parameters in TML, part of the Publishing feature. Both are features that must be enabled on your ThoughtSpot instances by support ticket.

### Set obj_id for each object
obj_id is a user-setable string identifier with uniqueness constraints per Org. Thus org_id.obj_id is equivalent to the unique GUID assigned to each object.

When obj_id is first enabled, pre-existing objects will have an empty value, while new objects will be auto-assigned a guaranteed unique obj_id.

Objects created via TML will have the obj_id provided in the TML file, but changes to an existing object's obj_id require a specific operation. 

You can set obj_id for any object in the ThoughtSpot UI within the TML Editor's Edit Menu or using the REST API V2.0 /metadata/update-obj-id endpoint.

### Create Variables and Variablize Connection and Table TML
Connection and Table TML both have properties related to the underlying databases that may vary between different environments - for example, warehouse and keypair in a Connection, or the database name or schema in a Table.

Variables provide a way to use identical TML files across different Orgs, where the actual values are stored securely in ThoughtSpot and updated via REST API calls.

Steps to use variables:

 1. Create the Variable: This generates a unique Variable identifier, and sets the type and if it is Secure (for secrets)
 2. Set Variable Values per Org: Define the values for the variable on each desired Org (not every Org must have values defined)
 3. Variablize the TML for the desired properties: Open the TML Editor and replace the existing actual values with the Variable name, using the syntax: "${variableName}"

Once the TML for an object has been 'variablized', it will always export with the variable reference rather than the actual value of the variable. This allows for complete re-use of the TML files across Orgs, while keeping any secrets safe.

## Setting up GitHub Repo
The workflow files use a number of variables and secrets to allow linking GitHub branches with ThoughtSpot Orgs (and multiple ThoughtSpot instances if you have them).

For those not used to building GitHub actions, there are numerous sources of 'context' flowing into a given job run.

Inputs from a manually triggered event defined within the 'workflow_dispatch' section are referenced using:
`${{ github.event.inputs.InputName }}`

### Branches

- **main / master**: Actions / workflows / other shared assets, but **no TML files** from any Org
- **dev**: Version Control for all content on Dev Org
- **release**: Branch for Specific Content to go through deployment to other Orgs
- **test_deploy**: Import TML from 'release' and do other Actions to Test Org
- **test**: Version control for all content on Test Org
- Optional UAT / etc.: 
    - **uat_deploy**: Import TML from 'release' and do other Actions to UAT Org
    - **uat**: Version control for all content on UAT Org
- **prod_deploy** Import TML from 'release' and do other Actions to Prod Org(s)
- Version control for prod Orgs:
    - **prod**: if single Prod, version control of all Content
    - **customer_orgs(s)**: version control branch for each Single Tenant Org

Pull requests / merges should be possible smoothly from "release" -> "test_deploy" -> "uat_deploy" -> "prod_deploy"

The version control branches should be made originally from the empty "main"/"master" so that the TML unique to their linked Org can be downloaded.

### Variables and Secrets
Variables and Secrets can from a defined Environment or the Repository (if they have the same name, Environment is used over Repository ):

`${{ vars.VarName }}`

`${{ secrets.SecretName }}`

If you have a simple setup, you may use Repository level secrets for the following:

Secrets:

 - TS_SERVER
 - TS_SECRET_KEY
 - TS_INSTANCE_ADMIN_USERNAME
 - TS_DOWNLOAD_USERNAME
 - TS_IMPORT_USERNAME

### Environment secrets and variables
GitHub provides an Environments concept for defining different sets of secrets and variables.

The following should be set at the Environment level:

Variables:
 
 - TS_ORG_NAME

You may want to set the following for various environments / Orgs:

Secrets:

 - TS_DOWNLOAD_USERNAME
 - TS_IMPORT_USERNAME

If you have different instances, set the following per Environment to match your ThoughtSpot instance / Org config:

Secrets:
 
 - TS_SERVER
 - TS_SECRET_KEY
 - TS_INSTANCE_ADMIN_USERNAME

 ### Matching Environments to Branches
 Within each workflow YAML file, there is an environment section that looks like:

    environment: |-
        ${{
           github.ref_name == 'release' && 'dev'
        || github.ref_name == 'dev' && 'dev'
        || github.ref_name == 'prod_deploy' && 'prod'
        || github.ref_name == 'prod' && 'prod'
        || github.ref_name == 'test_deploy' && 'test'
        || github.ref_name == 'test' && 'test'
        || github.ref_name == 'uat_deploy' && 'uat'
        || github.ref_name == 'uat' && 'uat'
        || 'default'
        }} 


`github.ref_name` is the branch name, while the value after the `&&` is the GitHub environment name. Feel free to modify this to match your preferred branch and environment naming scheme.

## Using the Workflows

### download_tml.yml

download_tml.yml defines the 'name: Download TML from Org to Branch' Action. 

This Action uses the TML Export REST API to get the current TML for a set of objects, into directories in the linked Git remote/branchName, then it commits back to the origin/branchName. It replaces the functionality of the earlier ThoughtSpot REST API called 'Commit Branch'.

There are filter inputs for a single Author Username or Tag Name. Use these to export only certain sets of TML - both Author and Tag Name are useful mechanisms for identifying which content in a 'dev' Org should become part of the actual 'release' that is deployed through to other branches and Orgs within ThoughtSpot.

Directories are generated automatically for the various TML object types. 

Within each directory, the TML files are stored along with a `last_download_runtime.txt` file. The `last_download_runtime.txt` file allows the Action to only download items that have been modified since the timestamp stored within the file, preventing unnecessary generation of identical TML. 

If you want all files to be retrieved, delete the `last_download_runtime.txt` file in a given directory (for data objects, delete in all the directories).

#### Version control vs. Deployment
ThoughtSpot has a Version Control capability, also linked to a GitHub repo, designed to make a commit automatically when any object has been changed within the UI. 

You can replicate this functionality using the `Download TML for Org to Branch` Action (on a polling timer), by looking for all objects in a given Org.

The workflow uses the `TS_DOWNLOAD_USERNAME` secret for the username within ThoughtSpot to do the REST API actions. This does not have to be an admin user, but the user must have Access to the objects that are being exported, along with the necessary Privileges via Roles. 

What you actually want to Deploy out through the SDLC stages as a 'release' to Prod may only be a subset of the total content in your dev Org in ThoughtSpot. 

You can use various stratgies for identifying which content will actually be part of the Release. As mentioned above, Tags ('release' or a version number scheme) or transferring the content to a particular Author username are two that are easily supported via the /metadata/search REST API which retrieves object listings. Other possibilities would be looking for all content that is linked to a given Connection or shared with certain Groups - those are slightly more complex API lookups but can be easily built out.

### import_tml.yml

import_tml.yml defines the `name: Import TML to Org` Action. 

This action takes all of the TML in a branch and uses the TML Import REST API to import it into a linked ThoughtSpot Org. It replaces the functionality of the previous REST API called 'Deploy Commits'. 

The workflow uses the `TS_IMPORT_USERNAME` secret, which will become the Author of the content in the Org it is imported to.

The results of the Python script are output to the console and are thus are available in the logs for the job run in GitHub. This includes the response from the TML Import command, which will show any warnings, errors, etc.

The workflow does not handle any Sharing (access control assignment). The content that is imported will not be available to anyone other than the `TS_IMPORT_USERNAME` and admin accounts without sharing it to other groups.

### import_tml_single_tenant_deploy.yml

import_tml_single_tenant_deploy.yml defines the `Import TML - Single Tenant Deployment Matrix` Action, which is the matrix strategy form of import_tml.yml, used to deploy out from a single 'production' / 'release' branch to any number of ThoughtSpot Orgs.

    strategy:
      matrix: 
        org_name: ${{ fromJson(vars.DEPLOY_ORGS_JSON_LIST) }}

The DEPLOY_ORGS_JSON_LIST should be a JSON array of Org Names, stored in the 'prod' environment like:

    ['Customer Org A', 'Customer Org B', ...]

Simply add to the org_name list under the strategy section, and each run of the Action will spawn jobs for each item in the list. When the action completes, you can check each job separately to check the logs. This utilizes the intentional feature within GitHub for running necessary variations on a job.

### change_obj_id_rename.yml
obj_id is used for filenames in the repo, but obj_id can be updated on ThoughtSpot via REST API or UI. This Action changes the appropriate filename to match the new obj_id, and updates the obj_id at the same time.

When the next Download TML Action is run, the TML file will be saved with the new filename, and the exported TML will contain the new obj_id, creating two commmits - first a filename change, then the obj_id changing at the top of the TML file.

These commits will merge smoothly into any other branches. The obj_id in other Orgs will need to be updated as well - see the other actions for changing obj_id across multiple Orgs at once.

### retrieve_org_id_from_org_name.py
retrieve_org_id_from_org_name.py is a helper script to get the numeric `org_id` for any arbitrary string Org Name on a ThoughtSpot instance.

It is called as a step in other workflows, and introduces an `ORG_ID` environment variable in to the `$GITHUB_ENV` for any future steps, via the following:

    python .github/workflows/retrieve_org_id_from_org_name.py >> $GITHUB_ENV