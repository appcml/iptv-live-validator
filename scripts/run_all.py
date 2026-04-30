#!/usr/bin/env python3
"""
Orquestador principal
Ejecuta todo el pipeline: scrape -> validate -> generate
"""

import subprocess
import sys
import time

def run(script_name):
    print(f"\n{'='*60}")
    print(f"EJECUTANDO: {script_name}")
    print(f"{'='*60}")
    result = subprocess.run([sys.executable, f"scripts/{script_name}"], capture_output=False)
    if result.returncode != 0:
        print(f"❌ Error en {script_name}")
        return False
    return True

def main():
    start_time = time.time()
    
    print("🚀 INICIANDO PIPELINE DE ACTUALIZACIÓN")
    print(f"⏰ {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Scrapear fuentes
    if not run("scraper.py"):
        sys.exit(1)
    
    # 2. Validar streams
    if not run("validator.py"):
        sys.exit(1)
    
    # 3. Generar archivos finales
    if not run("generator.py"):
        sys.exit(1)
    
    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"✅ PIPELINE COMPLETADO EN {elapsed:.1f} SEGUNDOS")
    print(f"{'='*60}")
    print(f"📁 Archivos generados en /output")
    print(f"🔗 Tu app puede leer desde:")
    print(f"   - output/api_all.json")
    print(f"   - output/lista_completa.m3u")

if __name__ == "__main__":
    main()
