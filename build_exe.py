#!/usr/bin/env python3
"""
Build-Skript für die Maschinengemeinschaft EXE-Datei
"""

import PyInstaller.__main__
import os
import shutil
from pathlib import Path

def build_exe():
    # Basis-Pfad
    base_path = Path(__file__).parent
    
    # Definiere welche Dateien inkludiert werden sollen
    datas = [
        (str(base_path / 'templates'), 'templates'),
        (str(base_path / 'static'), 'static'),
        (str(base_path / 'schema.sql'), '.'),
        (str(base_path / 'database.py'), '.'),
    ]
    
    # PyInstaller Argumente
    args = [
        str(base_path / 'launcher.py'),
        '--name=Maschinengemeinschaft',
        '--onefile',
        '--windowed',  # Kein Konsolen-Fenster
        '--icon=static/favicon.ico' if (base_path / 'static' / 'favicon.ico').exists() else '',
        '--add-data=' + ';'.join(datas[0]) if os.name == 'nt' else '--add-data=' + ':'.join(datas[0]),
        '--add-data=' + ';'.join(datas[1]) if os.name == 'nt' else '--add-data=' + ':'.join(datas[1]),
        '--add-data=' + ';'.join(datas[2]) if os.name == 'nt' else '--add-data=' + ':'.join(datas[2]),
        '--hidden-import=flask',
        '--hidden-import=sqlite3',
        '--hidden-import=werkzeug',
        '--hidden-import=jinja2',
        '--hidden-import=email_validator',
        '--collect-all=flask',
        '--collect-all=werkzeug',
        '--collect-all=jinja2',
    ]
    
    # Entferne leere Icon-Argument
    args = [arg for arg in args if arg]
    
    print("Starte Build-Prozess...")
    print("=" * 60)
    
    try:
        PyInstaller.__main__.run(args)
        print("\n" + "=" * 60)
        print("✓ Build erfolgreich!")
        print(f"EXE-Datei: {base_path / 'dist' / 'Maschinengemeinschaft.exe'}")
    except Exception as e:
        print(f"\n✗ Build fehlgeschlagen: {e}")
        return False
    
    return True

if __name__ == '__main__':
    build_exe()
