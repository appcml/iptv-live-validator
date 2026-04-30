#!/usr/bin/env python3
"""
Importador manual desde CIC-TV
Lee canales del otro repositorio y los agrega para validacion
"""

import requests
import json
import sys

# URL del repo CIC-TV (raw github)
CIC_TV_REPO = "https://raw.githubusercontent.com/appcml/CIC-TV/main"

def fetch_json(url):
    """Descarga JSON desde URL"""
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"❌ Error descargando {url}: {e}")
    return None

def fetch_m3u(url):
    """Descarga M3U desde URL"""
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            return r.text
    except Exception as e:
        print(f"❌ Error descargando {url}: {e}")
    return None

def parse_m3u_to_channels(content, default_group="CIC-TV"):
    """Convierte M3U a lista de canales"""
    if not content:
        return []
    
    channels = []
    lines = content.strip().split('\n')
    current = None
    
    for line in lines:
        line = line.strip()
        
        if line.startswith('#EXTINF:'):
            # Extraer nombre despues de la coma
            name = "Canal"
            if ',' in line:
                name = line.split(',')[-1].strip()
            
            # Extraer atributos
            import re
            logo_match = re.search(r'tvg-logo="([^"]*)"', line)
            logo = logo_match.group(1) if logo_match else ""
            
            group_match = re.search(r'group-title="([^"]*)"', line)
            group = group_match.group(1) if group_match else default_group
            
            current = {
                "name": name,
                "url": "",
                "logo": logo,
                "group": group,
                "country": "CL",
                "source": "cic-tv-import"
            }
            
        elif line.startswith('http') and current:
            current["url"] = line
            channels.append(current)
            current = None
    
    return channels

def import_from_cic_tv():
    """Importa canales desde CIC-TV"""
    print("="*60)
    print("IMPORTANDO CANALES DESDE CIC-TV")
    print("="*60)
    
    all_channels = []
    
    # Opcion 1: Intentar leer JSON si existe en CIC-TV
    json_urls = [
        f"{CIC_TV_REPO}/channels.json",
        f"{CIC_TV_REPO}/data/channels.json",
        f"{CIC_TV_REPO}/api/channels.json"
    ]
    
    for url in json_urls:
        print(f"\n🔍 Buscando JSON: {url}")
        data = fetch_json(url)
        if data:
            print(f"✅ JSON encontrado!")
            if isinstance(data, list):
                channels = data
            elif isinstance(data, dict) and 'channels' in data:
                channels = data['channels']
            else:
                channels = []
            
            for ch in channels:
                if 'url' in ch:
                    all_channels.append({
                        "name": ch.get("name", "Canal"),
                        "url": ch["url"],
                        "logo": ch.get("logo", ""),
                        "group": ch.get("group", "CIC-TV"),
                        "country": ch.get("country", "CL"),
                        "source": "cic-tv-json"
                    })
            print(f"📊 {len(all_channels)} canales desde JSON")
            break
    
    # Opcion 2: Intentar leer M3U si existe en CIC-TV
    m3u_urls = [
        f"{CIC_TV_REPO}/lista.m3u",
        f"{CIC_TV_REPO}/channels.m3u",
        f"{CIC_TV_REPO}/playlist.m3u",
        f"{CIC_TV_REPO}/tv.m3u"
    ]
    
    for url in m3u_urls:
        print(f"\n🔍 Buscando M3U: {url}")
        content = fetch_m3u(url)
        if content:
            print(f"✅ M3U encontrado!")
            channels = parse_m3u_to_channels(content)
            all_channels.extend(channels)
            print(f"📊 {len(channels)} canales desde M3U")
            break
    
    # Opcion 3: Buscar cualquier archivo .m3u en el repo (listando)
    print(f"\n🔍 Buscando archivos en CIC-TV...")
    try:
        # Intentar leer el tree del repo
        tree_url = "https://api.github.com/repos/appcml/CIC-TV/git/trees/main?recursive=1"
        r = requests.get(tree_url, timeout=10)
        if r.status_code == 200:
            tree = r.json()
            m3u_files = [f for f in tree.get('tree', []) if f['path'].endswith('.m3u') or f['path'].endswith('.m3u8')]
            
            print(f"📁 Archivos M3U encontrados en CIC-TV: {len(m3u_files)}")
            for f in m3u_files:
                print(f"   - {f['path']}")
                
                # Descargar cada M3U encontrado
                file_url = f"{CIC_TV_REPO}/{f['path']}"
                content = fetch_m3u(file_url)
                if content:
                    channels = parse_m3u_to_channels(content, f['path'])
                    all_channels.extend(channels)
    except Exception as e:
        print(f"⚠️ No se pudo listar archivos: {e}")
    
    # Eliminar duplicados por URL
    seen = set()
    unique = []
    for ch in all_channels:
        if ch["url"] not in seen:
            seen.add(ch["url"])
            unique.append(ch)
    
    print(f"\n{'='*60}")
    print(f"📊 TOTAL IMPORTADO: {len(unique)} canales unicos")
    print(f"{'='*60}")
    
    # Separar TV y Radio (heuristico: si tiene 'radio' en nombre o grupo)
    tv_channels = []
    radio_channels = []
    
    for ch in unique:
        name_lower = ch["name"].lower()
        group_lower = ch["group"].lower()
        
        if any(x in name_lower or x in group_lower for x in ['radio', 'fm', 'am ', 'estacion']):
            radio_channels.append(ch)
        else:
            tv_channels.append(ch)
    
    print(f"📺 TV: {len(tv_channels)}")
    print(f"📻 Radio: {len(radio_channels)}")
    
    # Guardar para validacion
    # Merge con existentes (evitar duplicados)
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
    
    # Combinar sin duplicados
    existing_urls = {ch["url"] for ch in existing_tv + existing_radio}
    
    new_tv = [ch for ch in tv_channels if ch["url"] not in existing_urls]
    new_radio = [ch for ch in radio_channels if ch["url"] not in existing_urls]
    
    merged_tv = existing_tv + new_tv
    merged_radio = existing_radio + new_radio
    
    print(f"\n🆕 NUEVOS canales a validar:")
    print(f"   TV: {len(new_tv)} (ya existian: {len(existing_tv)})")
    print(f"   Radio: {len(new_radio)} (ya existian: {len(existing_radio)})")
    
    # Guardar merged
    with open('data/tv_channels_raw.json', 'w', encoding='utf-8') as f:
        json.dump(merged_tv, f, ensure_ascii=False, indent=2)
    
    with open('data/radio_channels_raw.json', 'w', encoding='utf-8') as f:
        json.dump(merged_radio, f, ensure_ascii=False, indent=2)
    
    # Guardar log de importacion
    import_log = {
        "imported_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source": "CIC-TV",
        "total_found": len(unique),
        "new_tv": len(new_tv),
        "new_radio": len(new_radio),
        "channels": unique
    }
    
    with open('data/import_log.json', 'w', encoding='utf-8') as f:
        json.dump(import_log, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Importacion completada!")
    print(f"📁 Guardado en data/tv_channels_raw.json y data/radio_channels_raw.json")
    print(f"📋 Log guardado en data/import_log.json")
    
    return merged_tv, merged_radio

if __name__ == "__main__":
    import time
    import_from_cic_tv()
