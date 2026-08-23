import urllib.request
import re

urls = ['https://bennyduah.com', 'https://kaluna.bennyduah.com', 'https://anchor.bennyduah.com']
for url in urls:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        html = urllib.request.urlopen(req).read().decode('utf-8')
        classes = re.findall(r'class="([^"]+)"', html)
        print(f'\n--- {url} ---')
        classes.sort(key=len, reverse=True)
        for c in classes[:10]:
            print(c)
    except Exception as e:
        print(f'Error on {url}: {e}')
