#!/usr/bin/env python3
"""
Generador de archivos M3U y JSON API
"""

import json
import time
import os

def generate_m3u(channels, title="Lista IPTV"):
    """Genera contenido M3U estandar"""
    lines = [
        "#EXTM3U",
        '#PLAYLIST:' + title,
        '## Generado: ' + time.strftime("%Y-%m-%d %H:%M:%S"),
        '## Total canales: ' + str(len(channels)),
        '## Fuente: github.com/appcml/iptv-live-validator',
        ""
    ]
    
    for ch in channels:
        name = ch.get("name", "Sin nombre").replace('"', "'")
        logo = ch.get("logo", "")
        group = ch.get("group", "General").replace('"', "'")
        country = ch.get("country", "XX")
        
        extinf = '#EXTINF:-1 tvg-id="" tvg-name="' + name + '" tvg-logo="' + logo + '" group-title="' + group + '" tvg-country="' + country + '",' + name
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
    # CREAR CARPETAS SI NO EXISTEN
    os.makedirs('output', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    
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
    print("✅ output/lista_tv.m3u (" + str(len(tv)) + " canales)")
    
    # Generar M3U Radio
    m3u_radio = generate_m3u(radio, "Radio Stations - Solo Online")
    with open('output/lista_radio.m3u', 'w', encoding='utf-8') as f:
        f.write(m3u_radio)
    print("✅ output/lista_radio.m3u (" + str(len(radio)) + " radios)")
    
    # Generar M3U Completa
    all_channels = tv + radio
    m3u_all = generate_m3u(all_channels, "TV + Radio - Solo Online")
    with open('output/lista_completa.m3u', 'w', encoding='utf-8') as f:
        f.write(m3u_all)
    print("✅ output/lista_completa.m3u (" + str(len(all_channels)) + " total)")
    
    # Generar JSON API
    api_tv = generate_json_api(tv, "tv")
    with open('output/api_tv.json', 'w', encoding='utf-8') as f:
        json.dump(api_tv, f, ensure_ascii=False, indent=2)
    
    api_radio = generate_json_api(radio, "radio")
    with open('output/api_radio.json', 'w', encoding='utf-8') as f:
        json.dump(api_radio, f, ensure_ascii=False, indent=2)
    
    api_all = generate_json_api(all_channels, "all")
    with open('output/api_all.json', 'w', encoding='utf-8') as f:
        json.dump(api_all, f, ensure_ascii=False, indent=2)
    
    print("✅ Archivos API JSON generados")
    
    # Generar README
    updated = time.strftime("%Y-%m-%d %H:%M:%S")
    readme = "# 📺 Canales Activos M3U\n\n"
    readme += "**Actualizado:** " + updated + "\n"
    readme += "**Estado:** ✅ Todos los streams verificados y online\n\n"
    readme += "## 📊 Estadísticas\n"
    readme += "- **TV:** " + str(len(tv)) + " canales funcionando\n"
    readme += "- **Radio:** " + str(len(radio)) + " estaciones funcionando\n"
    readme += "- **Total:** " + str(len(all_channels)) + " streams activos\n\n"
    readme += "## 📥 Descargas\n\n"
    readme += "| Lista | Canales | Link |\n"
    readme += "|-------|---------|------|\n"
    readme += "| TV | " + str(len(tv)) + " | [lista_tv.m3u](lista_tv.m3u) |\n"
    readme += "| Radio | " + str(len(radio)) + " | [lista_radio.m3u](lista_radio.m3u) |\n"
    readme += "| Completa | " + str(len(all_channels)) + " | [lista_completa.m3u](lista_completa.m3u) |\n\n"
    readme += "## 🔗 API JSON (para tu app)\n\n"
    readme += "```javascript\n"
    readme += "// TV\n"
    readme += "fetch('https://raw.githubusercontent.com/appcml/iptv-live-validator/main/output/api_tv.json')\n\n"
    readme += "// Radio\n"
    readme += "fetch('https://raw.githubusercontent.com/appcml/iptv-live-validator/main/output/api_radio.json')\n\n"
    readme += "// Todo\n"
    readme += "fetch('https://raw.githubusercontent.com/appcml/iptv-live-validator/main/output/api_all.json')\n"
    readme += "```\n\n"
    readme += "## ⏰ Actualizacion\n"
    readme += "Bot automatico verifica cada 3 horas. Solo canales online.\n"
    
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(readme)
    
    print("✅ README.md actualizado")

if __name__ == "__main__":
    main()
