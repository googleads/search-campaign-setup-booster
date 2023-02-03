import requests
import re
import sys
import os
from bs4 import BeautifulSoup
from collections import Counter

class CollectionModule():
  def __init__(self):
    return

  def get_soup(self, url, headers):
    html = requests.get(url, headers = headers)
    soup = BeautifulSoup(html.text, 'html.parser')
    return soup

  def get_collections(self, soup):
    collections = dict()
    urls = []
    data = soup.select('a')
    pattern = re.compile(r'^\/collections\/([^\/]+)$', re.I)
    filter_pattern = re.compile(r'.*(new|best|sale| or| and| all|price|off|2022|order).*', re.I)
    for d in data:
      try:
        href = d['href']
        if pattern.match(href) and not filter_pattern.match(href):
          if href not in collections.keys():
            # print(d.text)
            if len(d.text.strip()) > 3:
              collections[href] = d.text.strip()
            else:
              collections[href] = href.split('/')[2].replace('-',' ')
          urls.append(href)
      except:
        continue
    res = dict()
    for k, v in dict(Counter(urls).most_common(10)).items():
      res[k] = collections[k]
    return res
  
  def get_categories(self, soup):
    categories = dict()
    res = dict()
    data = soup.select('a')
    urls = []
    pattern = re.compile(r'^(https://[^\/]+)*(\/pc\/.+)$', re.I)
    filter_pattern = re.compile(r'.*(new|best|sale| or| and| all|price|off|2022|all-products).*', re.I)
    for d in data:
      try:
        href = d['href']
        # print(href)
        if pattern.match(href) and not filter_pattern.match(href):
          url = re.findall(pattern, href)[0][-1]
          if url not in categories.keys():
            # print(url)
            # print(d.text)
            if len(d.span.text.strip()) > 3:
              categories[url] = d.span.text.strip()
            else:
              categories[url] = url.split('/')[2].replace('-',' ')
          urls.append(url)
      except:
        continue
    for k, v in dict(Counter(urls).most_common(10)).items():
      res[k] = categories[k]
    return res

  def format_data(self, data, format='dict'):
    if format == 'dict':
      res = []
      for k, v in data.items():
        res.append({
          'category':v.strip(),
          'url':k
          })
    else:
      res = ""
      for k, v in data.items():
        res += f"{v.strip()}:{k}\n"
      res = res.strip()
    return res

  def extract(self,  url, format='dict'):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.119 Safari/537.36'}
    try:
      soup = self.get_soup(url, headers)
      collections = self.get_collections(soup)
      res = self.format_data(collections, format)
    except:
      res = None
    if not res or len(res) == 0:
      #not shopify, try business page
      print('business.page')
      try:
        soup = self.get_soup(os.path.join(url, 'pc/All-Products/all_products'), headers)
        categories = self.get_categories(soup)
        res = self.format_data(categories, format)
      except:
        res = None
    return res

if __name__ == "__main__":
  # url = sys.argv[1]
  # url = "https://www.wolddress.com/"
  # url = "https://www.aleadergear.com/"
  # url = "https://wutaleather.com/"
  # url = "https://www.bellabarnett.com/"
  # url = "https://www.cnhogroup.com/"
  # url = "https://scomera.business.page/"
  # url = "https://smartdepi.untlaser.cn/"
  # url = "https://www.yongnasocks.com/"
  url = "https://szkchk.business.page/"
  # url = "https://www.xikaiele.com/"
  cu = CollectionModule()
  # for item in cu.extract(url):
  #   print(item['category'],item['url'])
  res = cu.extract(url, "sheet")
  print(res)