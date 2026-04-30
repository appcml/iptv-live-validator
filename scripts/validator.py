#!/usr/bin/env python3
"""
Validador de streams - VERSIÓN RÁPIDA
Timeouts cortos, límite de canales, workers reducidos
"""

import requests
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': '*/*',
}

# LÍMITES PARA NO SATURAR GITHUB ACTIONS
MAX_CHANNELS = 150        # Máximo canales a validar
TIMEOUT = 5               # Segundos de espera por stream
MAX_WORKERS = 10          # Workers paralelos (GitHub limita a ~20)

def validate_stream(url, timeout=TIMEOUT):
    """Valida si un stream está online - RÁPIDO"""
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
        # Solo HEAD request para no descargar contenido
        r = requests.head(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        result["response_time"] = round(time.time() - start, 2)
        result["status_code"] = r.status_code
        
        if r.status_code in [200, 301, 302]:
            result["online"] = True
            
    except requests.exceptions.Timeout:
        result["error"] = "Timeout"
    except Exception as e:
        result["error"] = str(e)[:30]
    
    return result

def validate_channels(channels, max_workers=MAX_WORKERS):
    """Valida lista de canales en paralelo - RÁPIDO"""
    
    # Limitar cantidad para no demorar
    if len(channels) > MAX_CHANNELS:
        print(f"⚠️ Limitando a {MAX_CHANNELS} de {len(channels)} canales")
        channels = channels[:MAX_CHANNELS]
    
    valid_channels = []
    total = len(channels)
    
    print(f"🔍 Validando {total} streams (timeout {TIMEOUT}s, {max_workers} workers)...")
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_channel = {executor.submit(validate_stream, ch["url"]): ch for ch in channels}
        
        completed = 0
        for future in as_completed(future_to_channel):
            channel = future_to_channel[future]
            completed += 1
            
            try:
                result = future.result()
                channel["validation"] = result
                
                if result["online"]:
                    valid_channels.append(channel)
                    status = f"✅ {result['response_time']}s"
                else:
                    status = f"❌ {result['error'] or result['status_code']}"
                
                # Mostrar progreso cada 20
                if completed % 20 == 0 or completed == total:
                    elapsed = time.time() - start_time
                    print(f"   [{completed}/{total}] {elapsed:.0f}s transcurridos - {status}")
                    
            except Exception as e:
                pass
    
    total_time = time.time() - start_time
    print(f"\n📊 {len(valid_channels)}/{total} online en {total_time:.1f} segundos")
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
    
    print("\n" + "="*50)
    print("VALIDANDO TV")
    print("="*50)
    tv_valid = validate_channels(tv_raw)
    
    print("\n" + "="*50)
    print("VALIDANDO RADIO")
    print("="*50)
    radio_valid = validate_channels(radio_raw)
    
    # Guardar validados
    with open('data/tv_channels.json', 'w', encoding='utf-8') as f:
        json.dump(tv_valid, f, ensure_ascii=False, indent=2)
    
    with open('data/radio_channels.json', 'w', encoding='utf-8') as f:
        json.dump(radio_valid, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Listo: {len(tv_valid)} TV + {len(radio_valid)} Radio")

if __name__ == "__main__":
    main()
