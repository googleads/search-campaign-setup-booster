# Search Campaign Setup Booster
**Disclaimer**: This is not an official Google Product.

This is a tool that illustrates how to leverage [Google Ads API](https://developers.google.com/google-ads/api/docs/start) to create campaigns and ad groups as well as, fetch keywords ideas and get estimated metrics.
This tool is created by Google Ads gPS GrCN team. Please contact your gPSer if you have any questions. As an alternative, you may also create an issue in the GitHub issue tracker.

# Introduction

This app is an all-in-one request form built with Flask on Google Cloud AppEngine for Search Ads. It helps onboarding Google Ads search campaigns with a single click, including creating multiple ad groups and generating text creatives.
This toolkit uses keyword planner API. Functions are executed on Google Cloud Platform. This toolkit can easily be deployed for both developers and users.

# Architecture

The tool contains the following parts:

Cloud: The project leverages the Google Cloud Function and scheduler to fetch requests from request Google Sheets, and extract categories from the website homepage, create campaign & ad groups, get new keywords from api, and write text creatives based on templates.

Web: This is a web frontend built on Flask and Google AppEngine, to let users easily submit requests. It has several parts to fill: receiver email, client information, target and bidding, and other optional fields.


# Setup
This tool requires a Google Ads API Developer Token and an OAuth Client ID and Secret.

- You can refer this [link](https://developers.google.com/google-ads/api/docs/start) to apply for a Developer Token.

- Follow this [link](https://support.google.com/cloud/answer/6158849?hl=en) for instructions on how to obtain an OAuth client ID and secret.

After creating your own Google Ads API Token and OAuth Client ID and Secret, you can continue these steps:

- copy `web/config.py.template` to `web/config.py`

- edit the params in `web/config.py`

```
PROJECT_ID = 'INSERT_GCP_ID_HERE'
CLIENT_ID = 'INSERT_CLIENT_ID_HERE'
CLIENT_SECRET = 'INSERT_CLIENT_SECRET_HERE'
DEVELOPER_TOKEN = 'INSERT_DEVELOPER_TOKEN_HERE'
```

# Init

Use Firestore as a NoSQL Storage. Give your email account access to both your Google Ads account and Google Sheets.

Remember to give the `project_id@appspot.gserviceaccount.com` Role and Permissions

`gcloud init` to choose your GCP

Run `python setup.py` to generate credentials for sheets and google ads

Run `gcloud auth application-default login` if you need google cloud credentials

Request form, make a copy of https://docs.google.com/spreadsheets/d/1L_h22t3SWFflmU-RbpUkOtM_Lc78Ooo-otf4azZzSNw

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