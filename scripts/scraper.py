#!/usr/bin/env python3
"""
Scraper de fuentes M3U públicas
Descarga listas externas y extrae canales
"""

import requests
import re
import json
from urllib.parse import urljoin

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def fetch_m3u(url):
    """Descarga contenido M3U"""
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code == 200:
            return r.text
    except Exception as e:
        print(f"❌ Error descargando {url}: {e}")
    return None

def parse_m3u(content, default_country="XX"):
    """Parsea contenido M3U a lista de canales"""
    if not content:
        return []
    
    channels = []
    lines = content.strip().split('\n')
    current = None
    
    for line in lines:
        line = line.strip()
        
        if line.startswith('#EXTINF:'):
            # Extraer atributos con regex
            name_match = re.search(r',([^,]+)$', line)
            name = name_match.group(1).strip() if name_match else "Canal Desconocido"
            
            logo_match = re.search(r'tvg-logo="([^"]*)"', line)
            logo = logo_match.group(1) if logo_match else ""
            
            group_match = re.search(r'group-title="([^"]*)"', line)
            group = group_match.group(1) if group_match else "General"
            
            country_match = re.search(r'tvg-country="([^"]*)"', line) or re.search(r'country="([^"]*)"', line)
            country = country_match.group(1) if country_match else default_country
            
            current = {
                "name": name,
                "url": "",
                "logo": logo,
                "group": group,
                "country": country,
                "source": "scraped"
            }
            
        elif line.startswith('http') and current:
            current["url"] = line
            # Limpiar nombre si tiene comillas o caracteres raros
            current["name"] = current["name"].replace('"', '').strip()
            channels.append(current)
            current = None
    
    return channels

def scrape_all_sources():
    """Scrapea todas las fuentes configuradas"""
    with open('data/sources.json', 'r', encoding='utf-8') as f:
        sources = json.load(f)
    
    all_tv = []
    all_radio = []
    
    # Scrapear fuentes TV
    print("📺 Scrapeando fuentes TV...")
    for source_url in sources.get("tv_sources", []):
        print(f"   → {source_url}")
        content = fetch_m3u(source_url)
        if content:
            channels = parse_m3u(content)
            print(f"   ✓ {len(channels)} canales encontrados")
            all_tv.extend(channels)
    
    # Scrapear fuentes Radio
    print("📻 Scrapeando fuentes Radio...")
    for source_url in sources.get("radio_sources", []):
        print(f"   → {source_url}")
        content = fetch_m3u(source_url)
        if content:
            channels = parse_m3u(content)
            print(f"   ✓ {len(channels)} radios encontradas")
            all_radio.extend(channels)
    
    # Agregar estáticos
    all_tv.extend([{**ch, "source": "static"} for ch in sources.get("static_tv", [])])
    all_radio.extend([{**ch, "source": "static"} for ch in sources.get("static_radio", [])])
    
    # Eliminar duplicados por URL
    seen_urls = set()
    unique_tv = []
    unique_radio = []
    
    for ch in all_tv:
        if ch["url"] not in seen_urls:
            seen_urls.add(ch["url"])
            unique_tv.append(ch)
    
    for ch in all_radio:
        if ch["url"] not in seen_urls:
            seen_urls.add(ch["url"])
            unique_radio.append(ch)
    
    print(f"\n📊 Total únicos: {len(unique_tv)} TV + {len(unique_radio)} Radio")
    
    return unique_tv, unique_radio

if __name__ == "__main__":
    tv, radio = scrape_all_sources()
    
    # Guardar resultados crudos
    with open('data/tv_channels_raw.json', 'w', encoding='utf-8') as f:
        json.dump(tv, f, ensure_ascii=False, indent=2)
    
    with open('data/radio_channels_raw.json', 'w', encoding='utf-8') as f:
        json.dump(radio, f, ensure_ascii=False, indent=2)
    
    print("✅ Scraping completado. Archivos guardados en data/")
