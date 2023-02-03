from flask import Flask, redirect
from flask import render_template
from flask import request, url_for
from google.oauth2.credentials import Credentials
from google.cloud import firestore
import base64
import gspread
import datetime
import config
import logging
import google.cloud.logging

app = Flask(__name__)
app.config.from_object(config)
db = firestore.Client()
credential_dict = db.collection(app.config['CREDENTIAL_COLLECTION_NAME']).document(app.config['CREDENTIAL_DOCUMENT_NAME']).get().to_dict()

client = google.cloud.logging.Client()
client.setup_logging()

@app.route('/')
def index():
  # check credential
  if not credential_dict:
    return redirect(url_for('install'))
  credentials = Credentials.from_authorized_user_info(credential_dict)
  # if os.getenv('SERVER_SOFTWARE','local') == 'local':
  #   credentials = Credentials.from_authorized_user_info(credential)
  # else:
  #   credentials, _ = google.auth.default()
  gc = gspread.authorize(credentials)
  sh = gc.open_by_key(app.config['KEYWORD_EXPANSION_TRIX_ID'])
  ws = sh.worksheet('Templates')
  category_list = ws.col_values(1)[1:]
  return render_template('index.html', category_list=category_list)

@app.route('/success')
def success():
  return render_template('success.html')

@app.route('/install')
def install():
  if not credential_dict:
    return render_template('install.html')
  else:
    return redirect('/')
    # return render_template('install.html')

@app.route('/submit', methods=['POST'])
def submit():
  email = request.form.get('email')
  client_name = request.form.get('client_name')
  customer_id = request.form.get('customer_id')
  category_name = request.form.get('category_name')
  seed = request.form.get('seed')
  url = request.form.get('url')
  language = request.form.get('language')
  country = request.form.get('country')
  budget = float(request.form.get('budget'))
  bid_strategy_type = request.form.get('bid_strategy_type')
  #optional
  produce_type = request.form.get('produce_type')
  print(request.headers)
  # timestamp, Email-address, client-region, client-type, client-name, category_name, kwexp, seed, country, language, URL, budget, bid_strategy_type
  data = {}
  data[1] = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime('%-m/%-d/%Y %-H:%M:%S')
  data[2] = email
  data[3] = client_name
  data[4] = customer_id
  data[5] = category_name
  data[6] = seed
  data[7] = country
  data[8] = language
  data[9] = url
  data[10] = budget
  data[11] = bid_strategy_type
  data[12] = produce_type
  # save data to google sheet
  credentials = Credentials.from_authorized_user_info(credential_dict)
  # if os.getenv('SERVER_SOFTWARE','local') == 'local':
  #   credentials = Credentials.from_authorized_user_info(credential)
  # else:
  #   credentials, _ = google.auth.default()
  gc = gspread.authorize(credentials)
  sh = gc.open_by_key(app.config['KEYWORD_EXPANSION_TRIX_ID'])
  ws = sh.worksheet('Form Responses 1')
  records = ws.get_all_records()
  # ROW number of next record. Plus 2 means one line for header, one line for new record.
  newline = len(records) + 2
  # print(str(len(records)))
  # print(newline)
  for i in range(1, 13):
    ws.update_cell(newline, i, data[i])

  return render_template('success.html', email=email)

@app.route('/sheets')
def sheets():
  credentials = Credentials.from_authorized_user_info(credential_dict)
  gc = gspread.authorize(credentials)
  # gc = gspread.service_account()
  sh = gc.open_by_key(app.config['KEYWORD_EXPANSION_TRIX_ID'])
  ws = sh.worksheet('Form Responses 1')
  records = ws.get_all_records()
  return str(len(records))