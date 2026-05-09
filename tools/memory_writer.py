#!/usr/bin/env python3
"""
Memory Writer Tool für LehrerAgent

Schreibt Memory-Dateien im OpenClaw-Memory-Verzeichnis.
Unterstützt verschiedene Modi: overwrite, append, update_section.
"""

import sys
import json
import os
import re
from pathlib import Path


def get_memory_path(relative_path: str) -> Path:
    """Konvertiert relativen Pfad zu absolutem Pfad im repo-lokalen Memory-Verzeichnis."""
    memory_dir = Path(__file__).resolve().parents[1] / "memory"
    # Verzeichnisstruktur sicherstellen
    memory_dir.mkdir(parents=True, exist_ok=True)
    return memory_dir / relative_path


def write_overwrite(filepath: Path, content: str) -> None:
    """Überschreibt Datei komplett."""
    # Elternverzeichnis erstellen falls nötig
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)


def write_append(filepath: Path, content: str) -> None:
    """Hängt Inhalt an bestehende Datei an."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'a', encoding='utf-8') as f:
        f.write(content)


def update_section(filepath: Path, section_name: str, new_content: str) -> None:
    """
    Aktualisiert einen bestimmten Abschnitt in einer Markdown-Datei.
    Der Abschnitt muss mit '## Section Name' beginnen.
    """
    # Datei lesen falls existiert
    if filepath.exists():
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        content = ""
    
    escaped_section = re.escape(section_name)
    pattern = rf'^(##\s*{escaped_section}\s*$\n?)(.*?)(?=^##|\Z)'
    
    if re.search(pattern, content, re.MULTILINE | re.DOTALL):
        # Abschnitt existiert - ersetzen
        replacement = f"## {section_name}\n\n{new_content}\n\n"
        new_content_all = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)
    else:
        # Abschnitt existiert nicht - am Ende hinzufügen
        if content and not content.endswith('\n'):
            content += '\n'
        new_content_all = content + f"## {section_name}\n\n{new_content}\n\n"
    
    # Zurückschreiben
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content_all)


def main():
    try:
        # JSON Input parsen
        if len(sys.argv) > 1:
            args = json.loads(sys.argv[1])
        else:
            # Fallback: von stdin lesen
            args = json.load(sys.stdin)
        
        # Input validieren
        filepath = args.get("filepath")
        mode = args.get("mode", "overwrite")
        content = args.get("content", "")
        section = args.get("section")
        
        if not filepath:
            raise ValueError("'filepath' ist erforderlich")
        
        if mode == "update_section" and not section:
            raise ValueError("'section' ist erforderlich im mode 'update_section'")
        
        # Absolute Pfad bestimmen
        abs_path = get_memory_path(filepath)
        
        # Je nach Modus schreiben
        if mode == "overwrite":
            write_overwrite(abs_path, content)
        elif mode == "append":
            write_append(abs_path, content)
        elif mode == "update_section":
            update_section(abs_path, section, content)
        else:
            raise ValueError(f"Unbekannter Modus: {mode}")
        
        # Erfolgsoutput
        output = {
            "success": True,
            "filepath": str(abs_path),
            "error": None
        }
        
    except Exception as e:
        output = {
            "success": False,
            "filepath": None,
            "error": str(e)
        }
    
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
