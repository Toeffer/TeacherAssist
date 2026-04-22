#!/usr/bin/env python3
"""
Usage-Tracker für LehrerAgent
Überwacht Token-Verbrauch und API-Kosten für Claude API.

Diese Datei wird von OpenClaw aufgerufen, um Token- und Kosten-Tracking durchzuführen.
Sie speichert die Nutzungsdaten in einer JSON-Datei für die spätere Analyse.
"""

import json
import os
import sys
import time
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import hashlib

# LLM API Preise (Stand: April 2026)
# Quellen: 
# - Anthropic: https://www.anthropic.com/pricing
# - OpenRouter: https://openrouter.ai/docs#models
# - OpenAI: https://openai.com/pricing

LLM_PRICES = {
    # Anthropic Claude API (direkt)
    "anthropic": {
        "claude-3-5-sonnet-20241022": {
            "input": 3.00,      # $3.00 pro 1M Tokens
            "output": 15.00,    # $15.00 pro 1M Tokens
        },
        "claude-3-opus-20240229": {
            "input": 15.00,     # $15.00 pro 1M Tokens
            "output": 75.00,    # $75.00 pro 1M Tokens
        },
        "claude-3-sonnet-20240229": {
            "input": 3.00,      # $3.00 pro 1M Tokens
            "output": 15.00,    # $15.00 pro 1M Tokens
        },
        "claude-3-haiku-20240307": {
            "input": 0.25,      # $0.25 pro 1M Tokens
            "output": 1.25,     # $1.25 pro 1M Tokens
        },
    },
    
    # OpenRouter API (Aggregator für viele Modelle)
    "openrouter": {
        # Anthropic Modelle via OpenRouter
        "anthropic/claude-3-5-sonnet": {
            "input": 3.00,      # $3.00 pro 1M Tokens
            "output": 15.00,    # $15.00 pro 1M Tokens
        },
        "anthropic/claude-3-opus": {
            "input": 15.00,     # $15.00 pro 1M Tokens
            "output": 75.00,    # $75.00 pro 1M Tokens
        },
        "anthropic/claude-3-sonnet": {
            "input": 3.00,      # $3.00 pro 1M Tokens
            "output": 15.00,    # $15.00 pro 1M Tokens
        },
        "anthropic/claude-3-haiku": {
            "input": 0.25,      # $0.25 pro 1M Tokens
            "output": 1.25,     # $1.25 pro 1M Tokens
        },
        
        # OpenAI Modelle via OpenRouter
        "openai/gpt-4-turbo": {
            "input": 10.00,     # $10.00 pro 1M Tokens
            "output": 30.00,    # $30.00 pro 1M Tokens
        },
        "openai/gpt-4": {
            "input": 30.00,     # $30.00 pro 1M Tokens
            "output": 60.00,    # $60.00 pro 1M Tokens
        },
        "openai/gpt-3.5-turbo": {
            "input": 0.50,      # $0.50 pro 1M Tokens
            "output": 1.50,     # $1.50 pro 1M Tokens
        },
        
        # Google Modelle via OpenRouter
        "google/gemini-pro": {
            "input": 0.50,      # $0.50 pro 1M Tokens
            "output": 1.50,     # $1.50 pro 1M Tokens
        },
        "google/gemini-ultra": {
            "input": 7.50,      # $7.50 pro 1M Tokens
            "output": 22.50,    # $22.50 pro 1M Tokens
        },
        
        # Meta Modelle via OpenRouter
        "meta-llama/llama-2-70b-chat": {
            "input": 0.65,      # $0.65 pro 1M Tokens
            "output": 0.90,     # $0.90 pro 1M Tokens
        },
        "meta-llama/llama-3-70b-instruct": {
            "input": 0.88,      # $0.88 pro 1M Tokens
            "output": 0.88,     # $0.88 pro 1M Tokens
        },
        
        # Mistral Modelle via OpenRouter
        "mistralai/mistral-7b-instruct": {
            "input": 0.14,      # $0.14 pro 1M Tokens
            "output": 0.14,     # $0.14 pro 1M Tokens
        },
        "mistralai/mixtral-8x7b-instruct": {
            "input": 0.24,      # $0.24 pro 1M Tokens
            "output": 0.24,     # $0.24 pro 1M Tokens
        },
    },
    
    # OpenAI API (direkt)
    "openai": {
        "gpt-4-turbo": {
            "input": 10.00,     # $10.00 pro 1M Tokens
            "output": 30.00,    # $30.00 pro 1M Tokens
        },
        "gpt-4": {
            "input": 30.00,     # $30.00 pro 1M Tokens
            "output": 60.00,    # $60.00 pro 1M Tokens
        },
        "gpt-3.5-turbo": {
            "input": 0.50,      # $0.50 pro 1M Tokens
            "output": 1.50,     # $1.50 pro 1M Tokens
        },
    },
    
    # Google AI (direkt)
    "google": {
        "gemini-pro": {
            "input": 0.50,      # $0.50 pro 1M Tokens
            "output": 1.50,     # $1.50 pro 1M Tokens
        },
        "gemini-ultra": {
            "input": 7.50,      # $7.50 pro 1M Tokens
            "output": 22.50,    # $22.50 pro 1M Tokens
        },
    },
}

# Standard-Modell für LehrerAgent
DEFAULT_MODEL = "claude-3-5-sonnet-20241022"
DEFAULT_PROVIDER = "anthropic"

# Mapping für Modell-Erkennung
MODEL_MAPPING = {
    # OpenRouter Modelle zu Provider-Mapping
    "anthropic/claude-3-5-sonnet": ("anthropic", "claude-3-5-sonnet-20241022"),
    "anthropic/claude-3-opus": ("anthropic", "claude-3-opus-20240229"),
    "anthropic/claude-3-sonnet": ("anthropic", "claude-3-sonnet-20240229"),
    "anthropic/claude-3-haiku": ("anthropic", "claude-3-haiku-20240307"),
    
    # OpenAI Modelle
    "openai/gpt-4-turbo": ("openai", "gpt-4-turbo"),
    "openai/gpt-4": ("openai", "gpt-4"),
    "openai/gpt-3.5-turbo": ("openai", "gpt-3.5-turbo"),
    
    # Google Modelle
    "google/gemini-pro": ("google", "gemini-pro"),
    "google/gemini-ultra": ("google", "gemini-ultra"),
}

class UsageTracker:
    """Klasse zur Überwachung von Token-Verbrauch und API-Kosten."""
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialisiert den Usage-Tracker.
        
        Args:
            data_dir: Verzeichnis für die Speicherung der Nutzungsdaten
                     (Standard: ~/.openclaw/usage/)
        """
        if data_dir is None:
            data_dir = os.path.expanduser("~/.openclaw/usage/")
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Pfad zur Haupt-Nutzungsdatei
        self.usage_file = self.data_dir / "usage_data.json"
        
        # Initialisiere Datenstruktur
        self.data = self._load_data()
    
    def _load_data(self) -> Dict:
        """Lädt die Nutzungsdaten aus der JSON-Datei."""
        if self.usage_file.exists():
            try:
                with open(self.usage_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                # Bei Fehler: neue Datenstruktur erstellen
                pass
        
        # Standard-Datenstruktur
        return {
            "version": "1.0",
            "created": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "total_usage": {
                "total_tokens": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "total_cost_usd": 0.0,
                "total_requests": 0,
                "total_skills_executed": 0,
            },
            "daily_usage": {},
            "monthly_usage": {},
            "skill_usage": {},
            "model_usage": {},
            "settings": {
                "currency": "USD",
                "default_model": DEFAULT_MODEL,
                "cost_warning_threshold": 50.0,  # $50 Warnschwelle
                "monthly_budget": 100.0,         # $100 Monatsbudget
            }
        }
    
    def _save_data(self):
        """Speichert die Nutzungsdaten in die JSON-Datei."""
        self.data["last_updated"] = datetime.now().isoformat()
        
        # Sicherung der alten Datei
        if self.usage_file.exists():
            backup_file = self.data_dir / f"usage_backup_{int(time.time())}.json"
            try:
                import shutil
                shutil.copy2(self.usage_file, backup_file)
            except:
                pass
        
        # Speichere neue Datei
        try:
            with open(self.usage_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Fehler beim Speichern der Nutzungsdaten: {e}", file=sys.stderr)
    
    def _get_date_key(self, timestamp: Optional[str] = None) -> Tuple[str, str]:
        """
        Gibt Tages- und Monatsschlüssel zurück.
        
        Args:
            timestamp: ISO-Format Zeitstempel (Standard: jetzt)
            
        Returns:
            Tuple (day_key, month_key)
        """
        if timestamp:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        else:
            dt = datetime.now()
        
        day_key = dt.strftime("%Y-%m-%d")
        month_key = dt.strftime("%Y-%m")
        
        return day_key, month_key
    
    def _get_skill_id(self, skill_name: str) -> str:
        """
        Erzeugt eine konsistente Skill-ID aus dem Skill-Namen.
        
        Args:
            skill_name: Name des Skills
            
        Returns:
            Skill-ID (Hash)
        """
        # Normalisiere Skill-Namen
        normalized = skill_name.lower().strip().replace('/', '_').replace('\\', '_')
        
        # Erzeuge kurzen Hash für bessere Lesbarkeit
        hash_obj = hashlib.md5(normalized.encode())
        short_hash = hash_obj.hexdigest()[:8]
        
        return f"{normalized}_{short_hash}"
    
    def _get_model_prices(self, model: str, provider: Optional[str] = None) -> Tuple[str, str, Dict]:
        """
        Ermittelt Provider, Modellname und Preise für ein gegebenes Modell.
        
        Args:
            model: Modellname (kann OpenRouter-Format sein)
            provider: Optionaler Provider (wenn bekannt)
            
        Returns:
            Tuple (provider, model_name, prices)
        """
        # Prüfe zuerst, ob es sich um ein OpenRouter-Modell handelt
        if model in MODEL_MAPPING:
            provider, mapped_model = MODEL_MAPPING[model]
            if provider in LLM_PRICES and mapped_model in LLM_PRICES[provider]:
                return provider, mapped_model, LLM_PRICES[provider][mapped_model]
        
        # Prüfe direkte Provider-Modelle
        if provider:
            if provider in LLM_PRICES and model in LLM_PRICES[provider]:
                return provider, model, LLM_PRICES[provider][model]
        
        # Durchsuche alle Provider
        for prov, models in LLM_PRICES.items():
            if model in models:
                return prov, model, models[model]
        
        # Fallback: Standard-Modell
        print(f"Warnung: Unbekanntes Modell '{model}', verwende Standard-Preise", file=sys.stderr)
        return DEFAULT_PROVIDER, DEFAULT_MODEL, LLM_PRICES[DEFAULT_PROVIDER][DEFAULT_MODEL]
    
    def track_usage(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        skill_name: Optional[str] = None,
        request_id: Optional[str] = None,
        timestamp: Optional[str] = None,
        provider: Optional[str] = None
    ) -> Dict:
        """
        Trackt die Token-Nutzung und berechnet Kosten.
        
        Args:
            model: Modellname (z.B. "claude-3-5-sonnet-20241022" oder "anthropic/claude-3-5-sonnet")
            input_tokens: Anzahl der Input-Tokens
            output_tokens: Anzahl der Output-Tokens
            skill_name: Optionaler Skill-Name für detailliertes Tracking
            request_id: Optionale Request-ID für Debugging
            timestamp: Optionaler Zeitstempel (ISO-Format)
            provider: Optionaler Provider (wenn nicht aus Modellname erkennbar)
            
        Returns:
            Dictionary mit Tracking-Informationen und Kosten
        """
        # Ermittle Provider und Preise
        provider, model_name, prices = self._get_model_prices(model, provider)
        
        # Berechne Kosten
        input_cost = (input_tokens / 1_000_000) * prices["input"]
        output_cost = (output_tokens / 1_000_000) * prices["output"]
        total_cost = input_cost + output_cost
        total_tokens = input_tokens + output_tokens
        
        # Hole Zeitstempel
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        day_key, month_key = self._get_date_key(timestamp)
        
        # Update Gesamtnutzung
        total = self.data["total_usage"]
        total["total_tokens"] += total_tokens
        total["input_tokens"] += input_tokens
        total["output_tokens"] += output_tokens
        total["total_cost_usd"] += total_cost
        total["total_requests"] += 1
        
        if skill_name:
            total["total_skills_executed"] += 1
        
        # Update Tagesnutzung
        if day_key not in self.data["daily_usage"]:
            self.data["daily_usage"][day_key] = {
                "total_tokens": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "total_cost_usd": 0.0,
                "requests": 0,
                "skills": {},
            }
        
        daily = self.data["daily_usage"][day_key]
        daily["total_tokens"] += total_tokens
        daily["input_tokens"] += input_tokens
        daily["output_tokens"] += output_tokens
        daily["total_cost_usd"] += total_cost
        daily["requests"] += 1
        
        # Update Monatsnutzung
        if month_key not in self.data["monthly_usage"]:
            self.data["monthly_usage"][month_key] = {
                "total_tokens": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "total_cost_usd": 0.0,
                "requests": 0,
                "days": [],
            }
        
        monthly = self.data["monthly_usage"][month_key]
        monthly["total_tokens"] += total_tokens
        monthly["input_tokens"] += input_tokens
        monthly["output_tokens"] += output_tokens
        monthly["total_cost_usd"] += total_cost
        monthly["requests"] += 1
        
        if day_key not in monthly["days"]:
            monthly["days"].append(day_key)
        
        # Update Skill-Nutzung
        if skill_name:
            skill_id = self._get_skill_id(skill_name)
            
            if skill_id not in self.data["skill_usage"]:
                self.data["skill_usage"][skill_id] = {
                    "name": skill_name,
                    "total_tokens": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_cost_usd": 0.0,
                    "executions": 0,
                    "first_used": timestamp,
                    "last_used": timestamp,
                }
            
            skill = self.data["skill_usage"][skill_id]
            skill["total_tokens"] += total_tokens
            skill["input_tokens"] += input_tokens
            skill["output_tokens"] += output_tokens
            skill["total_cost_usd"] += total_cost
            skill["executions"] += 1
            skill["last_used"] = timestamp
            
            # Füge Skill zum Tages-Tracking hinzu
            if skill_name not in daily["skills"]:
                daily["skills"][skill_name] = {
                    "executions": 0,
                    "tokens": 0,
                    "cost": 0.0,
                }
            
            daily_skill = daily["skills"][skill_name]
            daily_skill["executions"] += 1
            daily_skill["tokens"] += total_tokens
            daily_skill["cost"] += total_cost
        
        # Update Modell-Nutzung
        if model not in self.data["model_usage"]:
            self.data["model_usage"][model] = {
                "total_tokens": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "total_cost_usd": 0.0,
                "requests": 0,
            }
        
        model_usage = self.data["model_usage"][model]
        model_usage["total_tokens"] += total_tokens
        model_usage["input_tokens"] += input_tokens
        model_usage["output_tokens"] += output_tokens
        model_usage["total_cost_usd"] += total_cost
        model_usage["requests"] += 1
        
        # Speichere Daten
        self._save_data()
        
        # Prüfe Budget-Warnungen
        warnings = self._check_budget_warnings(month_key, total_cost)
        
        # Rückgabe-Informationen
        result = {
            "success": True,
            "tracking": {
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "input_cost_usd": round(input_cost, 6),
                "output_cost_usd": round(output_cost, 6),
                "total_cost_usd": round(total_cost, 6),
                "skill": skill_name,
                "request_id": request_id,
                "timestamp": timestamp,
                "day_key": day_key,
                "month_key": month_key,
            },
            "totals": {
                "total_tokens": total["total_tokens"],
                "total_cost_usd": round(total["total_cost_usd"], 2),
                "total_requests": total["total_requests"],
            },
            "warnings": warnings,
        }
        
        return result
    
    def _check_budget_warnings(self, month_key: str, current_cost: float) -> List[str]:
        """
        Prüft Budget-Warnungen.
        
        Args:
            month_key: Monatsschlüssel (YYYY-MM)
            current_cost: Aktuelle Kosten des Requests
            
        Returns:
            Liste von Warnmeldungen
        """
        warnings = []
        settings = self.data["settings"]
        
        # Prüfe Monatsbudget
        monthly_budget = settings.get("monthly_budget", 100.0)
        monthly_usage = self.data["monthly_usage"].get(month_key, {})
        monthly_cost = monthly_usage.get("total_cost_usd", 0.0)
        
        if monthly_budget > 0:
            budget_percentage = (monthly_cost / monthly_budget) * 100
            
            if budget_percentage >= 90:
                warnings.append(f"⚠️ Monatsbudget zu 90% ausgeschöpft: ${monthly_cost:.2f} von ${monthly_budget:.2f}")
            elif budget_percentage >= 75:
                warnings.append(f"⚠️ Monatsbudget zu 75% ausgeschöpft: ${monthly_cost:.2f} von ${monthly_budget:.2f}")
        
        # Prüfe Kosten-Warnschwelle pro Request
        cost_warning = settings.get("cost_warning_threshold", 50.0)
        if current_cost > cost_warning:
            warnings.append(f"⚠️ Hohe Kosten für einen Request: ${current_cost:.2f}")
        
        return warnings
    
    def get_usage_summary(
        self, 
        period: str = "month", 
        period_key: Optional[str] = None
    ) -> Dict:
        """
        Gibt eine Zusammenfassung der Nutzung zurück.
        
        Args:
            period: Zeitraum ("day", "month", "total", "skill", "model")
            period_key: Optionaler Schlüssel (z.B. "2024-01" für Monat)
            
        Returns:
            Dictionary mit Nutzungszusammenfassung
        """
        if period == "total":
            return self.data["total_usage"]
        
        elif period == "day":
            if period_key is None:
                period_key = datetime.now().strftime("%Y-%m-%d")
            return self.data["daily_usage"].get(period_key, {})
        
        elif period == "month":
            if period_key is None:
                period_key = datetime.now().strftime("%Y-%m")
            return self.data["monthly_usage"].get(period_key, {})
        
        elif period == "skill":
            if period_key:
                # Spezifischer Skill
                skill_id = self._get_skill_id(period_key)
                return self.data["skill_usage"].get(skill_id, {})
            else:
                # Alle Skills
                return self.data["skill_usage"]
        
        elif period == "model":
            if period_key:
                # Spezifisches Modell
                return self.data["model_usage"].get(period_key, {})
            else:
                # Alle Modelle
                return self.data["model_usage"]
        
        else:
            return {"error": f"Unbekannter Zeitraum: {period}"}
    
    def get_cost_estimate(
        self, 
        model: str, 
        estimated_input_tokens: int, 
        estimated_output_tokens: int,
        provider: Optional[str] = None
    ) -> Dict:
        """
        Schätzt Kosten für einen geplanten Request.
        
        Args:
            model: Modellname
            estimated_input_tokens: Geschätzte Input-Tokens
            estimated_output_tokens: Geschätzte Output-Tokens
            provider: Optionaler Provider (wenn nicht aus Modellname erkennbar)
            
        Returns:
            Dictionary mit Kostenschätzung
        """
        # Ermittle Provider und Preise
        provider, model_name, prices = self._get_model_prices(model, provider)
        
        input_cost = (estimated_input_tokens / 1_000_000) * prices["input"]
        output_cost = (estimated_output_tokens / 1_000_000) * prices["output"]
        total_cost = input_cost + output_cost
        
        return {
            "provider": provider,
            "model": model_name,
            "original_model": model,
            "estimated_input_tokens": estimated_input_tokens,
            "estimated_output_tokens": estimated_output_tokens,
            "estimated_input_cost_usd": round(input_cost, 6),
            "estimated_output_cost_usd": round(output_cost, 6),
            "estimated_total_cost_usd": round(total_cost, 6),
            "price_per_million_input": prices["input"],
            "price_per_million_output": prices["output"],
        }
    
    def reset_usage(self, confirm: bool = False) -> Dict:
        """
        Setzt alle Nutzungsdaten zurück.
        
        Args:
            confirm: Bestätigung erforderlich
            
        Returns:
            Dictionary mit Ergebnis
        """
        if not confirm:
            return {
                "success": False,
                "error": "Bestätigung erforderlich. Setze confirm=True",
                "total_cost_before_reset": self.data["total_usage"]["total_cost_usd"],
            }
        
        # Sichere alte Daten
        backup_file = self.data_dir / f"usage_reset_backup_{int(time.time())}.json"
        try:
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            return {
                "success": False,
                "error": f"Backup fehlgeschlagen: {e}",
            }
        
        # Setze Daten zurück
        old_data = self.data.copy()
        self.data = self._load_data()  # Neue, leere Datenstruktur
        self.data["created"] = datetime.now().isoformat()
        self.data["reset_from_backup"] = backup_file.name
        
        self._save_data()
        
        return {
            "success": True,
            "message": "Nutzungsdaten zurückgesetzt",
            "backup_file": str(backup_file),
            "old_total_cost": old_data["total_usage"]["total_cost_usd"],
            "old_total_requests": old_data["total_usage"]["total_requests"],
        }
    
    def export_report(self, format: str = "json", output_path: Optional[str] = None) -> Dict:
        """
        Exportiert einen Nutzungsbericht.
        
        Args:
            format: Export-Format ("json", "csv", "text")
            output_path: Optionaler Ausgabepfad
            
        Returns:
            Dictionary mit Export-Informationen
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.data_dir / f"usage_report_{timestamp}.{format}"
        else:
            output_path = Path(output_path)
        
        report_data = {
            "generated": datetime.now().isoformat(),
            "period": "all_time",
            "summary": self.data["total_usage"],
            "monthly_summary": self.data["monthly_usage"],
            "skill_summary": self.data["skill_usage"],
            "model_summary": self.data["model_usage"],
            "settings": self.data["settings"],
        }
        
        try:
            if format == "json":
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            elif format == "csv":
                import csv
                
                # Erstelle CSV für monatliche Nutzung
                monthly_file = output_path.with_suffix('.monthly.csv')
                with open(monthly_file, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Month", "Total Tokens", "Input Tokens", "Output Tokens", "Cost (USD)", "Requests"])
                    
                    for month, data in self.data["monthly_usage"].items():
                        writer.writerow([
                            month,
                            data.get("total_tokens", 0),
                            data.get("input_tokens", 0),
                            data.get("output_tokens", 0),
                            f"{data.get('total_cost_usd', 0.0):.2f}",
                            data.get("requests", 0),
                        ])
                
                # Erstelle CSV für Skill-Nutzung
                skill_file = output_path.with_suffix('.skills.csv')
                with open(skill_file, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Skill Name", "Executions", "Total Tokens", "Input Tokens", "Output Tokens", "Cost (USD)", "First Used", "Last Used"])
                    
                    for skill_id, data in self.data["skill_usage"].items():
                        writer.writerow([
                            data.get("name", "Unknown"),
                            data.get("executions", 0),
                            data.get("total_tokens", 0),
                            data.get("input_tokens", 0),
                            data.get("output_tokens", 0),
                            f"{data.get('total_cost_usd', 0.0):.2f}",
                            data.get("first_used", ""),
                            data.get("last_used", ""),
                        ])
                
                output_path = monthly_file  # Rückgabe des Haupt-CSV-Files
            
            elif format == "text":
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write("=" * 60 + "\n")
                    f.write("LEHRERAGENT NUTZUNGSBERICHT\n")
                    f.write("=" * 60 + "\n\n")
                    
                    total = self.data["total_usage"]
                    f.write(f"Gesamtnutzung:\n")
                    f.write(f"  Total Tokens:      {total['total_tokens']:,}\n")
                    f.write(f"  Input Tokens:      {total['input_tokens']:,}\n")
                    f.write(f"  Output Tokens:     {total['output_tokens']:,}\n")
                    f.write(f"  Total Kosten:      ${total['total_cost_usd']:.2f}\n")
                    f.write(f"  Total Requests:    {total['total_requests']}\n")
                    f.write(f"  Skills ausgeführt: {total.get('total_skills_executed', 0)}\n\n")
                    
                    f.write("Monatliche Nutzung:\n")
                    for month in sorted(self.data["monthly_usage"].keys(), reverse=True)[:6]:  # Letzte 6 Monate
                        monthly = self.data["monthly_usage"][month]
                        f.write(f"  {month}: ${monthly['total_cost_usd']:.2f} ({monthly['total_tokens']:,} Tokens)\n")
                    
                    f.write("\nTop 5 Skills nach Kosten:\n")
                    skills_sorted = sorted(
                        self.data["skill_usage"].items(),
                        key=lambda x: x[1].get("total_cost_usd", 0),
                        reverse=True
                    )[:5]
                    
                    for skill_id, skill_data in skills_sorted:
                        f.write(f"  {skill_data.get('name', 'Unknown')}: ")
                        f.write(f"${skill_data.get('total_cost_usd', 0):.2f} ")
                        f.write(f"({skill_data.get('executions', 0)}x)\n")
            
            else:
                return {
                    "success": False,
                    "error": f"Unbekanntes Format: {format}",
                }
            
            return {
                "success": True,
                "message": f"Bericht exportiert als {format}",
                "output_path": str(output_path),
                "file_size": output_path.stat().st_size if output_path.exists() else 0,
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Export fehlgeschlagen: {e}",
            }


def main():
    """Hauptfunktion für Kommandozeilenaufruf."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Usage-Tracker für LehrerAgent")
    parser.add_argument("--track", action="store_true", help="Tracke Nutzung")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL, help="Modellname")
    parser.add_argument("--input-tokens", type=int, help="Anzahl Input-Tokens")
    parser.add_argument("--output-tokens", type=int, help="Anzahl Output-Tokens")
    parser.add_argument("--skill", type=str, help="Skill-Name")
    parser.add_argument("--request-id", type=str, help="Request-ID")
    
    parser.add_argument("--summary", action="store_true", help="Zeige Zusammenfassung")
    parser.add_argument("--period", type=str, default="total", help="Zeitraum (day, month, total, skill, model)")
    parser.add_argument("--period-key", type=str, help="Zeitraum-Schlüssel (z.B. '2024-01')")
    
    parser.add_argument("--estimate", action="store_true", help="Schätze Kosten")
    parser.add_argument("--estimated-input", type=int, help="Geschätzte Input-Tokens")
    parser.add_argument("--estimated-output", type=int, help="Geschätzte Output-Tokens")
    
    parser.add_argument("--export", action="store_true", help="Exportiere Bericht")
    parser.add_argument("--format", type=str, default="json", help="Export-Format (json, csv, text)")
    parser.add_argument("--output", type=str, help="Ausgabepfad")
    
    parser.add_argument("--reset", action="store_true", help="Setze Nutzungsdaten zurück")
    parser.add_argument("--confirm-reset", action="store_true", help="Bestätige Reset")
    
    args = parser.parse_args()
    
    tracker = UsageTracker()
    
    if args.track:
        if not args.input_tokens or not args.output_tokens:
            print("Fehler: --input-tokens und --output-tokens erforderlich für Tracking", file=sys.stderr)
            sys.exit(1)
        
        result = tracker.track_usage(
            model=args.model,
            input_tokens=args.input_tokens,
            output_tokens=args.output_tokens,
            skill_name=args.skill,
            request_id=args.request_id,
        )
        
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif args.summary:
        result = tracker.get_usage_summary(
            period=args.period,
            period_key=args.period_key,
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif args.estimate:
        if not args.estimated_input or not args.estimated_output:
            print("Fehler: --estimated-input und --estimated-output erforderlich", file=sys.stderr)
            sys.exit(1)
        
        result = tracker.get_cost_estimate(
            model=args.model,
            estimated_input_tokens=args.estimated_input,
            estimated_output_tokens=args.estimated_output,
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif args.export:
        result = tracker.export_report(
            format=args.format,
            output_path=args.output,
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif args.reset:
        result = tracker.reset_usage(confirm=args.confirm_reset)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    else:
        # Zeige Hilfe, wenn keine Aktion angegeben
        parser.print_help()


if __name__ == "__main__":
    main()