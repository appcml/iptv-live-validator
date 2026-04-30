#!/usr/bin/env python3
"""
Importador desde CIC-TV - SOLO para carga inicial
No se ejecuta en auto-update
"""

import requests
import json
import re

CIC_TV_REPO = "https://raw.githubusercontent.com/appcml/CIC-TV/main"

def fetch_m3u(url):
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            return r.text
    except:
        pass
    return None

def parse_m3u(content):
    if not content:
        return []
    
    channels = []
    lines = content.strip().split('\n')
    current = None
    
    for line in lines:
        line = line.strip()
        
        if line.startswith('#EXTINF:'):
            name = "Canal"
            if ',' in line:
                name = line.split(',')[-1].strip()
            
            logo_match = re.search(r'tvg-logo="([^"]*)"', line)
            logo = logo_match.group(1) if logo_match else ""
            
            group_match = re.search(r'group-title="([^"]*)"', line)
            group = group_match.group(1) if group_match else "CIC-TV"
            
            current = {
                "name": name.replace('"', '').strip(),
                "url": "",
                "logo": logo,
                "group": group,
                "country": "CL",
                "source": "cic-tv"
            }
            
        elif line.startswith('http') and current:
            current["url"] = line
            channels.append(current)
            current = None
    
    return channels

def import_cic_tv():
    print("="*60)
    print("📥 IMPORTANDO DESDE CIC-TV (carga inicial)")
    print("="*60)
    
    # Buscar playlist.m3u
    url = f"{CIC_TV_REPO}/playlist.m3u"
    print(f"🔍 {url}")
    
    content = fetch_m3u(url)
    if not content:
        print("❌ No se encontró playlist.m3u en CIC-TV")
        return
    
    channels = parse_m3u(content)
    print(f"✅ {len(channels)} canales importados")
    
    # Separar TV y Radio
    tv = []
    radio = []
    
    for ch in channels:
        name_lower = ch["name"].lower()
        group_lower = ch["group"].lower()
        
        if any(x in name_lower or x in group_lower for x in ['radio', 'fm', 'am ', 'estacion']):
            radio.append(ch)
        else:
            tv.append(ch)
    
    print(f"📺 TV: {len(tv)}")
    print(f"📻 Radio: {len(radio)}")
    
    # Merge con existentes (si hay)
    try:
        with open('data/tv_channels_raw.json', 'r', encoding='utf-8') as f:
            existing_tv = json.load(f)
    except:
        existing_tv = []
    
    try:
        with open('data/radio_channels_raw.json', 'r', encoding='utf-8') as f:
            existing_radio = json.load(f)
    except:
        existing_radio = []
    
    seen = {ch["url"] for ch in existing_tv + existing_radio}
    
    added_tv = 0
    for ch in tv:
        if ch["url"] not in seen:
            existing_tv.append(ch)
            seen.add(ch["url"])
            added_tv += 1
    
    added_radio = 0
    for ch in radio:
        if ch["url"] not in seen:
            existing_radio.append(ch)
            seen.add(ch["url"])
            added_radio += 1
    
    # Guardar
    with open('data/tv_channels_raw.json', 'w', encoding='utf-8') as f:
        json.dump(existing_tv, f, ensure_ascii=False, indent=2)
    
    with open('data/radio_channels_raw.json', 'w', encoding='utf-8') as f:
        json.dump(existing_radio, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Importación completada")
    print(f"🆕 Nuevos: {added_tv} TV + {added_radio} Radio")
    print(f"📦 Total: {len(existing_tv)} TV + {len(existing_radio)} Radio")

if __name__ == "__main__":
    import_cic_tv()
