# VERSION: 1.9
# AUTHORS: AhkTex + Grok
# NAME: StarckFilmesV3

import re
import time
from urllib import request, parse
from novaprinter import prettyPrinter
from bs4 import BeautifulSoup

class starckfilmes(object):
    url = 'https://www.starckfilmes-v3.com'
    name = 'StarckFilmesV3'
    supported_categories = {'all': '0', 'movies': 'filme', 'tv': 'série'}

    def __init__(self):
        self.opener = request.build_opener()
        self.opener.addheaders = [
            ('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        ]

    def search(self, what, cat='all'):
        what = parse.quote_plus(what)
        search_terms = [t.lower() for t in what.replace('+', ' ').split()]

        for page in range(1, 3):  # SÓ 2 PÁGINAS
            try:
                if cat in self.supported_categories and self.supported_categories[cat] != '0':
                    search_url = f"{self.url}/?s={what}&type={self.supported_categories[cat]}&page={page}"
                else:
                    search_url = f"{self.url}/?s={what}&page={page}"

                req = self.opener.open(search_url, timeout=20)
                soup = BeautifulSoup(req.read().decode('utf-8', errors='ignore'), 'html.parser')
            except Exception as e:
                break

            for item in soup.find_all('div', class_='item'):
                try:
                    a = item.find('a', href=True)
                    if not a: continue
                    link = a['href'] if a['href'].startswith('http') else self.url + a['href']

                    title_tag = item.find('a', class_='title')
                    title = title_tag.get_text(strip=True) if title_tag else "Unknown"

                    spans = item.find_all('span')
                    year = spans[0].get_text(strip=True) if len(spans) > 0 else ""
                    audio = spans[1].get_text(strip=True) if len(spans) > 1 else ""

                    full = f"{title} {year} {audio}".lower()
                    if not any(term in full for term in search_terms):
                        continue

                    magnets = self._get_magnets(link)
                    for magnet, qual in magnets:
                        size_match = re.search(r'([\d\.]+ ?[GM]B)', qual)
                        size_str = size_match.group(1) if size_match else "0 MB"

                        data = {
                            'link': magnet,
                            'name': f"{title} ({year}) [{audio}] {qual}",
                            'size': size_str.replace(' GB','000000000').replace(' MB','000000').replace('.',''),
                            'seeds': -1,
                            'leech': -1,
                            'engine_url': self.url,
                            'desc_link': link
                        }
                        prettyPrinter(data)
                except:
                    continue
            time.sleep(1.5
