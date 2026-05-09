#!/usr/bin/env python3
"""
Lehrplan Searcher Tool für LehrerAgent

Führt semantische Suche in indizierten Lehrplänen durch.
Verwendet ChromaDB für Vektorsuche mit lokalen Embeddings.
"""

import sys
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional


def get_chromadb_path() -> Path:
    """Gibt den Pfad zur ChromaDB zurück."""
    db_path = Path(__file__).resolve().parent / "chroma_db"
    return db_path


def get_embedding_model():
    """Lädt das sentence-transformers Modell für Query-Embeddings."""
    try:
        from sentence_transformers import SentenceTransformer
        # Gleiches Modell wie beim Indexieren verwenden
        model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        return model
    except ImportError:
        raise ImportError("sentence-transformers nicht installiert. Bitte installieren: pip install sentence-transformers")


def get_all_collections(client) -> List[str]:
    """Gibt alle verfügbaren Collections in der Datenbank zurück."""
    try:
        collections = client.list_collections()
        return [col.name for col in collections]
    except Exception:
        return []


def filter_collections_by_metadata(collections: List[str], filter_dict: Dict[str, Any]) -> List[str]:
    """
    Filtert Collections basierend auf Metadaten.
    
    Args:
        collections: Liste von Collection-Namen
        filter_dict: Dictionary mit Filterkriterien (z.B. {'bundesland': 'Bayern'})
    
    Returns:
        Gefilterte Liste von Collection-Namen
    """
    if not filter_dict:
        return collections
    
    filtered = []
    for collection_name in collections:
        # Extrahiere Metadaten aus Collection-Namen
        # Format: lehrplan_bundesland_schulform_fach_klasse_hash
        parts = collection_name.split('_')
        
        if len(parts) < 6:  # Mindestens: lehrplan + 4 Felder + hash
            continue
        
        # Mapping der Positionen (abhängig vom Namensschema)
        collection_metadata = {
            'bundesland': parts[1] if len(parts) > 1 else '',
            'schulform': parts[2] if len(parts) > 2 else '',
            'fach': parts[3] if len(parts) > 3 else '',
            'klasse': parts[4] if len(parts) > 4 else ''
        }
        
        # Prüfe alle Filterkriterien
        matches_all = True
        for key, value in filter_dict.items():
            if value is None:
                continue
                
            if key in collection_metadata:
                # Normalisiere für Vergleich
                collection_value = collection_metadata[key].lower().replace('_', ' ')
                filter_value = str(value).lower().replace('_', ' ')
                
                # Teilübereinstimmung erlauben
                if filter_value not in collection_value and collection_value not in filter_value:
                    matches_all = False
                    break
        
        if matches_all:
            filtered.append(collection_name)
    
    return filtered


def search_in_collection(collection, query_embedding: List[float], n_results: int, 
                         where_filter: Optional[Dict] = None) -> List[Dict]:
    """
    Sucht in einer einzelnen Collection.
    
    Args:
        collection: ChromaDB Collection
        query_embedding: Embedding der Query
        n_results: Anzahl der Ergebnisse
        where_filter: Optionaler Filter für Metadaten
    
    Returns:
        Liste von Ergebnissen
    """
    try:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter,
            include=['documents', 'metadatas', 'distances']
        )
        
        if not results['documents']:
            return []
        
        formatted_results = []
        for i in range(len(results['documents'][0])):
            formatted_results.append({
                'text': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': float(results['distances'][0][i]) if results['distances'] else 0.0
            })
        
        return formatted_results
    except Exception as e:
        print(f"Fehler bei Suche in Collection {collection.name}: {e}", file=sys.stderr)
        return []


def main():
    try:
        # JSON Input parsen
        if len(sys.argv) > 1:
            args = json.loads(sys.argv[1])
        else:
            # Fallback: von stdin lesen
            args = json.load(sys.stdin)
        
        # Input validieren
        query = args.get("query", "")
        n_results = args.get("n_results", 3)
        filter_dict = args.get("filter", {})
        
        if not query:
            raise ValueError("'query' ist erforderlich")
        
        # ChromaDB initialisieren
        try:
            import chromadb
        except ImportError:
            raise ImportError("chromadb nicht installiert. Bitte installieren: pip install chromadb")
        
        db_path = get_chromadb_path()
        
        # Prüfen ob Datenbank existiert
        if not db_path.exists() or not any(db_path.iterdir()):
            output = {
                "success": True,
                "results": [],
                "warning": "Keine indizierten Lehrpläne gefunden. Bitte zuerst Lehrpläne mit lehrplan_indexer.py indizieren.",
                "error": None
            }
            print(json.dumps(output, ensure_ascii=False))
            return
        
        client = chromadb.PersistentClient(path=str(db_path))
        
        # Alle Collections abrufen
        all_collections = get_all_collections(client)
        
        if not all_collections:
            output = {
                "success": True,
                "results": [],
                "warning": "Keine Collections in der Datenbank gefunden.",
                "error": None
            }
            print(json.dumps(output, ensure_ascii=False))
            return
        
        # Collections nach Metadaten filtern
        filtered_collections = filter_collections_by_metadata(all_collections, filter_dict)
        
        if not filtered_collections:
            output = {
                "success": True,
                "results": [],
                "warning": f"Keine Collections gefunden, die den Filterkriterien entsprechen: {filter_dict}",
                "error": None
            }
            print(json.dumps(output, ensure_ascii=False))
            return
        
        # Embedding-Modell für Query laden
        model = get_embedding_model()
        query_embedding = model.encode([query])[0].tolist()
        
        # In allen gefilterten Collections suchen
        all_results = []
        
        for collection_name in filtered_collections:
            try:
                collection = client.get_collection(collection_name)
                
                # Zusätzlicher Filter für Metadaten innerhalb der Collection
                where_filter = {}
                for key, value in filter_dict.items():
                    if value is not None and key in ['bundesland', 'schulform', 'fach', 'klasse']:
                        where_filter[key] = str(value)
                
                results = search_in_collection(
                    collection, 
                    query_embedding, 
                    n_results,
                    where_filter if where_filter else None
                )
                
                # Collection-Name zu Metadaten hinzufügen
                for result in results:
                    result['metadata']['collection'] = collection_name
                    all_results.append(result)
                    
            except Exception as e:
                print(f"Fehler mit Collection {collection_name}: {e}", file=sys.stderr)
                continue
        
        # Ergebnisse nach Distanz sortieren (niedrigste Distanz = beste Übereinstimmung)
        all_results.sort(key=lambda x: x['distance'])
        
        # Top n_results auswählen
        top_results = all_results[:n_results]
        
        # Distanz in Lesbarkeit umwandeln (0 = perfekt, höher = schlechter)
        for result in top_results:
            # Normalisiere Distanz für bessere Lesbarkeit
            result['similarity_score'] = max(0.0, 1.0 - result['distance'])
        
        # Erfolgsoutput
        output = {
            "success": True,
            "results": top_results,
            "total_collections_searched": len(filtered_collections),
            "total_results_found": len(all_results),
            "warning": None if top_results else "Keine passenden Ergebnisse gefunden.",
            "error": None
        }
        
    except Exception as e:
        output = {
            "success": False,
            "results": [],
            "total_collections_searched": 0,
            "total_results_found": 0,
            "warning": None,
            "error": str(e)
        }
    
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
