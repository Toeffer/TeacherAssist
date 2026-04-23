/// OpenClaw Service für LehrerAgent
/// WebSocket-Client für die Kommunikation mit OpenClaw Server
library openclaw_service;

import 'dart:async';
import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:web_socket_channel/io.dart';
import 'package:flutter/foundation.dart';
import '../config/app_config.dart';

// Globale appConfig-Instanz aus app_config.dart ist direkt verfügbar

/// OpenClaw Nachrichtentypen
enum OpenClawMessageType {
  skillRequest,    // Skill-Ausführung anfordern
  skillResponse,   // Skill-Antwort
  toolCall,        // Tool-Aufruf
  toolResponse,    // Tool-Antwort
  statusUpdate,    // Status-Update
  error,           // Fehler
  ping,            // Ping (Keep-Alive)
  pong,            // Pong (Keep-Alive Antwort)
}

/// OpenClaw Nachricht
class OpenClawMessage {
  final String id;
  final OpenClawMessageType type;
  final Map<String, dynamic> data;
  final DateTime timestamp;
  final String? correlationId;

  OpenClawMessage({
    required this.id,
    required this.type,
    required this.data,
    required this.timestamp,
    this.correlationId,
  });

  factory OpenClawMessage.fromJson(Map<String, dynamic> json) {
    return OpenClawMessage(
      id: json['id'],
      type: OpenClawMessageType.values.firstWhere(
        (e) => e.toString() == json['type'],
        orElse: () => OpenClawMessageType.error,
      ),
      data: json['data'] ?? {},
      timestamp: DateTime.parse(json['timestamp']),
      correlationId: json['correlationId'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'type': type.toString(),
      'data': data,
      'timestamp': timestamp.toIso8601String(),
      if (correlationId != null) 'correlationId': correlationId,
    };
  }

  String toJsonString() => jsonEncode(toJson());
}

/// OpenClaw Service Status
enum OpenClawServiceStatus {
  disconnected,    // Nicht verbunden
  connecting,      // Verbindung wird aufgebaut
  connected,       // Erfolgreich verbunden
  reconnecting,    // Wiederverbindung wird versucht
  error,           // Fehler
}

/// OpenClaw Service
class OpenClawService {
  static final OpenClawService _instance = OpenClawService._internal();
  factory OpenClawService() => _instance;
  OpenClawService._internal();

  WebSocketChannel? _channel;
  OpenClawServiceStatus _currentStatus = OpenClawServiceStatus.disconnected;
  StreamController<OpenClawServiceStatus> _statusStream = StreamController.broadcast();
  StreamController<OpenClawMessage> _messageStream = StreamController.broadcast();
  Timer? _pingTimer;
  Timer? _reconnectTimer;
  int _reconnectAttempts = 0;
  final int _maxReconnectAttempts = 10;
  final Map<String, Completer<OpenClawMessage>> _pendingRequests = {};
  bool _initialized = false;

  /// Aktueller Status
  OpenClawServiceStatus get currentStatus => _currentStatus;

  /// Status-Stream
  Stream<OpenClawServiceStatus> get statusStream => _statusStream.stream;

  /// Nachrichten-Stream
  Stream<OpenClawMessage> get messageStream => _messageStream.stream;

  /// Initialisierung
  Future<void> initialize(AppConfig config) async {
    if (_initialized) return;
    
    _initialized = true;
    await _connect(config);
  }

  /// Verbindung herstellen
  Future<void> _connect(AppConfig config) async {
    try {
      _updateStatus(OpenClawServiceStatus.connecting);
      
      final url = config.websocketUrl;
      debugPrint('Verbinde zu OpenClaw: $url');
      
      _channel = IOWebSocketChannel.connect(
        url,
        pingInterval: const Duration(seconds: 30),
      );
      
      // Nachrichten-Listener
      _channel!.stream.listen(
        _handleMessage,
        onError: _handleError,
        onDone: _handleDisconnect,
      );
      
      _updateStatus(OpenClawServiceStatus.connected);
      _reconnectAttempts = 0;
      
      // Ping-Timer starten
      _startPingTimer();
      
      debugPrint('OpenClaw Verbindung erfolgreich');
    } catch (e) {
      debugPrint('OpenClaw Verbindungsfehler: $e');
      _updateStatus(OpenClawServiceStatus.error);
      _scheduleReconnect(config);
    }
  }

  /// Status aktualisieren
  void _updateStatus(OpenClawServiceStatus newStatus) {
    if (_currentStatus != newStatus) {
      _currentStatus = newStatus;
      _statusStream.add(newStatus);
      debugPrint('OpenClaw Status: $newStatus');
    }
  }

  /// Nachricht verarbeiten
  void _handleMessage(dynamic message) {
    try {
      final json = jsonDecode(message as String);
      final openClawMessage = OpenClawMessage.fromJson(json);
      
      debugPrint('OpenClaw Nachricht empfangen: ${openClawMessage.type}');
      
      // Korrelierte Antwort verarbeiten
      if (openClawMessage.correlationId != null &&
          _pendingRequests.containsKey(openClawMessage.correlationId)) {
        final completer = _pendingRequests[openClawMessage.correlationId]!;
        completer.complete(openClawMessage);
        _pendingRequests.remove(openClawMessage.correlationId);
      }
      
      // An Stream senden
      _messageStream.add(openClawMessage);
    } catch (e) {
      debugPrint('Fehler beim Verarbeiten der OpenClaw-Nachricht: $e');
    }
  }

  /// Fehler behandeln
  void _handleError(dynamic error) {
    debugPrint('OpenClaw WebSocket Fehler: $error');
    _updateStatus(OpenClawServiceStatus.error);
  }

  /// Verbindungsabbruch behandeln
  void _handleDisconnect() {
    debugPrint('OpenClaw Verbindung getrennt');
    _updateStatus(OpenClawServiceStatus.disconnected);
    _stopPingTimer();
    
    // Automatische Wiederherstellung versuchen
    if (_initialized) {
      _updateStatus(OpenClawServiceStatus.reconnecting);
      _scheduleReconnect(appConfig);
    }
  }

  /// Skill ausführen
  Future<OpenClawMessage> executeSkill({
    required String skillName,
    required Map<String, dynamic> parameters,
    String? messageId,
  }) async {
    final id = messageId ?? _generateMessageId();
    final completer = Completer<OpenClawMessage>();
    
    _pendingRequests[id] = completer;
    
    final message = OpenClawMessage(
      id: id,
      type: OpenClawMessageType.skillRequest,
      data: {
        'skill': skillName,
        'parameters': parameters,
      },
      timestamp: DateTime.now(),
    );
    
    await _sendMessage(message);
    
    // Timeout nach 60 Sekunden
    return completer.future.timeout(
      const Duration(seconds: 60),
      onTimeout: () {
        _pendingRequests.remove(id);
        throw TimeoutException('Skill-Ausführung timeout nach 60 Sekunden');
      },
    );
  }

  /// Tool aufrufen
  Future<OpenClawMessage> callTool({
    required String toolName,
    required Map<String, dynamic> parameters,
    String? messageId,
  }) async {
    final id = messageId ?? _generateMessageId();
    final completer = Completer<OpenClawMessage>();
    
    _pendingRequests[id] = completer;
    
    final message = OpenClawMessage(
      id: id,
      type: OpenClawMessageType.toolCall,
      data: {
        'tool': toolName,
        'parameters': parameters,
      },
      timestamp: DateTime.now(),
    );
    
    await _sendMessage(message);
    
    // Timeout nach 30 Sekunden
    return completer.future.timeout(
      const Duration(seconds: 30),
      onTimeout: () {
        _pendingRequests.remove(id);
        throw TimeoutException('Tool-Aufruf timeout nach 30 Sekunden');
      },
    );
  }

  /// Nachricht senden
  Future<void> _sendMessage(OpenClawMessage message) async {
    if (_channel == null || _currentStatus != OpenClawServiceStatus.connected) {
      throw Exception('OpenClaw nicht verbunden');
    }
    
    try {
      final jsonString = message.toJsonString();
      _channel!.sink.add(jsonString);
      debugPrint('OpenClaw Nachricht gesendet: ${message.type}');
    } catch (e) {
      debugPrint('Fehler beim Senden der OpenClaw-Nachricht: $e');
      throw Exception('Nachricht konnte nicht gesendet werden: $e');
    }
  }

  /// Ping-Timer starten
  void _startPingTimer() {
    _pingTimer?.cancel();
    _pingTimer = Timer.periodic(
      const Duration(seconds: 25),
      (_) => _sendPing(),
    );
  }

  /// Ping senden
  void _sendPing() {
    if (_channel == null || _currentStatus != OpenClawServiceStatus.connected) {
      return;
    }
    
    try {
      final pingMessage = OpenClawMessage(
        id: _generateMessageId(),
        type: OpenClawMessageType.ping,
        data: {'timestamp': DateTime.now().toIso8601String()},
        timestamp: DateTime.now(),
      );
      
      _channel!.sink.add(pingMessage.toJsonString());
    } catch (e) {
      debugPrint('Fehler beim Senden des Pings: $e');
    }
  }

  /// Ping-Timer stoppen
  void _stopPingTimer() {
    _pingTimer?.cancel();
    _pingTimer = null;
  }

  /// Wiederverbindung planen
  void _scheduleReconnect(AppConfig config) {
    if (_reconnectAttempts >= _maxReconnectAttempts) {
      debugPrint('Maximale Wiederverbindungsversuche erreicht');
      return;
    }
    
    _reconnectTimer?.cancel();
    
    // Exponential Backoff: 1s, 2s, 4s, 8s, 16s, 32s, max 60s
    final delay = Duration(seconds: 1 << _reconnectAttempts).inSeconds;
    final backoff = Duration(seconds: delay > 60 ? 60 : delay);
    
    _reconnectTimer = Timer(
      backoff,
      () => _reconnect(config),
    );
    
    _reconnectAttempts++;
    debugPrint('Wiederverbindung in ${backoff.inSeconds} Sekunden (Versuch $_reconnectAttempts)');
  }

  /// Wiederverbindung versuchen
  Future<void> _reconnect(AppConfig config) async {
    if (_currentStatus == OpenClawServiceStatus.connected) {
      return;
    }
    
    debugPrint('Versuche Wiederverbindung zu OpenClaw...');
    await _connect(config);
  }

  /// Nachrichten-ID generieren
  String _generateMessageId() {
    return 'msg_${DateTime.now().millisecondsSinceEpoch}_${_pendingRequests.length}';
  }

  /// Verfügbare Skills abrufen
  Future<List<Map<String, dynamic>>> getAvailableSkills() async {
    try {
      final response = await executeSkill(
        skillName: 'list_skills',
        parameters: {},
      );
      
      if (response.type == OpenClawMessageType.skillResponse &&
          response.data['skills'] is List) {
        return List<Map<String, dynamic>>.from(response.data['skills']);
      }
      
      return [];
    } catch (e) {
      debugPrint('Fehler beim Abrufen der Skills: $e');
      return [];
    }
  }

  /// Verfügbare Tools abrufen
  Future<List<Map<String, dynamic>>> getAvailableTools() async {
    try {
      final response = await executeSkill(
        skillName: 'list_tools',
        parameters: {},
      );
      
      if (response.type == OpenClawMessageType.skillResponse &&
          response.data['tools'] is List) {
        return List<Map<String, dynamic>>.from(response.data['tools']);
      }
      
      return [];
    } catch (e) {
      debugPrint('Fehler beim Abrufen der Tools: $e');
      return [];
    }
  }

  /// Verbindung trennen
  Future<void> disconnect() async {
    _reconnectTimer?.cancel();
    _stopPingTimer();
    
    if (_channel != null) {
      await _channel!.sink.close();
      _channel = null;
    }
    
    _updateStatus(OpenClawServiceStatus.disconnected);
    _initialized = false;
    
    // Alle ausstehenden Requests abbrechen
    for (final completer in _pendingRequests.values) {
      if (!completer.isCompleted) {
        completer.completeError(Exception('Verbindung getrennt'));
      }
    }
    _pendingRequests.clear();
    
    debugPrint('OpenClaw Service beendet');
  }

  /// Service beenden
  Future<void> dispose() async {
    await disconnect();
    await _statusStream.close();
    await _messageStream.close();
  }
}

/// Globale OpenClaw Service Instanz
final openClawService = OpenClawService();