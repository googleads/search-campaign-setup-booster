# Copyright 2022 Google LLC

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     https://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#!/bin/bash

gcloud services enable 'sheets.googleapis.com'
gcloud services enable 'googleads.googleapis.com'
gcloud services enable 'firestore.googleapis.com'
gcloud services enable 'pubsub.googleapis.com'
gcloud services enable 'cloudfunctions.googleapis.com'
gcloud services enable 'appengine.googleapis.com'
gcloud services enable 'cloudscheduler.googleapis.com'
gcloud services enable 'cloudbuild.googleapis.com'


#make sure your work-directory is in app/cloud, otherwise function/.. can't be found
gcloud functions deploy search_ads --source cloud/functions/search_ads --entry-point solve_request --trigger-topic search_ads --timeout=540 --runtime python38 --memory=1024MB  --no-allow-unauthenticated
gcloud scheduler jobs create pubsub search_ads_job --schedule "*/10 * * * *" --topic search_ads --message-body "job_started" --time-zone "Etc/UTC"

#make sure your work-directory is in app/web
gcloud app deploy
