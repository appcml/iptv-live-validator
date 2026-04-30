#!/usr/bin/env python3
"""
Scraper proactivo - Busca nuevos canales y radios en la web
Agrega a los existentes sin borrar
"""

import requests
import re
import json
import time

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
}

# FUENTES PÚBLICAS DE IPTV - Se pueden agregar más
IPTV_SOURCES = [
    "https://iptv-org.github.io/iptv/index.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/cl.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/us.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/es.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/mx.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/ar.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/br.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/co.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/pe.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/radio.m3u",
]

# FUENTES DE RADIOS ONLINE
RADIO_SOURCES = [
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/radio.m3u",
    "http://radio.garden/api/ara/content/places",
]

MAX_PER_SOURCE = 100  # Más canales por fuente

def fetch_m3u(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code == 200:
            return r.text
    except Exception as e:
        print(f"   ❌ Error: {str(e)[:50]}")
    return None

def parse_m3u(content, default_country="XX", source_name="unknown"):
    if not content:
        return []
    
    channels = []
    lines = content.strip().split('\n')
    current = None
    
    for line in lines:
        line = line.strip()
        
        if line.startswith('#EXTINF:'):
            name_match = re.search(r',([^,]+)$', line)
            name = name_match.group(1).strip() if name_match else "Canal"
            
            logo_match = re.search(r'tvg-logo="([^"]*)"', line)
            logo = logo_match.group(1) if logo_match else ""
            
            group_match = re.search(r'group-title="([^"]*)"', line)
            group = group_match.group(1) if group_match else "General"
            
            country_match = re.search(r'tvg-country="([^"]*)"', line)
            country = country_match.group(1) if country_match else default_country
            
            current = {
                "name": name.replace('"', '').strip(),
                "url": "",
                "logo": logo,
                "group": group,
                "country": country,
                "source": source_name
            }
            
        elif line.startswith('http') and current:
            current["url"] = line
            channels.append(current)
            current = None
            
            if len(channels) >= MAX_PER_SOURCE:
                break
    
    return channels

def load_existing():
    """Carga canales existentes"""
    try:
        with open('data/tv_channels_raw.json', 'r', encoding='utf-8') as f:
            tv = json.load(f)
    except:
        tv = []
    
    try:
        with open('data/radio_channels_raw.json', 'r', encoding='utf-8') as f:
            radio = json.load(f)
    except:
        radio = []
    
    return tv, radio

def save_channels(tv, radio):
    """Guarda canales"""
    with open('data/tv_channels_raw.json', 'w', encoding='utf-8') as f:
        json.dump(tv, f, ensure_ascii=False, indent=2)
    
    with open('data/radio_channels_raw.json', 'w', encoding='utf-8') as f:
        json.dump(radio, f, ensure_ascii=False, indent=2)

def merge_channels(existing, new_channels):
    """Merge sin duplicados, preservando existentes"""
    seen = {ch["url"] for ch in existing}
    added = 0
    
    for ch in new_channels:
        if ch["url"] not in seen:
            seen.add(ch["url"])
            existing.append(ch)
            added += 1
    
    return existing, added

def scrape_all():
    """Scrapea todas las fuentes y mergea"""
    print("="*60)
    print("🔍 BUSCANDO NUEVOS CANALES Y RADIOS EN LA WEB")
    print("="*60)
    
    existing_tv, existing_radio = load_existing()
    print(f"📦 Existentes: {len(existing_tv)} TV + {len(existing_radio)} Radio")
    
    new_tv = []
    new_radio = []
    
    # Scrapear fuentes TV
    print(f"\n📺 Scrapeando {len(IPTV_SOURCES)} fuentes TV...")
    for i, source in enumerate(IPTV_SOURCES, 1):
        print(f"\n[{i}/{len(IPTV_SOURCES)}] {source[:70]}")
        content = fetch_m3u(source)
        if content:
            channels = parse_m3u(content, source_name=source.split('/')[-1])
            print(f"   ✓ {len(channels)} canales encontrados")
            
            # Separar TV y Radio por heurística
            for ch in channels:
                name_lower = ch["name"].lower()
                group_lower = ch["group"].lower()
                if any(x in name_lower or x in group_lower for x in ['radio', 'fm', 'am ', 'estacion', 'hlsradio']):
                    new_radio.append(ch)
                else:
                    new_tv.append(ch)
        else:
            print(f"   ❌ No se pudo descargar")
        time.sleep(1)  # Respetar servidores
    
    print(f"\n📊 Nuevos encontrados: {len(new_tv)} TV + {len(new_radio)} Radio")
    
    # Mergear
    merged_tv, added_tv = merge_channels(existing_tv, new_tv)
    merged_radio, added_radio = merge_channels(existing_radio, new_radio)
    
    print(f"\n🆕 Agregados: {added_tv} TV + {added_radio} Radio")
    print(f"📦 Total ahora: {len(merged_tv)} TV + {len(merged_radio)} Radio")
    
    # Guardar
    save_channels(merged_tv, merged_radio)
    
    # Guardar log de scraping
    log = {
        "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "sources_checked": len(IPTV_SOURCES),
        "new_tv_found": len(new_tv),
        "new_radio_found": len(new_radio),
        "added_tv": added_tv,
        "added_radio": added_radio,
        "total_tv": len(merged_tv),
        "total_radio": len(merged_radio)
    }
    
    with open('data/scrape_log.json', 'w', encoding='utf-8') as f:
        json.dump(log, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Scraping completado")
    print(f"📋 Log guardado en data/scrape_log.json")

if __name__ == "__main__":
    scrape_all()
