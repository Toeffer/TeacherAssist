/// Connection Manager für LehrerAgent
/// Verwaltet Netzwerkverbindungen mit Priorität: WLAN → Tailscale → Offline
library connection_manager;

import 'dart:async';
import 'dart:io';
import 'package:connectivity_plus/connectivity_plus.dart';
import '../config/app_config.dart';

/// Verbindungsstatus
enum ConnectionStatus {
  /// Vollständig verbunden (OpenClaw erreichbar)
  connected,

  /// Verbindung zu OpenClaw getrennt
  disconnected,

  /// Offline-Modus (keine Netzwerkverbindung)
  offline,

  /// Tailscale-Verbindung aktiv
  tailscale,

  /// Lokale WLAN-Verbindung
  localWifi,
}

/// Verbindungs-Event
class ConnectionEvent {
  /// Neuer Status
  final ConnectionStatus status;

  /// Vorheriger Status
  final ConnectionStatus previousStatus;

  /// Fehlermeldung (falls vorhanden)
  final String? error;

  /// Zeitstempel
  final DateTime timestamp;

  /// Konstruktor
  ConnectionEvent({
    required this.status,
    required this.previousStatus,
    this.error,
    DateTime? timestamp,
  }) : timestamp = timestamp ?? DateTime.now();

  @override
  String toString() {
    return 'ConnectionEvent($status, prev: $previousStatus, error: $error)';
  }
}

/// Connection Manager
class ConnectionManager {
  /// App-Konfiguration
  final AppConfig config;

  /// Connectivity Plugin
  final Connectivity _connectivity = Connectivity();

  /// Aktueller Status
  ConnectionStatus _currentStatus = ConnectionStatus.disconnected;

  /// Stream-Controller für Status-Änderungen
  final StreamController<ConnectionEvent> _statusController =
      StreamController<ConnectionEvent>.broadcast();

  /// Timer für regelmäßige Prüfungen
  Timer? _checkTimer;

  /// Letzte erfolgreiche Prüfung
  DateTime? _lastSuccessfulCheck;

  /// Anzahl fehlgeschlagener Prüfungen
  int _failedChecks = 0;

  /// Maximal erlaubte fehlgeschlagene Prüfungen
  static const int maxFailedChecks = 3;

  /// Prüf-Intervall in Sekunden
  static const int checkIntervalSeconds = 30;

  /// Konstruktor
  ConnectionManager({required this.config});

  /// Status-Stream
  Stream<ConnectionEvent> get statusStream => _statusController.stream;

  /// Aktueller Status
  ConnectionStatus get currentStatus => _currentStatus;

  /// Ist verbunden? (lokal, Tailscale oder direkt)
  bool get isConnected =>
      _currentStatus == ConnectionStatus.connected ||
      _currentStatus == ConnectionStatus.localWifi ||
      _currentStatus == ConnectionStatus.tailscale;

  /// Ist offline?
  bool get isOffline => _currentStatus == ConnectionStatus.offline;

  /// Initialisierung
  Future<void> initialize() async {
    // Initialen Status prüfen
    await _checkConnection();

    // Listener für Netzwerk-Änderungen (connectivity_plus v5: List)
    _connectivity.onConnectivityChanged.listen((results) {
      _handleConnectivityChange(results);
    });

    // Timer für regelmäßige Prüfungen starten
    _startCheckTimer();
  }

  /// Timer starten
  void _startCheckTimer() {
    _checkTimer?.cancel();
    _checkTimer = Timer.periodic(
      Duration(seconds: checkIntervalSeconds),
      (_) => _checkConnection(),
    );
  }

  /// Netzwerk-Änderung behandeln (connectivity_plus v5: List)
  Future<void> _handleConnectivityChange(List<ConnectivityResult> results) async {
    final isOffline = results.isEmpty ||
        results.every((r) => r == ConnectivityResult.none);
    if (isOffline) {
      await _updateStatus(ConnectionStatus.offline);
    } else {
      await _checkConnection();
    }
  }

  /// Verbindung prüfen
  Future<void> _checkConnection() async {
    try {
      // Netzwerk-Verfügbarkeit prüfen (connectivity_plus v5: List)
      final connectivityResults = await _connectivity.checkConnectivity();
      final isOffline = connectivityResults.isEmpty ||
          connectivityResults.every((r) => r == ConnectivityResult.none);

      if (isOffline) {
        await _updateStatus(ConnectionStatus.offline);
        return;
      }

      // Priorität 1: Lokales WLAN (falls konfiguriert)
      if (config.isLocalConnection) {
        final localReachable = await _isHostReachable(config.openClawHost, config.openClawPort);
        if (localReachable) {
          await _updateStatus(ConnectionStatus.localWifi);
          return;
        }
      }

      // Priorität 2: Tailscale (falls konfiguriert)
      if (config.usesTailscale) {
        final tailscaleReachable = await _isHostReachable(
          config.tailscaleHostname!,
          config.openClawPort,
        );
        if (tailscaleReachable) {
          await _updateStatus(ConnectionStatus.tailscale);
          return;
        }
      }

      // Priorität 3: Konfigurierter Host (Fallback)
      final hostReachable = await _isHostReachable(config.openClawHost, config.openClawPort);
      if (hostReachable) {
        await _updateStatus(ConnectionStatus.connected);
      } else {
        await _updateStatus(ConnectionStatus.disconnected,
            error: 'OpenClaw nicht erreichbar');
      }
    } catch (e) {
      await _updateStatus(ConnectionStatus.disconnected, error: e.toString());
    }
  }

  /// Host erreichbar prüfen
  Future<bool> _isHostReachable(String host, int port) async {
    try {
      final socket = await Socket.connect(host, port, timeout: const Duration(seconds: 5));
      socket.destroy();
      _failedChecks = 0; // Reset failed checks
      _lastSuccessfulCheck = DateTime.now();
      return true;
    } catch (e) {
      _failedChecks++;
      return false;
    }
  }

  /// Status aktualisieren
  Future<void> _updateStatus(ConnectionStatus newStatus, {String? error}) async {
    final previousStatus = _currentStatus;
    
    // Nur aktualisieren wenn sich etwas geändert hat
    if (newStatus == _currentStatus && error == null) {
      return;
    }

    _currentStatus = newStatus;

    // Event senden
    final event = ConnectionEvent(
      status: newStatus,
      previousStatus: previousStatus,
      error: error,
    );

    _statusController.add(event);

    // Logging (nur im Debug-Modus)
    if (config.debugMode) {
      print('ConnectionManager: $event');
    }

    // Bei zu vielen fehlgeschlagenen Prüfungen: Offline-Modus
    if (_failedChecks >= maxFailedChecks && newStatus != ConnectionStatus.offline) {
      await _updateStatus(ConnectionStatus.offline,
          error: 'Zu viele fehlgeschlagene Verbindungsversuche');
    }
  }

  /// Manuelle Verbindungsprüfung
  Future<ConnectionEvent> checkConnectionManually() async {
    await _checkConnection();
    return ConnectionEvent(
      status: _currentStatus,
      previousStatus: _currentStatus,
    );
  }

  /// Beste verfügbare URL zurückgeben
  String getBestAvailableUrl() {
    switch (_currentStatus) {
      case ConnectionStatus.localWifi:
      case ConnectionStatus.connected:
        return config.websocketUrl;
      case ConnectionStatus.tailscale:
        return 'ws://${config.tailscaleHostname}:${config.openClawPort}';
      case ConnectionStatus.disconnected:
      case ConnectionStatus.offline:
        // Fallback auf konfigurierte URL (wird wahrscheinlich fehlschlagen)
        return config.websocketUrl;
    }
  }

  /// Verbindungs-Statistiken
  Map<String, dynamic> getStatistics() {
    return {
      'currentStatus': _currentStatus.toString(),
      'failedChecks': _failedChecks,
      'lastSuccessfulCheck': _lastSuccessfulCheck?.toIso8601String(),
      'maxFailedChecks': maxFailedChecks,
      'checkIntervalSeconds': checkIntervalSeconds,
      'config': {
        'host': config.openClawHost,
        'port': config.openClawPort,
        'tailscale': config.tailscaleHostname,
        'isLocal': config.isLocalConnection,
      },
    };
  }

  /// Cleanup
  Future<void> dispose() async {
    _checkTimer?.cancel();
    _statusController.close();
  }
}

/// Globaler Connection Manager
ConnectionManager? _globalConnectionManager;

/// Globalen Connection Manager initialisieren
Future<ConnectionManager> initializeConnectionManager(AppConfig config) async {
  _globalConnectionManager = ConnectionManager(config: config);
  await _globalConnectionManager!.initialize();
  return _globalConnectionManager!;
}

/// Globalen Connection Manager abrufen
ConnectionManager get connectionManager {
  if (_globalConnectionManager == null) {
    throw StateError('ConnectionManager nicht initialisiert. Rufe initializeConnectionManager() zuerst auf.');
  }
  return _globalConnectionManager!;
}