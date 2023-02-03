from google.cloud import firestore
from web import config
from google_auth_oauthlib.flow import InstalledAppFlow

collection = config.CREDENTIAL_COLLECTION_NAME
document = config.CREDENTIAL_DOCUMENT_NAME

scopes = scopes = [
                  "https://www.googleapis.com/auth/spreadsheets",
                  "https://www.googleapis.com/auth/adwords",
                  "https://www.googleapis.com/auth/drive",
                  "https://www.googleapis.com/auth/gmail.compose"
                  ]

project_id = config.PROJECT_ID
client_id = config.CLIENT_ID
client_secret = config.CLIENT_SECRET
developer_token = config.DEVELOPER_TOKEN

client_config = {
  "installed":{
    "auth_uri":"https://accounts.google.com/o/oauth2/auth",
    "token_uri":"https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs",
    "redirect_uris":["http://localhost"]
  }
}
client_config["installed"]["project_id"] = project_id
client_config["installed"]["client_id"] = client_id
client_config["installed"]["client_secret"] = client_secret

flow = InstalledAppFlow.from_client_config(
  client_config, scopes=scopes
)

flow.run_local_server()

print("Access token: %s" % flow.credentials.token)
print("Refresh token: %s" % flow.credentials.refresh_token)

credential = {"use_proto_plus": False}
credential['client_id'] = client_id
credential['client_secret'] = client_secret
credential["refresh_token"] = flow.credentials.refresh_token
credential["developer_token"] = developer_token

db = firestore.Client()
credential_ref = db.collection(config.CREDENTIAL_COLLECTION_NAME).document(config.CREDENTIAL_DOCUMENT_NAME)
credential_ref.set(credential)
print('Install Finished!')
