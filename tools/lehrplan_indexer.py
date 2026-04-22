#!/usr/bin/env python3
"""
Lehrplan Indexer Tool für LehrerAgent

Indiziert Lehrplan-Text in ChromaDB als Vektoren für semantische Suche.
Verwendet sentence-transformers für lokale Embeddings (DSGVO-konform).
"""

import sys
import json
import os
import hashlib
from pathlib import Path
from typing import List, Dict, Any


def get_chromadb_path() -> Path:
    """Gibt den Pfad zur ChromaDB zurück."""
    home = Path.home()
    db_path = home / ".openclaw" / "memory" / "lehrplan_vectordb"
    db_path.mkdir(parents=True, exist_ok=True)
    return db_path


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    Teilt Text in überlappende Chunks.
    
    Args:
        text: Der zu chunkende Text
        chunk_size: Maximale Zeichen pro Chunk
        overlap: Überlappung zwischen Chunks in Zeichen
    
    Returns:
        Liste von Text-Chunks
    """
    if not text:
        return []
    
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = min(start + chunk_size, text_length)
        
        # Versuche, am Satzende zu schneiden
        if end < text_length:
            # Suche nach Satzende
            for i in range(end, max(start, end - 100), -1):
                if i < text_length and text[i] in '.!?':
                    end = i + 1
                    break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        start = end - overlap  # Überlappung für nächsten Chunk
    
    return chunks


def get_embedding_model():
    """Lädt das sentence-transformers Modell."""
    try:
        from sentence_transformers import SentenceTransformer
        # Multilinguales Modell für Deutsch
        model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        return model
    except ImportError:
        raise ImportError("sentence-transformers nicht installiert. Bitte installieren: pip install sentence-transformers")


def create_collection_name(metadata: Dict[str, Any]) -> str:
    """Erstellt einen eindeutigen Collection-Namen aus Metadaten."""
    # Normalisiere Werte
    parts = [
        metadata.get('bundesland', 'unknown').lower().replace(' ', '_'),
        metadata.get('schulform', 'unknown').lower().replace(' ', '_'),
        metadata.get('fach', 'unknown').lower().replace(' ', '_'),
        metadata.get('klasse', 'unknown').lower().replace(' ', '_')
    ]
    
    # Erstelle Hash für Eindeutigkeit
    metadata_str = json.dumps(metadata, sort_keys=True)
    hash_obj = hashlib.md5(metadata_str.encode())
    hash_hex = hash_obj.hexdigest()[:8]
    
    return f"lehrplan_{'_'.join(parts)}_{hash_hex}"


def main():
    try:
        # JSON Input parsen
        if len(sys.argv) > 1:
            args = json.loads(sys.argv[1])
        else:
            # Fallback: von stdin lesen
            args = json.load(sys.stdin)
        
        # Input validieren
        text = args.get("text", "")
        metadata = args.get("metadata", {})
        chunk_size = args.get("chunk_size", 500)
        
        if not text:
            raise ValueError("'text' ist erforderlich")
        
        # Pflichtfelder in Metadaten prüfen
        required_fields = ['bundesland', 'schulform', 'fach', 'klasse']
        for field in required_fields:
            if field not in metadata:
                raise ValueError(f"Metadaten-Feld '{field}' ist erforderlich")
        
        # Text in Chunks aufteilen
        chunks = chunk_text(text, chunk_size)
        
        if not chunks:
            output = {
                "success": True,
                "chunks_indexed": 0,
                "collection": "",
                "warning": "Keine Text-Chunks erzeugt (Text möglicherweise zu kurz)",
                "error": None
            }
            print(json.dumps(output, ensure_ascii=False))
            return
        
        # Embedding-Modell laden
        model = get_embedding_model()
        
        # Embeddings berechnen
        embeddings = model.encode(chunks, show_progress_bar=False)
        
        # ChromaDB initialisieren
        try:
            import chromadb
        except ImportError:
            raise ImportError("chromadb nicht installiert. Bitte installieren: pip install chromadb")
        
        db_path = get_chromadb_path()
        client = chromadb.PersistentClient(path=str(db_path))
        
        # Collection-Name erstellen
        collection_name = create_collection_name(metadata)
        
        # Collection erstellen oder laden
        try:
            collection = client.get_collection(collection_name)
            # Collection existiert bereits - löschen und neu erstellen
            client.delete_collection(collection_name)
            collection = client.create_collection(collection_name)
        except:
            # Collection existiert nicht - neu erstellen
            collection = client.create_collection(collection_name)
        
        # Dokumente vorbereiten
        documents = []
        metadatas = []
        ids = []
        
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            # Metadaten für diesen Chunk
            chunk_metadata = metadata.copy()
            chunk_metadata['chunk_index'] = i
            chunk_metadata['total_chunks'] = len(chunks)
            
            documents.append(chunk)
            metadatas.append(chunk_metadata)
            ids.append(f"{collection_name}_chunk_{i}")
        
        # In ChromaDB speichern
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
            embeddings=embeddings.tolist()  # Konvertiere numpy array zu Liste
        )
        
        # Erfolgsoutput
        output = {
            "success": True,
            "chunks_indexed": len(chunks),
            "collection": collection_name,
            "db_path": str(db_path),
            "warning": None,
            "error": None
        }
        
    except Exception as e:
        output = {
            "success": False,
            "chunks_indexed": 0,
            "collection": "",
            "db_path": "",
            "warning": None,
            "error": str(e)
        }
    
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()