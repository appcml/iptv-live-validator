#!/usr/bin/env python3
"""
Generador de archivos M3U
Crea listas finales desde los JSON validados
"""

import json
import time

def generate_m3u(channels, title="Lista IPTV"):
    """Genera contenido M3U estándar"""
    lines = [
        "#EXTM3U",
        f'#PLAYLIST:{title}',
        f'## Generado: {time.strftime("%Y-%m-%d %H:%M:%S")}',
        f'## Total canales: {len(channels)}',
        f'## Fuente: github.com/tu-usuario/iptv-live-validator',
        ""
    ]
    
    for ch in channels:
        # Atributos EXTINF
        name = ch.get("name", "Sin nombre").replace('"', "'")
        logo = ch.get("logo", "")
        group = ch.get("group", "General").replace('"', "'")
        country = ch.get("country", "XX")
        
        extinf = f'#EXTINF:-1 tvg-id="" tvg-name="{name}" tvg-logo="{logo}" group-title="{group}" tvg-country="{country}",{name}'
        lines.append(extinf)
        lines.append(ch.get("url", ""))
        lines.append("")
    
    return "\n".join(lines)

def generate_json_api(channels, type_name):
    """Genera JSON simplificado para tu app"""
    return {
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "type": type_name,
        "count": len(channels),
        "channels": [
            {
                "name": ch.get("name"),
                "url": ch.get("url"),
                "logo": ch.get("logo"),
                "group": ch.get("group"),
                "country": ch.get("country")
            }
            for ch in channels
        ]
    }

def main():
    # Cargar canales validados
    try:
        with open('data/tv_channels.json', 'r', encoding='utf-8') as f:
            tv = json.load(f)
    except:
        tv = []
        print("⚠️ No hay canales TV validados")
    
    try:
        with open('data/radio_channels.json', 'r', encoding='utf-8') as f:
            radio = json.load(f)
    except:
        radio = []
        print("⚠️ No hay radios validadas")
    
    # Generar M3U TV
    m3u_tv = generate_m3u(tv, "TV Channels - Solo Online")
    with open('output/lista_tv.m3u', 'w', encoding='utf-8') as f:
        f.write(m3u_tv)
    print(f"✅ output/lista_tv.m3u ({len(tv)} canales)")
    
    # Generar M3U Radio
    m3u_radio = generate_m3u(radio, "Radio Stations - Solo Online")
    with open('output/lista_radio.m3u', 'w', encoding='utf-8') as f:
        f.write(m3u_radio)
    print(f"✅ output/lista_radio.m3u ({len(radio)} radios)")
    
    # Generar M3U Completa
    all_channels = tv + radio
    m3u_all = generate_m3u(all_channels, "TV + Radio - Solo Online")
    with open('output/lista_completa.m3u', 'w', encoding='utf-8') as f:
        f.write(m3u_all)
    print(f"✅ output/lista_completa.m3u ({len(all_channels)} total)")
    
    # Generar JSON API para tu app
    api_tv = generate_json_api(tv, "tv")
    with open('output/api_tv.json', 'w', encoding='utf-8') as f:
        json.dump(api_tv, f, ensure_ascii=False, indent=2)
    
    api_radio = generate_json_api(radio, "radio")
    with open('output/api_radio.json', 'w', encoding='utf-8') as f:
        json.dump(api_radio, f, ensure_ascii=False, indent=2)
    
    api_all = generate_json_api(all_channels, "all")
    with open('output/api_all.json', 'w', encoding='utf-8') as f:
        json.dump(api_all, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Archivos API JSON generados")
    
    # Generar README con estadísticas
    readme = f"""# 📺 Canales Activos M3U

**Actualizado:** {time.strftime("%Y-%m-%d %H:%M:%S")}  
**Estado:** ✅ Todos los streams verificados y online

## 📊 Estadísticas
- **TV:** {len(tv)} canales funcionando
- **Radio:** {len(radio)} estaciones funcionando
- **Total:** {len(all_channels)} streams activos

## 📥 Descargas

| Lista | Canales | Link |
|-------|---------|------|
| TV | {len(tv)} | [lista_tv.m3u](lista_tv.m3u) |
| Radio | {len(radio)} | [lista_radio.m3u](lista_radio.m3u) |
| Completa | {len(all_channels)} | [lista_completa.m3u](lista_completa.m3u) |

## 🔗 API JSON (para tu app)

```javascript
// TV
fetch('https://raw.githubusercontent.com/TU-USUARIO/iptv-live-validator/main/output/api_tv.json')

// Radio  
fetch('https://raw.githubusercontent.com/TU-USUARIO/iptv-live-validator/main/output/api_radio.json')

// Todo
fetch('https://raw.githubusercontent.com/TU-USUARIO/iptv-live-validator/main/output/api_all.json')
