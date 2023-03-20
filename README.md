# Search Campaign Setup Booster
Disclaimer: This is not an official Google Product.

This is an example of how to leverage Google Ads API to create campaign, adgroup, fetch keywords ideas and get estimated metrics.

This tool is created by Google Ads gPS GrCN team. Please contact your PoC if you have any questions. Or you can fire an issue in the github page.

## Introduction

This app is an all-in-one request form build with Flask on google cloud app engine for search ads. It helps onboarding Google Ads search campaigns within one click, including creating multiple ad groups and generating text creatives.

This toolkit uses keyword planner API, and functions are executed on GCP. Toolkits can easily be deployed for developers and users. 

### Architecture

The tool contains "cloud" and "web" part:

cloud: leverage the google cloud function and scheduler, to fetch requests from request google sheets, and execute extract the website, create campaign & adgroups, get new keywords from api, and write text creatives based on templates.

web: a UI built on flask and google app engine, to let users easily submit requests. It has several parts to fill: receiver email, client information, target and bidding, and other optional fields.

# Setup
It requires the google ads api token and oauth client id and secret

You can refer this [link](https://developers.google.com/google-ads/api/docs/start) to apply a api token

and this [link](https://support.google.com/cloud/answer/6158849?hl=en) to obtain oauth

Please create your own before using, and:

copy `web/config.py.template` to `web/config.py`

edit the params in `web/config.py`

```
PROJECT_ID = 'search-project-id'
CLIENT_ID = '571404068263-xxxxxxxxqn7o34oh2k0m.apps.googleusercontent.com'
CLIENT_SECRET = 'XXXXX-kmffYFP6p5VK5bOWh_S_bXXXXX'
DEVELOPER_TOKEN = 'WXXXXXXXXXX6ktw'
```

# Init

Use Firestore as NoSQL Storage, have your account with ads API token access and sheets access

remember to give the `project_id@appspot.gserviceaccount.com` Role and Permissions

`gcloud init` to choose your GCP

run `python setup.py` to generate credentials for sheets and google ads

run `gcloud auth application-default login` if you need google cloud credentials

Request form, make a copy of https://docs.google.com/spreadsheets/d/1mhiNXsc083Ykf7BTbhKxctCSN-_1BpgyEx-lb0gVBzU

# Develop

web: open your terminal and run:

```
sh dev.sh
```
or
```
export FLASK_APP=web/main.py
export FLASK_ENV=development
flask run --host=0.0.0.0 --port=80
```

Check cloud/functions/search_ads for more details:

- collection.py: extracts website structures, each category creates an adgroup
- generate.py: generates text creatives based on templates
- mining.py and estimate.py: fetches new keywords and estimate metrics with google ads keyword ideas api
- category.csv: templates lists
- language.csv and location.csv: language and location code to name mapping csv

functions

`python /path/to/functions/main.py`

# Deploy
open your terminal and run:

`sh deploy.sh`

then run:

```
cd web
gcloud app deploy
```
Navigate your browser to the https://yourappname.appspot.com/ link

# Upload
How to use the results after execution:
- keywords recommendation results: used as a complementary of all keywords, you can choose more keywords from it.
- ads campaign results: either upload from google ads backend as a google sheet or download to an excel file, then upload as a file.

# Disclaimer

This is not an official Google product.

This solution, including any related sample code or data, is made available on an “as is,” “as available,” and “with all faults” basis, solely for illustrative purposes, and without warranty or representation of any kind. 

This solution is experimental, unsupported and provided solely for your convenience. Your use of it is subject to your agreements with Google, as applicable, and may constitute a beta feature as defined under those agreements. 

To the extent that you make any data available to Google in connection with your use of the solution, you represent and warrant that you have all necessary and appropriate rights, consents and permissions to permit Google to use and process that data. 

By using any portion of this solution, you acknowledge, assume and accept all risks, known and unknown, associated with its usage, including with respect to your deployment of any portion of this solution in your systems, or usage in connection with your business, if at all.

# License

[Apache 2.0 License](http://www.apache.org/licenses/LICENSE-2.0.html)