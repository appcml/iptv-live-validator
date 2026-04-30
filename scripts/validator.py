#!/usr/bin/env python3
"""
Validador inteligente
- Verifica streams online
- Elimina caídos
- Intenta reparar links rotos buscando alternativas
"""

import requests
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': '*/*',
}

# LÍMITES
MAX_CHANNELS = 500        # Validar hasta 500 por tipo
TIMEOUT = 6
MAX_WORKERS = 12

# FUENTES ALTERNATIVAS PARA REPARAR (busca mismo canal en otras listas)
REPAIR_SOURCES = [
    "https://iptv-org.github.io/iptv/index.m3u",
]

def validate_stream(url, timeout=TIMEOUT):
    """Valida si un stream está online"""
    result = {
        "url": url,
        "online": False,
        "status_code": 0,
        "response_time": 0,
        "checked_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "error": ""
    }
    
    try:
        start = time.time()
        r = requests.head(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        result["response_time"] = round(time.time() - start, 2)
        result["status_code"] = r.status_code
        
        if r.status_code in [200, 301, 302, 307]:
            result["online"] = True
            
    except requests.exceptions.Timeout:
        result["error"] = "Timeout"
    except Exception as e:
        result["error"] = str(e)[:30]
    
    return result

def try_repair_channel(channel):
    """Intenta encontrar link alternativo para canal caído"""
    print(f"   🔧 Intentando reparar: {channel['name'][:40]}")
    
    # Buscar en fuentes alternativas
    for source_url in REPAIR_SOURCES:
        try:
            r = requests.get(source_url, headers=HEADERS, timeout=15)
            if r.status_code == 200:
                content = r.text
                lines = content.split('\n')
                
                for i, line in enumerate(lines):
                    if channel['name'].lower() in line.lower():
                        # Encontró el canal, buscar URL siguiente
                        for j in range(i+1, min(i+5, len(lines))):
                            if lines[j].startswith('http'):
                                new_url = lines[j].strip()
                                # Validar nuevo link
                                test = validate_stream(new_url, timeout=4)
                                if test["online"]:
                                    print(f"   ✅ Reparado: {new_url[:60]}")
                                    return new_url
        except:
            pass
    
    return None

def validate_channels(channels, max_workers=MAX_WORKERS, try_repair=True):
    """Valida canales, elimina caídos, intenta reparar"""
    
    if len(channels) > MAX_CHANNELS:
        print(f"⚠️ Limitando a {MAX_CHANNELS} de {len(channels)} canales")
        channels = channels[:MAX_CHANNELS]
    
    valid_channels = []
    repaired = 0
    removed = 0
    total = len(channels)
    
    print(f"🔍 Validando {total} streams...")
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_channel = {executor.submit(validate_stream, ch["url"]): ch for ch in channels}
        
        completed = 0
        for future in as_completed(future_to_channel):
            channel = future_to_channel[future]
            completed += 1
            
            try:
                result = future.result()
                
                if result["online"]:
                    channel["validation"] = result
                    valid_channels.append(channel)
                    
                    if completed % 25 == 0:
                        print(f"   [{completed}/{total}] ✅ {channel['name'][:40]} ({result['response_time']}s)")
                        
                else:
                    # INTENTAR REPARAR
                    if try_repair:
                        new_url = try_repair_channel(channel)
                        if new_url:
                            channel["url"] = new_url
                            channel["validation"] = validate_stream(new_url)
                            valid_channels.append(channel)
                            repaired += 1
                        else:
                            removed += 1
                    else:
                        removed += 1
                        
            except Exception as e:
                removed += 1
    
    total_time = time.time() - start_time
    print(f"\n📊 Resultado: {len(valid_channels)}/{total} online")
    print(f"   🔧 Reparados: {repaired}")
    print(f"   ❌ Eliminados: {removed}")
    print(f"   ⏱️ Tiempo: {total_time:.1f}s")
    
    return valid_channels

def main():
    # Cargar canales crudos
    try:
        with open('data/tv_channels_raw.json', 'r', encoding='utf-8') as f:
            tv_raw = json.load(f)
    except:
        tv_raw = []
        print("⚠️ No hay TV crudo")
    
    try:
        with open('data/radio_channels_raw.json', 'r', encoding='utf-8') as f:
            radio_raw = json.load(f)
    except:
        radio_raw = []
        print("⚠️ No hay Radio crudo")
    
    print("\n" + "="*60)
    print("VALIDANDO TV")
    print("="*60)
    tv_valid = validate_channels(tv_raw, try_repair=True)
    
    print("\n" + "="*60)
    print("VALIDANDO RADIO")
    print("="*60)
    radio_valid = validate_channels(radio_raw, try_repair=True)
    
    # Guardar validados
    with open('data/tv_channels.json', 'w', encoding='utf-8') as f:
        json.dump(tv_valid, f, ensure_ascii=False, indent=2)
    
    with open('data/radio_channels.json', 'w', encoding='utf-8') as f:
        json.dump(radio_valid, f, ensure_ascii=False, indent=2)
    
    # Guardar caídos para análisis
    tv_offline = [ch for ch in tv_raw if ch["url"] not in {v["url"] for v in tv_valid}]
    radio_offline = [ch for ch in radio_raw if ch["url"] not in {v["url"] for v in radio_valid}]
    
    with open('data/offline_log.json', 'w', encoding='utf-8') as f:
        json.dump({
            "checked_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "tv_total": len(tv_raw),
            "tv_online": len(tv_valid),
            "tv_offline": len(tv_offline),
            "radio_total": len(radio_raw),
            "radio_online": len(radio_valid),
            "radio_offline": len(radio_offline),
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Validación completada")
    print(f"   📺 TV: {len(tv_valid)} online / {len(tv_offline)} caídos")
    print(f"   📻 Radio: {len(radio_valid)} online / {len(radio_offline)} caídos")

if __name__ == "__main__":
    main()
