import pandas as pd
import os
import argparse
import sys
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from google.ads.googleads import util

_DEFAULT_LOCATION_IDS = ["1023191"]  # location ID for New York, NY
_DEFAULT_LANGUAGE_ID = "1000"  # language ID for English

class MiningModule:
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

  def get_client(self):
    return self.client

  def get_resources(self):
    customer_service = self.client.get_service("CustomerService")

    accessible_customers = customer_service.list_accessible_customers()
    result_total = len(accessible_customers.resource_names)
    print(f"Total results: {result_total}")

    resource_names = accessible_customers.resource_names
    for resource_name in resource_names:
      print(f'Customer resource name: "{resource_name}"')

  def get_keywords(self, customer_id, campaign_id = None, ad_group_id = None, page_size = 1000):
    service = self.client.get_service("GoogleAdsService")

    query = """
      SELECT
        ad_group.id,
        ad_group_criterion.type,
        ad_group_criterion.criterion_id,
        ad_group_criterion.keyword.text,
        ad_group_criterion.keyword.match_type
      FROM ad_group_criterion
      WHERE ad_group_criterion.type = KEYWORD"""

    if campaign_id:
      query += f" AND campaign.id = {campaign_id}"
    if ad_group_id:
      query += f" AND ad_group.id = {ad_group_id}"

    search_request = self.client.get_type("SearchGoogleAdsRequest")
    search_request.customer_id = customer_id
    search_request.query = query
    search_request.page_size = page_size

    results = service.search(request=search_request)

    for row in results:
      ad_group = row.ad_group
      ad_group_criterion = row.ad_group_criterion
      keyword = row.ad_group_criterion.keyword

      print(
        f'Keyword with text "{keyword.text}", match type '
        f"{keyword.match_type}, criteria type "
        f"{ad_group_criterion.type_}, and ID "
        f"{ad_group_criterion.criterion_id} was found in ad group "
        f"with ID {ad_group.id}."
      )

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

  def get_new_keywords(self, customer_id, location_ids, language_id, keyword_texts = None, page_url = None):
    keyword_plan_idea_service = self.client.get_service("KeywordPlanIdeaService")
    keyword_competition_level_enum = (
        self.client.enums.KeywordPlanCompetitionLevelEnum
    )
    keyword_plan_network = (
        self.client.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH_AND_PARTNERS
    )

    location_ids = self._convert_location_ids(location_ids)
    location_rns = self._map_locations_ids_to_resource_names(location_ids)
    language_id = self._convert_language_id(language_id)
    language_rn = self.client.get_service("GoogleAdsService").language_constant_path(language_id)
    print(location_rns)
    print(language_rn)

    # Either keywords or a page_url are required to generate keyword ideas
    # so this raises an error if neither are provided.
    if not (keyword_texts or page_url):
        raise ValueError(
            "At least one of keywords or page URL is required, "
            "but neither was specified."
        )

    # Only one of the fields "url_seed", "keyword_seed", or
    # "keyword_and_url_seed" can be set on the request, depending on whether
    # keywords, a page_url or both were passed to this function.
    request = self.client.get_type("GenerateKeywordIdeasRequest")
    request.customer_id = customer_id
    request.language = language_rn
    request.geo_target_constants.extend(location_rns)
    request.include_adult_keywords = False
    request.keyword_plan_network = keyword_plan_network

    # To generate keyword ideas with only a page_url and no keywords we need
    # to initialize a UrlSeed object with the page_url as the "url" field.
    if not keyword_texts and page_url:
        request.url_seed.url = page_url

    # To generate keyword ideas with only a list of keywords and no page_url
    # we need to initialize a KeywordSeed object and set the "keywords" field
    # to be a list of StringValue objects.
    if keyword_texts and not page_url:
        request.keyword_seed.keywords.extend(keyword_texts)

    # To generate keyword ideas using both a list of keywords and a page_url we
    # need to initialize a KeywordAndUrlSeed object, setting both the "url" and
    # "keywords" fields.
    if keyword_texts and page_url:
        request.keyword_and_url_seed.url = page_url
        request.keyword_and_url_seed.keywords.extend(keyword_texts)

    keyword_ideas = keyword_plan_idea_service.generate_keyword_ideas(
        request=request
    )
    res = []
    for idea in keyword_ideas:
      # print(idea)
      res.append({
        'keyword':idea.text,
        'monthly_search':idea.keyword_idea_metrics.avg_monthly_searches,
        'competition_index':idea.keyword_idea_metrics.competition_index,
        'low_top_of_page_bid':round(idea.keyword_idea_metrics.low_top_of_page_bid_micros/1000000,2),
        'high_top_of_page_bid':round(idea.keyword_idea_metrics.high_top_of_page_bid_micros/1000000,2),
        })
    return res
