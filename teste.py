# VERSION: 1.6
# AUTHORS: AhkTex 
# NAME: StarckFilmesV3

import sys
import re
import time
from datetime import date
from pathlib import Path
from urllib import request, parse
from novaprinter import prettyPrinter
from bs4 import BeautifulSoup

# ====================== PASTAS E CACHE ======================
home = str(Path.home())
system_paths = {
    'win32': f"{home}/AppData/Roaming",
    'linux': f"{home}/.local/share",
    'darwin': f"{home}/Library/Application Support",
}
cache_dir = Path(f"{system_paths[sys.platform]}/qbit_plugins_data")
cache_path = cache_dir / "starckfilmes_cache.html"

# ====================== CLASSE PRINCIPAL ======================
class starckfilmes(object):
    url = 'https://www.starckfilmes-v3.com'
    name = 'StarckFilmesV3'
    supported_categories = {'all': '0', 'movies': 'filme', 'tv': 'série'}

    def __init__(self):
        self.opener = request.build_opener()
        self.opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')]

    # ==================== CACHE (atualiza 1x por dia) ====================
    def _update_cache(self):
        if not cache_dir.exists():
            cache_dir.mkdir(parents=True, exist_ok=True)

        today = str(date.today())
        if cache_path.exists():
            with open(cache_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                if first_line == today:
                    return  # já atualizado hoje

        # Baixa APENAS as 2 primeiras páginas
        with open(cache_path, 'w', encoding='utf-8') as f:
            f.write(f"{today}\n")
            for page in range(1, 3):  # SÓ 2 PÁGINAS
                try:
                    search_url = f"{self.url}/page/{page}/"
                    req = self.opener.open(search_url, timeout=15)
                    html = req.read().decode('utf-8', errors='ignore')
                    f.write(html + "\n<!-- PAGE BREAK -->\n")
                    time.sleep(0.7)
                except:
                    break

    def _load_cache(self):
        if not cache_path.exists():
            self._update_cache()
        with open(cache_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()[1:]  # pula a data
            return "".join(lines)

    # ==================== BUSCA PRINCIPAL (só 2 páginas) ====================
    def search(self, what, cat='all'):
        # Atualiza cache se necessário
        self._update_cache()

        # Carrega as 2 páginas do cache
        html = self._load_cache()
        soup = BeautifulSoup(html, 'html.parser')

        # Filtra pelo termo buscado
        search_terms = [term.lower() for term in str(what).split("%20")]

        items = soup.find_all('div', class_='item')
        for item in items:
            try:
                link_tag = item.find('a', href=True)
                if not link_tag:
                    continue
                desc_link = link_tag['href']
                if not desc_link.startswith('http'):
                    desc_link = self.url + desc_link

                # Título, ano e áudio
                title_tag = item.find('a', class_='title')
                title = title_tag.get_text(strip=True) if title_tag else "Unknown"

                footer = item.find_all('span')
                year = footer[0].get_text(strip=True) if len(footer) > 0 else ""
                audio = footer[1].get_text(strip=True) if len(footer) > 1 else ""

                full_title = f"{title} ({year}) [{audio}]".strip().lower()

                # Filtra pelo termo
                if not any(term in full_title for term in search_terms):
                    continue

                # Pega todos os magnets da página
                magnets = self._get_magnets_from_page(desc_link)
                if not magnets:
                    continue

                for magnet, quality in magnets:
                    size_match = re.search(r'([\d\.]+ ?[GM]B)', quality)
                    size_str = size_match.group(1) if size_match else "-1"

                    data = {
                        'link': magnet,
                        'name': f"{title} ({year}) [{audio}] {quality}",
                        'size': size_str.replace(' GB', '000000000').replace(' MB', '000000').replace('.', ''),
                        'seeds': -1,
                        'leech': -1,
                        'engine_url': self.url,
                        'desc_link': desc_link
                    }
                    prettyPrinter(data)
            except:
                continue

    # ==================== PEGA MAGNETS DA PÁGINA ====================
    def _get_magnets_from_page(self, url):
        try:
            req = self.opener.open(url, timeout=15)
            soup = BeautifulSoup(req.read().decode('utf-8', errors='ignore'), 'html.parser')
            magnets = []
            for btn in soup.find_all('span', class_='btn-down'):
                a = btn.find('a', href=re.compile(r'^magnet:'))
                if a and a.get('href'):
                    magnet = a['href']
                    text_span = btn.find('span', class_='text')
                    if text_span:
                        lines = [t.get_text(strip=True) for t in text_span.find_all('span')]
                        quality = " | ".join(lines[-2:])  # ex: "1080p (2.80 GB)"
                    else:
                        quality = "Magnet"
                    magnets.append((magnet, quality))
            return magnets
        except:
            return []

# ==================== FIM ====================
