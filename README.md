# introduction

This app is an all-in-one request form build with Flask on google cloud app engine for search ads.

It requires the google ads api token and oauth client id and secret

Please create your own before using, and:

copy `web/config.py.template` to `web/config.py`

edit the params in `web/config.py`

Contact guyi@ if you have any question.

# init

Use Firestore as NoSQL Storage, have your account with ads API token access and sheets access

remember to give the `project_id@appspot.gserviceaccount.com` Role and Permissions

`gcloud init` to choose your GCP

run `python setup.py` to generate credentials for sheets and google ads

run `gcloud auth application-default login` if you need google cloud credentials

Request form, make a copy of https://docs.google.com/spreadsheets/d/1mhiNXsc083Ykf7BTbhKxctCSN-_1BpgyEx-lb0gVBzU

# develop

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

functions

`python /path/to/functions/main.py`

# deploy
open your terminal and run:

`sh deploy.sh`

then run:

```
cd web
gcloud app deploy
```


# License

[Apache 2.0 License](http://www.apache.org/licenses/LICENSE-2.0.html)