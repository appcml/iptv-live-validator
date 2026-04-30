#!/usr/bin/env python3
"""
Orquestador principal
Ejecuta todo el pipeline: scrape -> [import] -> validate -> generate
"""

import subprocess
import sys
import time
import os

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
    
    # Detectar si estamos en GitHub Actions (no interactivo)
    in_github = os.environ.get('GITHUB_ACTIONS') == 'true'
    
    # Preguntar si importar desde CIC-TV (solo modo manual)
    if not in_github:
        print("\n" + "="*60)
        print("¿Importar canales desde CIC-TV?")
        print("="*60)
        print("1. Si - Importar desde CIC-TV antes de validar")
        print("2. No - Solo usar fuentes actuales")
        print("="*60)
        
        # En GitHub Actions usa '2', en local pregunta
        respuesta = input("Selecciona (1 o 2): ").strip()
        
        if respuesta == '1':
            print("\n📥 IMPORTANDO DESDE CIC-TV...")
            if not run("import_from_cic_tv.py"):
                print("⚠️ Fallo importacion, continuando con fuentes actuales...")
        else:
            print("⏭️ Saltando importacion")
    
    # 1. Scrapear fuentes externas
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
