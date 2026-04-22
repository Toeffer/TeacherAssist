/// Offline Queue für LehrerAgent
/// Speichert Anfragen bei Netzwerkausfall und sendet sie beim Reconnect
library offline_queue;

import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:path_provider/path_provider.dart';
import '../config/app_config.dart';

/// Offline-Queue-Eintrag
class QueueEntry {
  /// Eindeutige ID
  final String id;

  /// Typ der Anfrage (z.B. 'chat_message', 'file_upload', 'tool_call')
  final String type;

  /// Daten der Anfrage (JSON-serialisierbar)
  final Map<String, dynamic> data;

  /// Zeitstempel der Erstellung
  final DateTime createdAt;

  /// Anzahl Versuche
  int attempts = 0;

  /// Letzter Versuch
  DateTime? lastAttempt;

  /// Fehlermeldung (falls vorhanden)
  String? error;

  /// Maximal erlaubte Versuche
  static const int maxAttempts = 3;

  /// Konstruktor
  QueueEntry({
    required this.id,
    required this.type,
    required this.data,
    DateTime? createdAt,
  }) : createdAt = createdAt ?? DateTime.now();

  /// Factory-Methode für neue Einträge
  factory QueueEntry.create({
    required String type,
    required Map<String, dynamic> data,
  }) {
    return QueueEntry(
      id: '${DateTime.now().millisecondsSinceEpoch}_${type}_${_generateRandomId()}',
      type: type,
      data: data,
    );
  }

  /// Aus Map erstellen
  factory QueueEntry.fromMap(Map<String, dynamic> map) {
    final entry = QueueEntry(
      id: map['id'],
      type: map['type'],
      data: Map<String, dynamic>.from(map['data']),
      createdAt: DateTime.parse(map['createdAt']),
    );
    entry.attempts = map['attempts'] ?? 0;
    entry.lastAttempt = map['lastAttempt'] != null ? DateTime.parse(map['lastAttempt']) : null;
    entry.error = map['error'];
    return entry;
  }

  /// Zu Map konvertieren
  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'type': type,
      'data': data,
      'createdAt': createdAt.toIso8601String(),
      'attempts': attempts,
      'lastAttempt': lastAttempt?.toIso8601String(),
      'error': error,
    };
  }

  /// Als JSON speichern
  String toJson() => json.encode(toMap());

  /// Aus JSON laden
  factory QueueEntry.fromJson(String jsonString) {
    return QueueEntry.fromMap(json.decode(jsonString));
  }

  /// Versuch registrieren
  void recordAttempt({String? error}) {
    attempts++;
    lastAttempt = DateTime.now();
    this.error = error;
  }

  /// Kann erneut versucht werden?
  bool get canRetry => attempts < maxAttempts;

  /// Ist abgelaufen? (älter als 7 Tage)
  bool get isExpired => createdAt.isBefore(DateTime.now().subtract(const Duration(days: 7)));

  @override
  String toString() {
    return 'QueueEntry($id, type: $type, attempts: $attempts/$maxAttempts)';
  }
}

/// Zufällige ID generieren
static String _generateRandomId() {
  return DateTime.now().microsecondsSinceEpoch.toRadixString(36).substring(0, 6);
}

/// Offline Queue
class OfflineQueue {
  /// App-Konfiguration
  final AppConfig config;

  /// Queue-Einträge
  final List<QueueEntry> _entries = [];

  /// Stream-Controller für Queue-Änderungen
  final StreamController<List<QueueEntry>> _queueController =
      StreamController<List<QueueEntry>>.broadcast();

  /// Dateipfad für persistente Speicherung
  late final String _storagePath;

  /// Timer für regelmäßige Bereinigung
  Timer? _cleanupTimer;

  /// Konstruktor
  OfflineQueue({required this.config});

  /// Queue-Stream
  Stream<List<QueueEntry>> get queueStream => _queueController.stream;

  /// Anzahl Einträge
  int get length => _entries.length;

  /// Ist leer?
  bool get isEmpty => _entries.isEmpty;

  /// Ist nicht leer?
  bool get isNotEmpty => _entries.isNotEmpty;

  /// Initialisierung
  Future<void> initialize() async {
    // Speicherpfad bestimmen
    final directory = await getApplicationDocumentsDirectory();
    _storagePath = '${directory.path}/lehreragent_offline_queue.json';

    // Gespeicherte Einträge laden
    await _loadFromStorage();

    // Bereinigungstimer starten
    _startCleanupTimer();

    // Logging
    if (config.debugMode) {
      print('OfflineQueue initialisiert: ${_entries.length} Einträge geladen');
    }
  }

  /// Eintrag hinzufügen
  Future<QueueEntry> add({
    required String type,
    required Map<String, dynamic> data,
  }) async {
    final entry = QueueEntry.create(type: type, data: data);
    _entries.add(entry);
    
    // Sortieren: älteste zuerst
    _entries.sort((a, b) => a.createdAt.compareTo(b.createdAt));
    
    // Speichern
    await _saveToStorage();
    
    // Event senden
    _queueController.add(List.from(_entries));
    
    // Logging
    if (config.debugMode) {
      print('OfflineQueue: Eintrag hinzugefügt: $entry');
    }
    
    return entry;
  }

  /// Nächsten Eintrag holen (ohne zu entfernen)
  QueueEntry? peek() {
    if (_entries.isEmpty) return null;
    
    // Suche ersten Eintrag, der noch versucht werden kann
    for (final entry in _entries) {
      if (entry.canRetry && !entry.isExpired) {
        return entry;
      }
    }
    
    return null;
  }

  /// Eintrag als erfolgreich markieren und entfernen
  Future<void> markAsSuccess(String id) async {
    final index = _entries.indexWhere((entry) => entry.id == id);
    if (index != -1) {
      _entries.removeAt(index);
      await _saveToStorage();
      _queueController.add(List.from(_entries));
      
      if (config.debugMode) {
        print('OfflineQueue: Eintrag $id als erfolgreich markiert');
      }
    }
  }

  /// Eintrag als fehlgeschlagen markieren
  Future<void> markAsFailed(String id, String error) async {
    final index = _entries.indexWhere((entry) => entry.id == id);
    if (index != -1) {
      final entry = _entries[index];
      entry.recordAttempt(error: error);
      
      // Wenn keine Versuche mehr übrig sind, entfernen
      if (!entry.canRetry) {
        _entries.removeAt(index);
        if (config.debugMode) {
          print('OfflineQueue: Eintrag $id entfernt (max. Versuche erreicht)');
        }
      }
      
      await _saveToStorage();
      _queueController.add(List.from(_entries));
      
      if (config.debugMode) {
        print('OfflineQueue: Eintrag $id als fehlgeschlagen markiert: $error');
      }
    }
  }

  /// Eintrag entfernen
  Future<void> remove(String id) async {
    final index = _entries.indexWhere((entry) => entry.id == id);
    if (index != -1) {
      _entries.removeAt(index);
      await _saveToStorage();
      _queueController.add(List.from(_entries));
    }
  }

  /// Alle Einträge löschen
  Future<void> clear() async {
    _entries.clear();
    await _saveToStorage();
    _queueController.add(List.from(_entries));
    
    if (config.debugMode) {
      print('OfflineQueue: Alle Einträge gelöscht');
    }
  }

  /// Abgelaufene Einträge bereinigen
  Future<void> cleanup() async {
    final initialLength = _entries.length;
    _entries.removeWhere((entry) => entry.isExpired);
    
    if (_entries.length < initialLength) {
      await _saveToStorage();
      _queueController.add(List.from(_entries));
      
      if (config.debugMode) {
        print('OfflineQueue: ${initialLength - _entries.length} abgelaufene Einträge bereinigt');
      }
    }
  }

  /// In Datei speichern
  Future<void> _saveToStorage() async {
    try {
      final file = File(_storagePath);
      final entriesJson = _entries.map((entry) => entry.toMap()).toList();
      await file.writeAsString(json.encode(entriesJson));
    } catch (e) {
      if (config.debugMode) {
        print('OfflineQueue: Fehler beim Speichern: $e');
      }
    }
  }

  /// Aus Datei laden
  Future<void> _loadFromStorage() async {
    try {
      final file = File(_storagePath);
      if (await file.exists()) {
        final content = await file.readAsString();
        final List<dynamic> entriesJson = json.decode(content);
        _entries.clear();
        _entries.addAll(entriesJson.map((json) => QueueEntry.fromMap(json)));
        
        // Abgelaufene Einträge direkt bereinigen
        await cleanup();
      }
    } catch (e) {
      if (config.debugMode) {
        print('OfflineQueue: Fehler beim Laden: $e');
      }
    }
  }

  /// Bereinigungstimer starten
  void _startCleanupTimer() {
    _cleanupTimer?.cancel();
    _cleanupTimer = Timer.periodic(
      const Duration(hours: 1),
      (_) => cleanup(),
    );
  }

  /// Queue-Statistiken
  Map<String, dynamic> getStatistics() {
    final now = DateTime.now();
    final pending = _entries.where((e) => e.canRetry && !e.isExpired).length;
    final expired = _entries.where((e) => e.isExpired).length;
    final failed = _entries.where((e) => !e.canRetry).length;
    
    return {
      'total': _entries.length,
      'pending': pending,
      'expired': expired,
      'failed': failed,
      'storagePath': _storagePath,
      'lastCleanup': _cleanupTimer?.isActive == true ? 'aktiv' : 'inaktiv',
      'types': _entries.fold<Map<String, int>>({}, (map, entry) {
        map[entry.type] = (map[entry.type] ?? 0) + 1;
        return map;
      }),
    };
  }

  /// Cleanup
  Future<void> dispose() async {
    _cleanupTimer?.cancel();
    await _queueController.close();
  }
}

/// Globaler Offline Queue
OfflineQueue? _globalOfflineQueue;

/// Globalen Offline Queue initialisieren
Future<OfflineQueue> initializeOfflineQueue(AppConfig config) async {
  _globalOfflineQueue = OfflineQueue(config: config);
  await _globalOfflineQueue!.initialize();
  return _globalOfflineQueue!;
}

/// Globalen Offline Queue abrufen
OfflineQueue get offlineQueue {
  if (_globalOfflineQueue == null) {
    throw StateError('OfflineQueue nicht initialisiert. Rufe initializeOfflineQueue() zuerst auf.');
  }
  return _globalOfflineQueue!;
}

/// Typische Queue-Einträge
class QueueEntryTypes {
  static const String chatMessage = 'chat_message';
  static const String fileUpload = 'file_upload';
  static const String toolCall = 'tool_call';
  static const String skillExecution = 'skill_execution';
}

/// Hilfsfunktion für Chat-Nachrichten
Future<QueueEntry> queueChatMessage({
  required String message,
  required String sender,
  Map<String, dynamic>? metadata,
}) async {
  return offlineQueue.add(
    type: QueueEntryTypes.chatMessage,
    data: {
      'message': message,
      'sender': sender,
      'timestamp': DateTime.now().toIso8601String(),
      'metadata': metadata ?? {},
    },
  );
}

/// Hilfsfunktion für Datei-Uploads
Future<QueueEntry> queueFileUpload({
  required String filePath,
  required String fileType,
  required String purpose,
  Map<String, dynamic>? metadata,
}) async {
  return offlineQueue.add(
    type: QueueEntryTypes.fileUpload,
    data: {
      'filePath': filePath,
      'fileType': fileType,
      'purpose': purpose,
      'timestamp': DateTime.now().toIso8601String(),
      'metadata': metadata ?? {},
    },
  );
}

/// Hilfsfunktion für Tool-Aufrufe
Future<QueueEntry> queueToolCall({
  required String toolName,
  required Map<String, dynamic> parameters,
  required String skillId,
}) async {
  return offlineQueue.add(
    type: QueueEntryTypes.toolCall,
    data: {
      'toolName': toolName,
      'parameters': parameters,
      'skillId': skillId,
      'timestamp': DateTime.now().toIso8601String(),
    },
  );
}