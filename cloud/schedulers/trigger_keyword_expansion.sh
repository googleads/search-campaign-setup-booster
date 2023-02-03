gcloud scheduler jobs create pubsub search_ads_job --schedule "*/10 * * * *" --topic search_ads --message-body "job_started" --time-zone "Etc/UTC"
