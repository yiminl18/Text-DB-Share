from civic_scraper.base.cache import Cache
from civic_scraper.platforms import CivicPlusSite

url1 = 'https://www.documentcloud.org/app?q=%2Borganization%3Aagenda-watch-11341%20'
url2 = "https://www.documentcloud.org/app?q=%2Buser%3Aserdar-tumgoren-20993%20%2Baccess%3Apublic%20"


# Change output dir to /tmp
output = '/Users/yiminglin/Documents/research/Text management system/data/stanford'
site = CivicPlusSite(url1, cache=Cache(output))
assets_metadata = site.scrape(download=True)
assets_metadata.to_csv('/Users/yiminglin/Documents/research/Text management system/data/stanford/civic-scraper/metadata')
for asset in assets_metadata:
    asset.download(output+'/civic-scraper/assets')