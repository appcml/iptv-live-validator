#!/usr/bin/env python3
"""
Validador de streams
Verifica que los canales/radios respondan HTTP 200
"""

import requests
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': '*/*',
    'Accept-Encoding': 'identity',
    'Connection': 'keep-alive',
}

def validate_stream(url, timeout=8):
    """
    Valida si un stream está online
    Retorna dict con estado y metadata
    """
    result = {
        "url": url,
        "online": False,
        "status_code": 0,
        "content_type": "",
        "response_time": 0,
        "checked_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "error": ""
    }
    
    try:
        start = time.time()
        # Usar stream=True para no descargar todo el contenido
        r = requests.get(
            url, 
            headers=HEADERS, 
            timeout=timeout, 
            stream=True,
            allow_redirects=True
        )
        result["response_time"] = round(time.time() - start, 2)
        result["status_code"] = r.status_code
        result["content_type"] = r.headers.get('content-type', 'unknown')
        
        if r.status_code == 200:
            # Leer solo los primeros bytes para confirmar que es media
            chunk = next(r.iter_content(1024), None)
            if chunk:
                result["online"] = True
        
        r.close()
        
    except requests.exceptions.Timeout:
        result["error"] = "Timeout"
    except requests.exceptions.ConnectionError:
        result["error"] = "Connection Error"
    except Exception as e:
        result["error"] = str(e)[:50]
    
    return result

def validate_channels(channels, max_workers=20):
    """
    Valida lista de canales en paralelo
    Retorna lista filtrada solo con los online
    """
    valid_channels = []
    total = len(channels)
    
    print(f"🔍 Validando {total} streams con {max_workers} workers...")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_channel = {
            executor.submit(validate_stream, ch["url"]): ch 
            for ch in channels
        }
        
        completed = 0
        for future in as_completed(future_to_channel):
            channel = future_to_channel[future]
            completed += 1
            
            try:
                result = future.result()
                channel["validation"] = result
                
                if result["online"]:
                    valid_channels.append(channel)
                    status = f"✅ ONLINE ({result['response_time']}s)"
                else:
                    status = f"❌ OFFLINE - {result['error'] or result['status_code']}"
                
                if completed % 10 == 0 or completed == total:
                    print(f"   [{completed}/{total}] {channel['name'][:40]:40} {status}")
                    
            except Exception as e:
                print(f"   [{completed}/{total}] {channel['name'][:40]:40} ❌ ERROR: {e}")
    
    print(f"\n📊 Resultado: {len(valid_channels)}/{total} streams online")
    return valid_channels

def load_and_validate():
    """Carga canales crudos, valida y guarda solo los funcionales"""
    
    # Cargar canales crudos
    try:
        with open('data/tv_channels_raw.json', 'r', encoding='utf-8') as f:
            tv_raw = json.load(f)
    except:
        tv_raw = []
        print("⚠️ No se encontró tv_channels_raw.json")
    
    try:
        with open('data/radio_channels_raw.json', 'r', encoding='utf-8') as f:
            radio_raw = json.load(f)
    except:
        radio_raw = []
        print("⚠️ No se encontró radio_channels_raw.json")
    
    # Validar
    print("\n" + "="*50)
    print("VALIDANDO CANALES TV")
    print("="*50)
    tv_valid = validate_channels(tv_raw, max_workers=15)
    
    print("\n" + "="*50)
    print("VALIDANDO RADIOS")
    print("="*50)
    radio_valid = validate_channels(radio_raw, max_workers=15)
    
    # Guardar canales validados
    with open('data/tv_channels.json', 'w', encoding='utf-8') as f:
        json.dump(tv_valid, f, ensure_ascii=False, indent=2)
    
    with open('data/radio_channels.json', 'w', encoding='utf-8') as f:
        json.dump(radio_valid, f, ensure_ascii=False, indent=2)
    
    # Guardar log de caídos para análisis
    tv_offline = [ch for ch in tv_raw if not ch.get("validation", {}).get("online", False)]
    radio_offline = [ch for ch in radio_raw if not ch.get("validation", {}).get("online", False)]
    
    with open('data/offline_log.json', 'w', encoding='utf-8') as f:
        json.dump({
            "checked_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "tv_offline": len(tv_offline),
            "radio_offline": len(radio_offline),
            "details": tv_offline + radio_offline
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Validación completada")
    print(f"   TV: {len(tv_valid)} online / {len(tv_offline)} caídos")
    print(f"   Radio: {len(radio_valid)} online / {len(radio_offline)} caídos")
    
    return tv_valid, radio_valid

if __name__ == "__main__":
    load_and_validate()
