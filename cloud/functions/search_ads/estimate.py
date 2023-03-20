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

import pandas as pd
import os
import sys
import uuid
import json
from google.ads.googleads.errors import GoogleAdsException

_DEFAULT_LOCATION_IDS = ["1023191"]  # location ID for New York, NY
_DEFAULT_LANGUAGE_ID = "1000"  # language ID for English
_CPC_BID_MICROS = 1500000

class EstimateModule:
  def __init__(self, client):
    self.client = client

  def _map_locations_ids_to_resource_names(self, location_ids):
    """Converts a list of location IDs to resource names.

    Args:
        client: an initialized GoogleAdsClient instance.
        location_ids: a list of location ID strings.

    Returns:
        a list of resource name strings using the given location IDs.
    """
    build_resource_name = self.client.get_service(
        "GeoTargetConstantService"
    ).geo_target_constant_path
    return [build_resource_name(location_id) for location_id in location_ids]

  def _convert_location_ids(self, locations):
    df = pd.read_csv(os.path.dirname(__file__) + '/' + 'location.csv')
    try:
      return list(df[(df.code.isin(locations))|(df.criteria_id.isin(locations))|(df.name.isin(locations))]['criteria_id'])
    except:
      return _DEFAULT_LOCATION_IDS

  def _convert_language_id(self, language):
    language = str(language)
    df = pd.read_csv(os.path.dirname(__file__) + '/' + 'language.csv')
    try:
      return int(df[(df.code == language)|(df.language==language)|(df.criteria_id.astype('string')==language)]['criteria_id'])
    except:
      return _DEFAULT_LANGUAGE_ID

  def _add_keyword_plan(self, customer_id, keywords, country_list, language_code):
    """Adds a keyword plan, campaign, ad group, etc. to the customer account.
    Args:
      customer_id: A str of the customer_id to use in requests.
    Raises:
      GoogleAdsException: If an error is returned from the API.
    """
    keyword_plan = self._create_keyword_plan(customer_id)
    keyword_plan_campaign = self._create_keyword_plan_campaign(
      customer_id, keyword_plan, country_list, language_code
    )
    # keyword_plan_campaign = self._create_keyword_plan_campaign(
    #   customer_id, keyword_plan, country_list, language_code
    # )
    keyword_plan_ad_group = self._create_keyword_plan_ad_group(
      customer_id, keyword_plan_campaign
    )
    self._create_keyword_plan_ad_group_keywords(
      customer_id, keyword_plan_ad_group, keywords
    )
    return keyword_plan.split('/')[-1]

  def _create_keyword_plan(self, customer_id):
    """Adds a keyword plan to the given customer account.
    Args:
      customer_id: A str of the customer_id to use in requests.
    Returns:
      A str of the resource_name for the newly created keyword plan.
    Raises:
      GoogleAdsException: If an error is returned from the API.
    """
    keyword_plan_service = self.client.get_service("KeywordPlanService")
    operation = self.client.get_type("KeywordPlanOperation")
    keyword_plan = operation.create

    keyword_plan.name = f"Keyword plan for traffic estimate {uuid.uuid4()}"

    forecast_interval = (
      self.client.enums.KeywordPlanForecastIntervalEnum.NEXT_MONTH
    )
    keyword_plan.forecast_period.date_interval = forecast_interval

    response = keyword_plan_service.mutate_keyword_plans(
      customer_id=customer_id, operations=[operation]
    )
    resource_name = response.results[0].resource_name
    # print(f"Created keyword plan with resource name: {resource_name}")
    return resource_name

  def _create_keyword_plan_campaign(self, customer_id, keyword_plan, country_list, language_code):
    """Adds a keyword plan campaign to the given keyword plan.

    Args:
        client: An initialized instance of GoogleAdsClient
        customer_id: A str of the customer_id to use in requests.
        keyword_plan: A str of the keyword plan resource_name this keyword plan
            campaign should be attributed to.create_keyword_plan.

    Returns:
        A str of the resource_name for the newly created keyword plan campaign.

    Raises:
        GoogleAdsException: If an error is returned from the API.
    """
    keyword_plan_campaign_service = self.client.get_service(
      "KeywordPlanCampaignService"
    )
    operation = self.client.get_type("KeywordPlanCampaignOperation")
    keyword_plan_campaign = operation.create

    keyword_plan_campaign.name = f"Keyword plan campaign {uuid.uuid4()}"
    keyword_plan_campaign.cpc_bid_micros = _CPC_BID_MICROS
    keyword_plan_campaign.keyword_plan = keyword_plan

    network = self.client.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH
    keyword_plan_campaign.keyword_plan_network = network

    location_ids = self._convert_location_ids(country_list)
    location_rns = self._map_locations_ids_to_resource_names(location_ids)
    language_id = self._convert_language_id(language_code)
    language_rn = self.client.get_service("GoogleAdsService").language_constant_path(language_id)

    geo_target = self.client.get_type("KeywordPlanGeoTarget")
    geo_target.geo_target_constant = location_rns[0]
    keyword_plan_campaign.geo_targets.append(geo_target)
    language = language_rn
    keyword_plan_campaign.language_constants.append(language)

    response = keyword_plan_campaign_service.mutate_keyword_plan_campaigns(
      customer_id=customer_id, operations=[operation]
    )
    resource_name = response.results[0].resource_name
    print(f"Created keyword plan campaign with resource name: {resource_name}")
    return resource_name

  def _create_keyword_plan_ad_group(self, customer_id, keyword_plan_campaign):
    """Adds a keyword plan ad group to the given keyword plan campaign.
    Args:
      customer_id: A str of the customer_id to use in requests.
      keyword_plan_campaign: A str of the keyword plan campaign resource_name
        this keyword plan ad group should be attributed to.
    Returns:
      A str of the resource_name for the newly created keyword plan ad group.
    Raises:
      GoogleAdsException: If an error is returned from the API.
    """
    operation = self.client.get_type("KeywordPlanAdGroupOperation")
    keyword_plan_ad_group = operation.create

    keyword_plan_ad_group.name = f"Keyword plan ad group {uuid.uuid4()}"
    keyword_plan_ad_group.cpc_bid_micros = _CPC_BID_MICROS
    keyword_plan_ad_group.keyword_plan_campaign = keyword_plan_campaign

    keyword_plan_ad_group_service = self.client.get_service(
      "KeywordPlanAdGroupService"
    )
    response = keyword_plan_ad_group_service.mutate_keyword_plan_ad_groups(
      customer_id=customer_id, operations=[operation]
    )
    resource_name = response.results[0].resource_name
    # print(f"Created keyword plan ad group with resource name: {resource_name}")
    return resource_name

  def _create_keyword_plan_ad_group_keywords(self, customer_id, plan_ad_group, keywords):
    """Adds keyword plan ad group keywords to the given keyword plan ad group.
    Args:
      customer_id: A str of the customer_id to use in requests.
      plan_ad_group: A str of the keyword plan ad group resource_name
        these keyword plan keywords should be attributed to.
    Raises:
      GoogleAdsException: If an error is returned from the API.
    """
    keyword_plan_ad_group_keyword_service = self.client.get_service(
      "KeywordPlanAdGroupKeywordService"
    )
    operation = self.client.get_type("KeywordPlanAdGroupKeywordOperation")
    operations = []

    for keyword in keywords:

      operation = self.client.get_type("KeywordPlanAdGroupKeywordOperation")
      keyword_plan_ad_group_keyword = operation.create
      keyword_plan_ad_group_keyword.text = keyword
      keyword_plan_ad_group_keyword.cpc_bid_micros = _CPC_BID_MICROS
      keyword_plan_ad_group_keyword.match_type = (
        self.client.enums.KeywordMatchTypeEnum.BROAD
      )
      keyword_plan_ad_group_keyword.keyword_plan_ad_group = plan_ad_group
      operations.append(operation)

    response = keyword_plan_ad_group_keyword_service.mutate_keyword_plan_ad_group_keywords(
      customer_id=customer_id, operations=operations
    )

  def estimate(self, customer_id, keywords, country_list, language_code):

    keyword_plan_id = self._add_keyword_plan('123456789', keywords, country_list, language_code)
    keyword_plan_service = self.client.get_service("KeywordPlanService")
    resource_name = keyword_plan_service.keyword_plan_path(
    customer_id, keyword_plan_id
    )

    response = keyword_plan_service.generate_forecast_metrics(
      keyword_plan=resource_name
    )

    res = []
    for i, forecast in enumerate(response.keyword_forecasts):
      # print(f"#{i+1} Keyword ID: {forecast.keyword_plan_ad_group_keyword}")
      metrics = forecast.keyword_forecast
      res.append({
        "keyword": keywords[i],
        "clicks": round(metrics.clicks),
        "impressions": round(metrics.impressions),
        "cpc": round(metrics.average_cpc/1000000,2),
        "ctr": round(metrics.ctr,4),
        "cost": round(metrics.cost_micros/1000000,2)
        })
    return res