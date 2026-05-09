#!/usr/bin/env python3
"""
Memory Reader Tool für LehrerAgent

Liest Memory-Dateien im OpenClaw-Memory-Verzeichnis.
Kann nach Abschnitten (##-Headings) oder Schlüssel-Wert-Paaren filtern.
"""

import sys
import json
import os
import re
from pathlib import Path


def get_memory_path(relative_path: str) -> Path:
    """Konvertiert relativen Pfad zu absolutem Pfad im repo-lokalen Memory-Verzeichnis."""
    memory_dir = Path(__file__).resolve().parents[1] / "memory"
    return memory_dir / relative_path


def read_file_content(filepath: Path) -> str:
    """Liest Datei mit UTF-8 Encoding."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return ""


def extract_section(content: str, section_name: str) -> str:
    """
    Extrahiert einen Abschnitt aus Markdown.
    Ein Abschnitt beginnt mit '## Section Name' und endet vor dem nächsten '##'
    oder Dateiende.
    """
    if not content:
        return ""
    
    # Escapen des Section-Namens für Regex
    escaped_section = re.escape(section_name)
    pattern = rf'^##\s*{escaped_section}\s*$(.*?)(?=^##|\Z)'
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    
    if match:
        return match.group(1).strip()
    return ""


def extract_by_key(content: str, key: str) -> str:
    """
    Sucht nach Markdown-Listen-Einträgen mit dem Format "- **Key:** Value"
    Gibt den Wert zurück.
    """
    if not content:
        return ""
    
    # Suche nach dem Schlüssel
    pattern = rf'^-\s*\*\*{re.escape(key)}:\*\*\s*(.+)$'
    match = re.search(pattern, content, re.MULTILINE)
    
    if match:
        return match.group(1).strip()
    return ""


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
        if not filepath:
            raise ValueError("'filepath' ist erforderlich")
        
        section = args.get("section")
        key = args.get("key")
        
        # Absolute Pfad bestimmen
        abs_path = get_memory_path(filepath)
        
        # Existenz prüfen
        exists = abs_path.exists() and abs_path.is_file()
        
        if not exists:
            output = {
                "success": True,
                "content": "",
                "exists": False,
                "error": None
            }
            print(json.dumps(output, ensure_ascii=False))
            return
        
        # Datei lesen
        content = read_file_content(abs_path)
        
        # Filtern nach Section
        if section:
            filtered_content = extract_section(content, section)
        else:
            filtered_content = content
        
        # Filtern nach Key (nur wenn noch nicht nach Section gefiltert wurde)
        if key and filtered_content:
            filtered_content = extract_by_key(filtered_content, key)
        
        # Output
        output = {
            "success": True,
            "content": filtered_content,
            "exists": True,
            "error": None
        }
        
    except Exception as e:
        output = {
            "success": False,
            "content": "",
            "exists": False,
            "error": str(e)
        }
    
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
