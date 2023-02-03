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

from email.policy import default
import pandas as pd
import numpy as np
import os
import random
from gspread_dataframe import get_as_dataframe, set_with_dataframe
from gspread_formatting.dataframe import format_with_dataframe
from sentence_transformers import SentenceTransformer
from datetime import datetime

#category_name, TRIX_id
#Generic to Customer,1JEpCxvJQX2Xeu2YVP7scAIRySdS5gyzWl8ZKK2_CTp8
_DEFAULT_CATEGORY_ID = '1JEpCxvJQX2Xeu2YVP7scAIRySdS5gyzWl8ZKK2_CTp8'
_DEFAULT_CATEGORY = 'Generic to Customer'
_CATEGORY_SIMILARITY_SHRESHOLD = 0.65

# this is TRIX_ID of Upload Templates
# don't change this TRIX file. creating new ads campaign TRIX rely on this TRIX.
UPLOAD_TEMPLATE_TRIX_ID = "1-Zx04HuqV_DN-GNTiOzmneGzgbS7Va6iXz7ereSQlLQ"
WORKSHEET_ID_LIST = [605956942, 1408798411, 1120179933, 822144526]

HEADLINE_PROMOTION_NUM = 3
HEADLINE_SHIPPING_NUM = 2
HEADLINE_PRODUCT_NUM = 10

DESCRIPTION_PROMOTION_NUM = 1
DESCRIPTION_SHIPPING_NUM = 1
DESCRIPTION_PRODUCT_NUM = 2

class GenerateModule:
  def __init__(self, gc):
    self.gc = gc
    print('Created a generate module object.')
  
  def get_similar(self, category, category_list):
    max_score = _CATEGORY_SIMILARITY_SHRESHOLD
    res = ''
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    embeddings = model.encode(category)

    for cat in category_list:
      cat_embeddings = model.encode(cat)
      similarity = embeddings.dot(cat_embeddings)/np.linalg.norm(embeddings)/np.linalg.norm(cat_embeddings)
      if similarity > max_score:
        max_score = similarity
        res = cat
    return res

  def _convert_TRIX_id(self, category, default_category):
    category = str(category)
    print(category)
    base_path = os.path.dirname(__file__)
    if not base_path:
      path = 'category.csv'
    else:
      path = base_path + '/' + 'category.csv'
    print(path)
    df = pd.read_csv(path)
    try:
      final_category = self.get_similar(category, list(df['category_name']))
      if final_category != '':
        print(f'Input {category}, find category {final_category}.')
      else:
        print(f'Input {category}, can not find similar category, use default {default_category}.')
        final_category = default_category
      ID_list = list(df[(df.category_name == final_category)]['TRIX_id'])
      return ID_list[0]
    except:
      print('Category TRIX not found. using default template.')
      ID_list = list(df[(df.category_name == default_category)]['TRIX_id'])
      return ID_list[0]

  def select_creatives(self, sh, position, promotion_num, shipping_num, product_num):
    res = []
    try:
      ws = sh.worksheet(position)
      df = pd.DataFrame.from_records(ws.get_all_records())
      df = df.drop_duplicates(subset=position)
      df = df.sample(frac=1)
      promotion = df[df['Label'] == 'Promotion']
      shipping = df[df['Label'] == 'Shipping']
      # filter promotion and shipping, others are general products
      product = df[df['Label'] != 'Promotion']
      product = product[product['Label'] != 'Shipping']
      res += list(promotion[position])[:promotion_num]
      res += list(shipping[position])[:shipping_num]
      res += list(product[position])[:product_num + promotion_num + shipping_num]
    except:
      res = [''] * (product_num + promotion_num + shipping_num)
    return res[:product_num + promotion_num + shipping_num]

  def get_new_headlines(self, category, client, counts, default_category=_DEFAULT_CATEGORY):
    TRIX_id = self._convert_TRIX_id(category, default_category)
    try:
      sh = self.gc.open_by_key(TRIX_id)
    except:
      sh = self.gc.open_by_key(_DEFAULT_CATEGORY_ID)
    headlines_module = self.select_creatives(sh, 'Headlines', HEADLINE_PROMOTION_NUM, HEADLINE_SHIPPING_NUM, HEADLINE_PRODUCT_NUM)
    random.shuffle(headlines_module)
    results = ["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""] # index of 0~15
    n = counts if (3<=counts and counts<=15) else 15
    for i in range(n):
      results[i] = headlines_module[i].replace('[product]', category).replace('[brand]',client).replace('{Keyword:','').replace('{KeyWord:','').replace('}','')
    print(results)
    return results

  def get_new_descriptions(self, category, client, counts, default_category=_DEFAULT_CATEGORY):
    TRIX_id = self._convert_TRIX_id(category, default_category)
    #print(TRIX_id)
    try:
      sh = self.gc.open_by_key(TRIX_id)
    except:
      sh = self.gc.open_by_key(_DEFAULT_CATEGORY_ID)    
    descriptions_module = self.select_creatives(sh, 'Descriptions', DESCRIPTION_PROMOTION_NUM, DESCRIPTION_SHIPPING_NUM, DESCRIPTION_PRODUCT_NUM)
    random.shuffle(descriptions_module)
    results = ["", "", "", "", ""] # index of 0~4
    n = counts if (2<=counts and counts<=4) else 4
    for i in range(n):
      results[i] = descriptions_module[i].replace('[product]', category).replace('[brand]',client).replace('{Keyword:','').replace('{KeyWord:','').replace('}','')
    print(results)
    return results

    # create a ads campaign TRIX using existing template
  def create_ads_campaign_trix(self, gc, service, client_name):
    ads_sh = self.gc.create(f"{client_name} Search Campaign Upload Form {datetime.now().strftime('%Y%m%d%H%M%S')}")
    source_sh_id = UPLOAD_TEMPLATE_TRIX_ID
    print(source_sh_id)
    destination_sh_id = ads_sh.id
    print(destination_sh_id)
    copy_sheet_to_another_spreadsheet_request_body = {
      # The ID of the spreadsheet to copy the sheet to.
      'destination_spreadsheet_id': destination_sh_id,
    }
    for ws_id in WORKSHEET_ID_LIST:
      request = service.spreadsheets().sheets().copyTo(spreadsheetId=source_sh_id, sheetId=ws_id, body=copy_sheet_to_another_spreadsheet_request_body)
      response = request.execute()
    print(ads_sh.url)
    ads_sh.del_worksheet(ads_sh.sheet1)
    ads_sh.get_worksheet(0).update_title('Campaign')
    ads_sh.get_worksheet(1).update_title('Adgroup')
    ads_sh.get_worksheet(2).update_title('Keyword')
    ads_sh.get_worksheet(3).update_title('Creative')
    #print(ads_sh.worksheets())
    return ads_sh

  def fill_in_ads_campaign_trix(self, gc, url, Campaign_res, Adgroup_res, Keyword_res, Creative_res):
    ads_sh = self.gc.open_by_url(url)
    Campaign_df = pd.DataFrame(Campaign_res)
    ws1 = ads_sh.worksheet('Campaign')
    set_with_dataframe(ws1, Campaign_df)
    format_with_dataframe(ws1, Campaign_df, include_column_header=True)
    Adgroup_df = pd.DataFrame(Adgroup_res)
    ws2 = ads_sh.worksheet('Adgroup')
    set_with_dataframe(ws2, Adgroup_df)
    format_with_dataframe(ws2, Adgroup_df, include_column_header=True)
    Keyword_df = pd.DataFrame(Keyword_res)
    ws3 = ads_sh.worksheet('Keyword')
    set_with_dataframe(ws3, Keyword_df)
    format_with_dataframe(ws3, Keyword_df, include_column_header=True)
    Creative_df = pd.DataFrame(Creative_res)
    ws4 = ads_sh.worksheet('Creative')
    set_with_dataframe(ws4, Creative_df)
    format_with_dataframe(ws4, Creative_df, include_column_header=True)

  def generate_campaign_dataframe(self, client_name, budget):
    campaign_res = []
    campaign_res.append({
    # 4 required fields total
      "Row Type": "Campaign", # Optional. Supported values: Campaign.
      "Action": "", # Optional. Supported values: Add; Edit; Remove.
      "Campaign status": "", # Optional. Supported values: Enabled; Paused; Removed.
      "Campaign ID": "", # Optional. Example: 1234.
      "Campaign": str(client_name)+" campaign", # Required. Example: Shoe campaign.
      "Campaign type": "Search", # Required on create. Supported values (Add): Search; Display; Video.
      "Networks": "", # Optional. Supported values: Google search; Search partners; Display Network; YouTube search; YouTube videos.
      "Budget": budget, # Required on create. Example: 10.00.
      "Delivery method": "", # Optional. Supported values: Standard.
      "Budget type": "", # Optional. Supported values: Daily; Campaign Total; Monthly.
      "Bid strategy type": "cpc", # Required on create. Supported values: CPC (enhanced); Manual CPC; cpc; Viewable CPM; cpm; CPA (target); Maximize clicks; Target ROAS; Target CPA; Maximize Conversions; Maximize Conversion Value; Manual CPV; cpv; Target CPM; CPC%; Target Impression Share; Commission; Invalid; Target Position.
      "Bid strategy": "", # Optional. Example: my bid strategy.
      "Campaign start date": "", # Optional. Example: 2024-02-29.
      "Campaign end date": "", # Optional. Example: 2024-05-31.
      "Language": "", # Optional. Example: en; zh_hk:excluded.
      "Location": "", # Optional. Example: 20 | mi | Seattle, Washington, United States : -5% ; Taipei City, Taiwan : +10% ; Montréal, Québec, Canada ; 600 | km | Redmond, Washington, United States:removed.
      "Exclusion": "", # Optional. Example: 20 | mi | Seattle, Washington, United States : -5% ; Taipei City, Taiwan : +10% ; Montréal, Québec, Canada ; 600 | km | Redmond, Washington, United States:removed.
      "Devices": "", # Optional. Example: Computers:+10%; Mobile devices with full browsers:-5%; Tablets with full browsers:+15%.
      "Label": "adsreadiness", # Optional. Example: label 1; label 2; label 3 [123-456-7890].
      "Target CPA": "", # Optional. Example: 10.00.
      "Target ROAS": "", # Optional. Example: 12%.
      "Target Impression Share": "", # Optional. Example: 15%.
      "Max CPC Bid Limit for Target IS": "", # Optional. Example: 10.00.
      "Location Goal for Target IS": "", # Optional. Supported values: Anywhere on results page; Top of results page; Absolute top of results page.
      "Tracking template": "", # Optional. Example: http://www.abc.com/tracking?param1=create&url={lpurl}.
      "Final URL suffix": "", # Optional. Example: x=y.
      "Custom parameter": "", # Optional. Example: {_color}=red ; {_bg}=blue.
      "Viewability vendor": "", # Optional. Supported values: None; MOAT; Double Verify; Integral Ad Science; comScore; Telemetry.
      "Inventory type": "", # Optional. Supported values: Expanded inventory; Standard inventory; 
      "Campaign subtype": "", # Optional. Supported values: Non-skippable; Drive conversions; Sequence; Mobile app; App engagement; Smart; Gmail display campaign; Engagement; Manufacturer; Comparison Listing; Shopping - Partners; Standard.
    })
    campaign_df = pd.DataFrame.from_dict(campaign_res)
    return campaign_df

  def generate_adgroup_dataframe(self, client_name, category_name):
    adgroup_res = []
    adgroup_res.append({
      # 2 required fields total
      "Row Type": "Ad group", # Optional. Supported values: Ad group.
      "Action": "", # Optional. Supported values: Add; Edit; Remove.
      "Ad group status": "", # Optional. Supported values: Enabled; Paused; Removed.
      "Campaign ID": "", # Optional. Example: 1234.
      "Campaign": str(client_name)+" campaign", # Required. Example: Shoe campaign.
      "Ad group ID": "", # Optional. Example: 1234.
      "Ad group": str(category_name)+" ad group", # Required. Example: Shoe ad group.
      "Ad group type": "", # Optional. Supported values: Standard; Dynamic; Display; Display engagement; Shopping - Product; Shopping - Showcase; Shopping - Smart; In-stream; In-feed video; Bumper; Non-skippable; Hotel; Hotels - Property promotion; Efficient reach; Video action.
      "Ad rotation": "", # Optional. Supported values: Optimize; Do not optimize.
      "Default max. CPC": "", # Optional. Example: 10.00.
      "CPC%": "", # Optional. Example: 12%.
      "Max. CPM": "", # Optional. Example: 10.00.
      "Max. CPV": "", # Optional. Example: 10.00.
      "Target CPA": "", # Optional. Example: 10.00.
      "Target CPM": "", # Optional. Example: 10.00.
      "Label": "adsreadiness", # Optional. Example: label 1; label 2; label 3 [123-456-7890].
      "Tracking template": "", # Optional. Example: http://www.abc.com/tracking?param1=create&url={lpurl}.
      "Final URL suffix": "", # Optional. Example: x=y.
      "Custom parameter": "", # Optional. Example: {_color}=red ; {_bg}=blue.
      "Target ROAS": "", # Optional. Example: 12%.
    })
    adgroup_df = pd.DataFrame.from_dict(adgroup_res)
    return adgroup_df

  def generate_keyword_dataframe(self, client_name, category_name, seed):
    keyword_res = []
    for i in range(0, len(seed)):
      keyword_res.append({
        # 3 required fields total
        "Row Type": "Keyword", # Optional. Supported values: Keyword.
        "Action": "", # Optional. Supported values: Add; Edit; Remove.
        "Keyword status": "", # Optional. Supported values: Enabled; Paused; Removed.
        "Campaign ID": "", # Optional. Example: 1234.
        "Campaign": str(client_name)+" campaign", # Required. Example: Shoe campaign.
        "Ad group ID": "", # Optional. Example: 1234.
        "Ad group": str(category_name)+" ad group", # Required. Example: Shoe ad group.
        "Keyword ID": "", # Optional. Example: 1234.
        "Keyword": seed[i], # Required on create. Example: buy frisbee.
        "Type": "", # Optional. Supported values: Exact match; Phrase match; Broad match.
        "Label": "adsreadiness", # Optional. Example: label 1; label 2; label 3 [123-456-7890].
        "Default max. CPC": "", # Optional. Example: 10.00.
        "Max. CPV": "", # Optional. Example: 10.00.
        "Final URL": "", # Optional. Example: http://www.example.com ; https://www.example.org.
        "Mobile final URL": "", # Optional. Example: http://www.example.com ; https://www.example.org.
        "Tracking template": "", # Optional. Example: http://www.abc.com/tracking?param1=create&url={lpurl}.
        "Final URL suffix": "", # Optional. Example: x=y.
        "Custom parameter": "", # Optional. Example: {_color}=red ; {_bg}=blue.
      })
    keyword_df = pd.DataFrame.from_dict(keyword_res)
    return keyword_df

  def generate_creative_dataframe(self, client_name, category_name, URL, headlines_list, descriptions_list):
    creative_res = []
    creative_res.append({
      # 4 required fields total
      "Row Type": "Ad", # Optional. Supported values: Ad.
      "Action": "", # Optional. Supported values: Add; Edit; Remove.
      "Ad status": "", # Optional. Supported values: Enabled; Paused; Removed.
      "Campaign ID": "", # Optional. Example: 1234.
      "Campaign": str(client_name)+" campaign", # Required. Example: Shoe campaign.
      "Ad group ID": "", # Optional. Example: 1234.
      "Ad group": str(category_name)+" ad group", # Required. Example: Shoe ad group.
      "Ad ID": "", # Optional. Example: 1234.
      "Ad type": "Responsive search ad", # Required on create. Supported values: Responsive search ad.
      "Label": "adsreadiness", # Optional. Example: label 1; label 2; label 3 [123-456-7890].
      "Headline 1": headlines_list[0],
      "Headline 2": headlines_list[1],
      "Headline 3": headlines_list[2],
      "Headline 4": headlines_list[3],
      "Headline 5": headlines_list[4],
      "Headline 6": headlines_list[5],
      "Headline 7": headlines_list[6],
      "Headline 8": headlines_list[7],
      "Headline 9": headlines_list[8],
      "Headline 10": headlines_list[9], 
      "Headline 11": headlines_list[10],
      "Headline 12": headlines_list[11],
      "Headline 13": headlines_list[12],
      "Headline 14": headlines_list[13],
      "Headline 15": headlines_list[14],
      "Description": descriptions_list[0],
      "Description 2": descriptions_list[1],
      "Description 3": descriptions_list[2],
      "Description 4": descriptions_list[3],
      "Headline 1 position": "",
      "Headline 2 position": "",
      "Headline 3 position": "",
      "Headline 4 position": "",
      "Headline 5 position": "",
      "Headline 6 position": "",
      "Headline 7 position": "",
      "Headline 8 position": "",
      "Headline 9 position": "",
      "Headline 10 position": "",
      "Headline 11 position": "",
      "Headline 12 position": "",
      "Headline 13 position": "",
      "Headline 14 position": "",
      "Headline 15 position": "",
      "Description 1 position": "",
      "Description 2 position": "",
      "Description 3 position": "",
      "Description 4 position": "",
      "Path 1": "",
      "Path 2": "",
      "Final URL": URL, # Required on create. Example: http://www.example.com ; https://www.example.org.
      "Mobile final URL": "", # Optional. Example: http://www.example.com ; https://www.example.org.
      "Tracking template": "", # Optional. Example: http://www.abc.com/tracking?param1=create&url={lpurl}.
      "Final URL suffix": "", # Optional. Example: x=y.
      "Custom parameter": "", # Optional. Example: {_color}=red ; {_bg}=blue.
    })
    creative_df = pd.DataFrame.from_dict(creative_res)
    return creative_df

  def generate_multiple_adgroups(self, r, single_category, single_url, adgroup_df, keyword_df, creative_df, keywords_list, headlines_list, descriptions_list):
    adgroup_df.append({
      # 2 required fields total
      "Row Type": "Ad group", # Optional. Supported values: Ad group.
      "Action": "", # Optional. Supported values: Add; Edit; Remove.
      "Ad group status": "", # Optional. Supported values: Enabled; Paused; Removed.
      "Campaign ID": "", # Optional. Example: 1234.
      "Campaign": str(r['Client Name'])+" campaign", # Required. Example: Shoe campaign.
      "Ad group ID": "", # Optional. Example: 1234.
      "Ad group": str(single_category)+" ad group", # Required. Example: Shoe ad group.
      "Ad group type": "", # Optional. Supported values: Standard; Dynamic; Display; Display engagement; Shopping - Product; Shopping - Showcase; Shopping - Smart; In-stream; In-feed video; Bumper; Non-skippable; Hotel; Hotels - Property promotion; Efficient reach; Video action.
      "Ad rotation": "", # Optional. Supported values: Optimize; Do not optimize.
      "Default max. CPC": "", # Optional. Example: 10.00.
      "CPC%": "", # Optional. Example: 12%.
      "Max. CPM": "", # Optional. Example: 10.00.
      "Max. CPV": "", # Optional. Example: 10.00.
      "Target CPA": "", # Optional. Example: 10.00.
      "Target CPM": "", # Optional. Example: 10.00.
      "Label": "adsreadiness", # Optional. Example: label 1; label 2; label 3 [123-456-7890].
      "Tracking template": "", # Optional. Example: http://www.abc.com/tracking?param1=create&url={lpurl}.
      "Final URL suffix": "", # Optional. Example: x=y.
      "Custom parameter": "", # Optional. Example: {_color}=red ; {_bg}=blue.
      "Target ROAS": "", # Optional. Example: 12%.
    })
    for i in range(0, len(keywords_list)):
      keyword_df.append({
        # 3 required fields total
        "Row Type": "Keyword", # Optional. Supported values: Keyword.
        "Action": "", # Optional. Supported values: Add; Edit; Remove.
        "Keyword status": "", # Optional. Supported values: Enabled; Paused; Removed.
        "Campaign ID": "", # Optional. Example: 1234.
        "Campaign": str(r['Client Name'])+" campaign", # Required. Example: Shoe campaign.
        "Ad group ID": "", # Optional. Example: 1234.
        "Ad group": str(single_category)+" ad group", # Required. Example: Shoe ad group.
        "Keyword ID": "", # Optional. Example: 1234.
        "Keyword": keywords_list[i], # Required on create. Example: buy frisbee.
        "Type": "", # Optional. Supported values: Exact match; Phrase match; Broad match.
        "Label": "adsreadiness", # Optional. Example: label 1; label 2; label 3 [123-456-7890].
        "Default max. CPC": "", # Optional. Example: 10.00.
        "Max. CPV": "", # Optional. Example: 10.00.
        "Final URL": "", # Optional. Example: http://www.example.com ; https://www.example.org.
        "Mobile final URL": "", # Optional. Example: http://www.example.com ; https://www.example.org.
        "Tracking template": "", # Optional. Example: http://www.abc.com/tracking?param1=create&url={lpurl}.
        "Final URL suffix": "", # Optional. Example: x=y.
        "Custom parameter": "", # Optional. Example: {_color}=red ; {_bg}=blue.
      })
    creative_df.append({
      # 4 required fields total
      "Row Type": "Ad", # Optional. Supported values: Ad.
      "Action": "", # Optional. Supported values: Add; Edit; Remove.
      "Ad status": "", # Optional. Supported values: Enabled; Paused; Removed.
      "Campaign ID": "", # Optional. Example: 1234.
      "Campaign": str(r['Client Name'])+" campaign", # Required. Example: Shoe campaign.
      "Ad group ID": "", # Optional. Example: 1234.
      "Ad group": str(single_category)+" ad group", # Required. Example: Shoe ad group.
      "Ad ID": "", # Optional. Example: 1234.
      "Ad type": "Responsive search ad", # Required on create. Supported values: Responsive search ad.
      "Label": "adsreadiness", # Optional. Example: label 1; label 2; label 3 [123-456-7890].
      "Headline 1": headlines_list[0],
      "Headline 2": headlines_list[1],
      "Headline 3": headlines_list[2],
      "Headline 4": headlines_list[3],
      "Headline 5": headlines_list[4],
      "Headline 6": headlines_list[5],
      "Headline 7": headlines_list[6],
      "Headline 8": headlines_list[7],
      "Headline 9": headlines_list[8],
      "Headline 10": headlines_list[9], 
      "Headline 11": headlines_list[10],
      "Headline 12": headlines_list[11],
      "Headline 13": headlines_list[12],
      "Headline 14": headlines_list[13],
      "Headline 15": headlines_list[14],
      "Description": descriptions_list[0],
      "Description 2": descriptions_list[1],
      "Description 3": descriptions_list[2],
      "Description 4": descriptions_list[3],
      "Headline 1 position": "",
      "Headline 2 position": "",
      "Headline 3 position": "",
      "Headline 4 position": "",
      "Headline 5 position": "",
      "Headline 6 position": "",
      "Headline 7 position": "",
      "Headline 8 position": "",
      "Headline 9 position": "",
      "Headline 10 position": "",
      "Headline 11 position": "",
      "Headline 12 position": "",
      "Headline 13 position": "",
      "Headline 14 position": "",
      "Headline 15 position": "",
      "Description 1 position": "",
      "Description 2 position": "",
      "Description 3 position": "",
      "Description 4 position": "",
      "Path 1": "",
      "Path 2": "",
      "Final URL": single_url, # Required on create. Example: http://www.example.com ; https://www.example.org.
      "Mobile final URL": "", # Optional. Example: http://www.example.com ; https://www.example.org.
      "Tracking template": "", # Optional. Example: http://www.abc.com/tracking?param1=create&url={lpurl}.
      "Final URL suffix": "", # Optional. Example: x=y.
      "Custom parameter": "", # Optional. Example: {_color}=red ; {_bg}=blue.
    })
