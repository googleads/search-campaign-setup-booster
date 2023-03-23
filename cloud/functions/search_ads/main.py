# Copyright 2023 Google LLC

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     https://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from mining import MiningModule
from estimate import EstimateModule
from generate import GenerateModule
from collection import CollectionModule

from google.ads.googleads.client import GoogleAdsClient
from google.oauth2.credentials import Credentials
from google.cloud import firestore
from gspread_dataframe import get_as_dataframe, set_with_dataframe
from gspread_formatting.dataframe import format_with_dataframe
import google.auth
import gspread

import pandas as pd
import os
import json

import google.cloud.logging
client = google.cloud.logging.Client()
client.setup_logging()

import logging
import datetime
import time
import random
from googleapiclient import discovery

# credential settings
CREDENTIAL_COLLECTION_NAME = 'credentials'
CREDENTIAL_DOCUMENT_NAME = 'search'
KEYWORD_EXPANSION_SHEET_ID = "INSERT_SHEET_ID_HERE"

#Google Ads Account Id
CUSTOMER_ID = 'INSERT_CUSTOMER_ID_HERE'

#Google Group Email
GOOGLE_GROUP_EMAIL = 'INSERT_GROUP_EMAIL_HERE'

# a string to mark record status
STATUS_DONE = 'DONE'
STATUS_ERROR = 'ERROR'
# the number of columns of the form. change this value to easier add more column in the future.
# right now the form have 13 columns. from A[Timestamp] to M[Bid Strategy Type]
FORM_COLUMN = 12
# 4 additional columns are: Status, Logs, 2 URLs

def create_keyword_expansion_sheet(gc, client_name):
  kwe_sh = gc.create(f"{client_name} Keywords Expansion Result {datetime.datetime.now().strftime('%Y%m%d%H%M%S')}")
  return kwe_sh

def fill_in_keywork_expansion_sheet(gc, url, dataframe):
  kwe_sh = gc.open_by_url(url)
  kwe_ws = kwe_sh.sheet1
  set_with_dataframe(kwe_ws, dataframe)
  format_with_dataframe(kwe_ws, dataframe, include_column_header=True)

def select_30_keywords(kwe_res):
  if kwe_res.shape[0] <= 30:
    keywords_result = list(kwe_res['keyword'])
  else:
    # kwe_res = kwe_res.sort_values(['monthly_search', 'cpc'], ascending=[True, True])
    threshold = 300
    filtered_keywords = kwe_res[ kwe_res['monthly_search'] < threshold ]
    while filtered_keywords.shape[0] <30:
      threshold += 100
      filtered_keywords = kwe_res[ kwe_res['monthly_search'] < threshold ]
    filtered_keywords = filtered_keywords.sort_values(['cpc'], ascending=[True])
    keywords_result = list(filtered_keywords[0:30]['keyword'])
  return keywords_result

def mining_and_estimate(mining_module, estimate_module, country, language, URL, seed):
  # mining process
  mining_res = mining_module.get_new_keywords(CUSTOMER_ID, country, language, keyword_texts=seed, page_url=URL)
  # estimate process
  if len(mining_res) > 0:
    print(len(mining_res))
    # maximum of 10000 request operations
    mining_res = mining_res[:10000]
    mining_keywords = list(set([k['keyword'] for k in mining_res]))
    estimate_res = estimate_module.estimate(CUSTOMER_ID, mining_keywords, country, language)
    mining_df = pd.DataFrame.from_dict(mining_res)
    estimate_df = pd.DataFrame.from_dict(estimate_res)
    #print(mining_df)
    #print(estimate_df)
    # sending a new sheet
    df = pd.merge(mining_df, estimate_df, how='left', on='keyword')
  else:
    mining_res = [{"keyword":"NULL"}]
    df = pd.DataFrame.from_dict(mining_res)
  return df  

def solve_request(event, context):
  """Triggered from a message on a Cloud Pub/Sub topic.
  Args:
       event (dict): Event payload.
       context (google.cloud.functions.Context): Metadata for the event.
  """
  db = firestore.Client()
  credential_ref = db.collection(CREDENTIAL_COLLECTION_NAME)
  credential = credential_ref.document(CREDENTIAL_DOCUMENT_NAME).get().to_dict()
  client = GoogleAdsClient.load_from_dict(credential)
  if os.getenv('SERVER_SOFTWARE','local') == 'local':
    credentials = Credentials.from_authorized_user_info(credential)
  else:
    credentials, _ = google.auth.default()
  service = discovery.build('sheets', 'v4', credentials=credentials)
    
  gc = gspread.authorize(credentials)
  sh = gc.open_by_key(KEYWORD_EXPANSION_SHEET_ID)
  ws = sh.worksheet('Form Responses 1')

  # from class mining and estimate
  mining = MiningModule(client)
  estimate = EstimateModule(client)
  generate = GenerateModule(gc)
  collection = CollectionModule()
  records = ws.get_all_records()
  total_lines = len(records)
  print(total_lines)

  # process each row as r
  row_num = 1
  max_requests = 5
  current_count = 0
  for r in records:
    # print(r)
    row_num += 1
    if r['Status'] != STATUS_DONE and r['Status'] != STATUS_ERROR:
      # new request
      current_count += 1
      try:
        # SHEET Request
        request_ws = sh.worksheet('Form Responses 1')

        # generate keyword expansion result to sheet
        kwe_sh = create_keyword_expansion_sheet(gc, r['Client Name'])
        # get seed from sheet
        seed = r['Seed Keywords']
        if len(seed) > 0:
          seed = r['Seed Keywords'].splitlines()
          # maximum of 20 api keywords
          seed = seed[:20]
        else:
          seed = None
        print(seed)
        #print(r['Target Country'], r['Target Language'], r['URL'], seed)
        kwe_res = mining_and_estimate(mining, estimate, r['Target Country'], r['Target Language'], r['URL'], seed)
        # print(kwe_res)
        # top_20_keywords = list(kwe_res[0:20]['keyword'])
        # print(top_20_keywords)
        top_30_keywords = select_30_keywords(kwe_res)
        # print(top_30_keywords)
        # kwe_res = kwe_res.sort_values(['monthly_search', 'cpc'], ascending=[True, True])
        fill_in_keywork_expansion_sheet(gc, kwe_sh.url, kwe_res)
        request_ws.update_cell(row_num, FORM_COLUMN+3, kwe_sh.url)
        # fetch product category from homepage url
        if r['Optional Product Type'] == '':
          product_category = collection.extract(r['URL'], 'sheet')
          if not product_category:
            print("can not extract url")
          else:
            request_ws.update_cell(row_num, FORM_COLUMN, product_category)
            r['Optional Product Type'] = product_category

        # generate Ads campaign information to sheet
        ads_sh = generate.create_ads_campaign_sheet(gc, service, r['Client Name'])
        # 'Optional Product Type': ''
        if r['Optional Product Type'] == '':
          # headlines should between 3 to 15
          # descriptions should between 2 to 4
          headlines_list = generate.get_new_headlines(r['Category Name'], r['Client Name'], 15)
          descriptions_list = generate.get_new_descriptions(r['Category Name'], r['Client Name'], 4)
          Campaign_res = generate.generate_campaign_dataframe(r['Client Name'], r['Budget'])
          Adgroup_res = generate.generate_adgroup_dataframe(r['Client Name'], r['Category Name'])
          Keyword_res = generate.generate_keyword_dataframe(r['Client Name'], r['Category Name'], top_30_keywords)
          Creative_res = generate.generate_creative_dataframe(r['Client Name'], r['Category Name'], r['URL'], headlines_list, descriptions_list)
        
        # 'Optional Product Type': 'Dresses:/collections/dresses\r\nClothing:/collections/clothing'
        else: 
          # headlines should between 3 to 15
          # descriptions should between 2 to 4
          raw_optional_data = r['Optional Product Type'].splitlines()
          adgroup_df = []
          keyword_df = []
          creative_df = []

          for s in raw_optional_data:
            single_category = s.split(':')[0]
            single_url = str(r['URL']) + str(s.split(':')[1])
            single_url = single_url.replace('//','/').replace(':/','://')
            seed = []
            seed.append(single_category)
            # for every Adgroup
            # generate keywords by single_category
            keywords_res = mining_and_estimate(mining, estimate, r['Target Country'], r['Target Language'], single_url, seed)
            keywords_list = select_30_keywords(keywords_res)
            # generate headlines 
            headlines_list = generate.get_new_headlines(single_category, r['Client Name'], 15, r['Category Name'])
            # generate descriptions
            descriptions_list = generate.get_new_descriptions(single_category, r['Client Name'], 4, r['Category Name'])
            generate.generate_multiple_adgroups(r, single_category, single_url, adgroup_df, keyword_df, creative_df, keywords_list, headlines_list, descriptions_list)
          Campaign_res = generate.generate_campaign_dataframe(r['Client Name'], r['Budget'])
          Adgroup_res = pd.DataFrame.from_dict(adgroup_df)
          Keyword_res = pd.DataFrame.from_dict(keyword_df)
          Creative_res = pd.DataFrame.from_dict(creative_df)
        
        generate.fill_in_ads_campaign_sheet(gc, ads_sh.url, Campaign_res, Adgroup_res, Keyword_res, Creative_res)
        # share keyword sheet and template sheet
        kwe_sh.share(r['Email Address'], perm_type='user', role='writer')
        kwe_sh.share(GOOGLE_GROUP_EMAIL, perm_type='group', role='writer', notify=False)
        ads_sh.share(r['Email Address'], perm_type='user', role='writer')
        ads_sh.share(GOOGLE_GROUP_EMAIL, perm_type='group', role='writer', notify=False)

        request_ws.update_cell(row_num, FORM_COLUMN+4, ads_sh.url)

        # change this record status to "DONE"
        request_ws.update_cell(row_num, FORM_COLUMN+1, STATUS_DONE)
        log_text = 'record process finished at '
        log_text += datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime('%-m/%-d/%Y %-H:%M:%S')
        print(log_text)
        request_ws.update_cell(row_num, FORM_COLUMN+2, log_text)

      except Exception as err:
        print(err)
        # write err info to CELL Logs
        request_ws.update_cell(row_num, FORM_COLUMN+1, STATUS_ERROR)
        request_ws.update_cell(row_num, FORM_COLUMN+2, str(err))
      if current_count >= max_requests:
        break
if __name__ == "__main__":
  solve_request(None, None)
