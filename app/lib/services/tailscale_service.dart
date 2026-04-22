/// Tailscale Service für LehrerAgent
/// Verwaltet Tailscale VPN-Verbindungen und Statusüberwachung
library tailscale_service;

import 'dart:async';
import 'dart:io';
import 'package:flutter/foundation.dart';

/// Tailscale Verbindungsstatus
enum TailscaleStatus {
  disconnected,    // Nicht verbunden
  connecting,     // Verbindung wird aufgebaut
  connected,      // Erfolgreich verbunden
  error,          // Fehler bei der Verbindung
  notInstalled,   // Tailscale nicht installiert
}

/// Tailscale Node Information
class TailscaleNode {
  final String hostname;
  final String ipAddress;
  final bool isOnline;
  final DateTime lastSeen;

  TailscaleNode({
    required this.hostname,
    required this.ipAddress,
    required this.isOnline,
    required this.lastSeen,
  });

  factory TailscaleNode.fromJson(Map<String, dynamic> json) {
    return TailscaleNode(
      hostname: json['hostname'],
      ipAddress: json['ipAddress'],
      isOnline: json['isOnline'],
      lastSeen: DateTime.parse(json['lastSeen']),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'hostname': hostname,
      'ipAddress': ipAddress,
      'isOnline': isOnline,
      'lastSeen': lastSeen.toIso8601String(),
    };
  }
}

/// Haupt-Tailscale-Service
class TailscaleService {
  static final TailscaleService _instance = TailscaleService._internal();
  factory TailscaleService() => _instance;
  TailscaleService._internal();

  TailscaleStatus _currentStatus = TailscaleStatus.disconnected;
  StreamController<TailscaleStatus> _statusStream = StreamController.broadcast();
  StreamController<List<TailscaleNode>> _nodesStream = StreamController.broadcast();
  Timer? _statusPollTimer;
  bool _initialized = false;

  /// Aktueller Status
  TailscaleStatus get currentStatus => _currentStatus;

  /// Status-Stream
  Stream<TailscaleStatus> get statusStream => _statusStream.stream;

  /// Nodes-Stream
  Stream<List<TailscaleNode>> get nodesStream => _nodesStream.stream;

  /// Initialisierung
  Future<void> initialize() async {
    if (_initialized) return;

    // Tailscale Installation prüfen
    final isInstalled = await _checkTailscaleInstallation();
    if (!isInstalled) {
      _currentStatus = TailscaleStatus.notInstalled;
      _statusStream.add(_currentStatus);
      debugPrint('Tailscale ist nicht installiert');
      return;
    }

    // Initialen Status abrufen
    await _updateStatus();

    // Status-Polling starten (alle 30 Sekunden)
    _statusPollTimer = Timer.periodic(
      Duration(seconds: 30),
      (_) => _updateStatus(),
    );

    _initialized = true;
    debugPrint('Tailscale Service initialisiert');
  }

  /// Tailscale Installation prüfen
  Future<bool> _checkTailscaleInstallation() async {
    try {
      if (Platform.isWindows) {
        final result = await Process.run('where', ['tailscale']);
        return result.exitCode == 0;
      } else if (Platform.isMacOS || Platform.isLinux) {
        final result = await Process.run('which', ['tailscale']);
        return result.exitCode == 0;
      }
      return false;
    } catch (e) {
      debugPrint('Fehler bei Tailscale-Installationsprüfung: $e');
      return false;
    }
  }

  /// Status aktualisieren
  Future<void> _updateStatus() async {
    try {
      final previousStatus = _currentStatus;
      
      // Tailscale Status abrufen
      final result = await Process.run('tailscale', ['status', '--json']);
      
      if (result.exitCode != 0) {
        _currentStatus = TailscaleStatus.error;
        debugPrint('Tailscale Status-Fehler: ${result.stderr}');
      } else {
        final statusJson = result.stdout as String;
        final statusData = _parseStatusJson(statusJson);
        
        if (statusData['BackendState'] == 'Running') {
          _currentStatus = TailscaleStatus.connected;
          
          // Nodes aktualisieren
          final nodes = _parseNodesFromStatus(statusData);
          _nodesStream.add(nodes);
        } else {
          _currentStatus = TailscaleStatus.disconnected;
        }
      }
      
      // Status-Änderung melden
      if (previousStatus != _currentStatus) {
        _statusStream.add(_currentStatus);
        debugPrint('Tailscale Status geändert: $previousStatus → $_currentStatus');
      }
    } catch (e) {
      debugPrint('Fehler beim Aktualisieren des Tailscale-Status: $e');
      _currentStatus = TailscaleStatus.error;
      _statusStream.add(_currentStatus);
    }
  }

  /// Tailscale Status JSON parsen
  Map<String, dynamic> _parseStatusJson(String jsonString) {
    try {
      // Einfache JSON-Parsing (ohne external package)
      final cleaned = jsonString
          .replaceAll('\\', '')
          .replaceAll('\n', '')
          .replaceAll('\r', '');
      
      final Map<String, dynamic> result = {};
      final lines = cleaned.split(',');
      
      for (var line in lines) {
        final parts = line.split(':');
        if (parts.length == 2) {
          final key = parts[0].trim().replaceAll('"', '');
          final value = parts[1].trim().replaceAll('"', '');
          result[key] = value;
        }
      }
      
      return result;
    } catch (e) {
      debugPrint('Fehler beim Parsen des Tailscale-Status: $e');
      return {};
    }
  }

  /// Nodes aus Status-Daten parsen
  List<TailscaleNode> _parseNodesFromStatus(Map<String, dynamic> statusData) {
    final nodes = <TailscaleNode>[];
    
    try {
      // Tailscale Status enthält Peer-Informationen
      // Hier müsste die tatsächliche Parsing-Logik implementiert werden
      // basierend auf der tatsächlichen Tailscale Status-Ausgabe
      
      // Beispiel-Node für Demo-Zwecke
      nodes.add(TailscaleNode(
        hostname: 'openclaw-server',
        ipAddress: '100.64.0.1',
        isOnline: true,
        lastSeen: DateTime.now(),
      ));
      
    } catch (e) {
      debugPrint('Fehler beim Parsen der Nodes: $e');
    }
    
    return nodes;
  }

  /// Tailscale verbinden
  Future<bool> connect() async {
    try {
      _currentStatus = TailscaleStatus.connecting;
      _statusStream.add(_currentStatus);
      
      final result = await Process.run('tailscale', ['up']);
      
      if (result.exitCode == 0) {
        await _updateStatus();
        return _currentStatus == TailscaleStatus.connected;
      } else {
        _currentStatus = TailscaleStatus.error;
        _statusStream.add(_currentStatus);
        debugPrint('Tailscale Verbindungsfehler: ${result.stderr}');
        return false;
      }
    } catch (e) {
      _currentStatus = TailscaleStatus.error;
      _statusStream.add(_currentStatus);
      debugPrint('Fehler bei Tailscale-Verbindung: $e');
      return false;
    }
  }

  /// Tailscale trennen
  Future<bool> disconnect() async {
    try {
      final result = await Process.run('tailscale', ['down']);
      
      if (result.exitCode == 0) {
        _currentStatus = TailscaleStatus.disconnected;
        _statusStream.add(_currentStatus);
        return true;
      } else {
        debugPrint('Tailscale Trennung fehlgeschlagen: ${result.stderr}');
        return false;
      }
    } catch (e) {
      debugPrint('Fehler bei Tailscale-Trennung: $e');
      return false;
    }
  }

  /// Tailscale Login-URL abrufen
  Future<String?> getLoginUrl() async {
    try {
      final result = await Process.run('tailscale', ['up', '--login-server', 'https://login.tailscale.com', '--qr']);
      
      if (result.exitCode == 0) {
        final output = result.stdout as String;
        // URL aus der Ausgabe extrahieren
        final urlMatch = RegExp(r'https://login\.tailscale\.com/admin/machines/[^\s]+').firstMatch(output);
        return urlMatch?.group(0);
      }
      return null;
    } catch (e) {
      debugPrint('Fehler beim Abrufen der Login-URL: $e');
      return null;
    }
  }

  /// Tailscale Netzwerk-Informationen abrufen
  Future<Map<String, dynamic>> getNetworkInfo() async {
    try {
      final result = await Process.run('tailscale', ['status', '--json']);
      
      if (result.exitCode == 0) {
        final statusJson = result.stdout as String;
        final statusData = _parseStatusJson(statusJson);
        
        return {
          'status': _currentStatus.toString(),
          'backendState': statusData['BackendState'] ?? 'Unknown',
          'magicDNS': statusData['MagicDNS'] ?? false,
          'tailscaleVersion': statusData['Version'] ?? 'Unknown',
          'lastUpdate': DateTime.now().toIso8601String(),
        };
      }
      
      return {'error': 'Tailscale Status konnte nicht abgerufen werden'};
    } catch (e) {
      return {'error': 'Fehler: $e'};
    }
  }

  /// Service beenden
  Future<void> dispose() async {
    _statusPollTimer?.cancel();
    await _statusStream.close();
    await _nodesStream.close();
  }
}

/// Globale Tailscale Service Instanz
final tailscaleService = TailscaleService();