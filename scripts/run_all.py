#!/usr/bin/env python3
"""
Orquestador principal
1. Scrapea nuevos canales de la web
2. Valida existentes (repara si puede)
3. Genera archivos finales
"""

import subprocess
import sys
import time

def run(script_name):
    print(f"\n{'='*60}")
    print(f"🚀 {script_name}")
    print(f"{'='*60}")
    result = subprocess.run([sys.executable, f"scripts/{script_name}"], capture_output=False)
    if result.returncode != 0:
        print(f"❌ Error en {script_name}")
        return False
    return True

def main():
    start = time.time()
    print(f"⏰ {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Buscar nuevos canales en la web
    if not run("scraper.py"):
        print("⚠️ Scrapeo falló, continuando con existentes...")
    
    # 2. Validar y reparar
    if not run("validator.py"):
        sys.exit(1)
    
    # 3. Generar M3U y JSON
    if not run("generator.py"):
        sys.exit(1)
    
    elapsed = time.time() - start
    print(f"\n{'='*60}")
    print(f"✅ COMPLETADO EN {elapsed:.1f}s")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
