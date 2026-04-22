/// App-Konfiguration für LehrerAgent
/// Lädt Konfiguration aus Umgebungsvariablen mit Fallbacks
library app_config;

import 'dart:io';

/// Hauptkonfigurationsklasse
class AppConfig {
  /// OpenClaw Server Host
  final String openClawHost;

  /// OpenClaw Server Port
  final int openClawPort;

  /// Tailscale Hostname (falls verwendet)
  final String? tailscaleHostname;

  /// App-Version
  final String appVersion;

  /// Debug-Modus
  final bool debugMode;

  /// Maximale Dateigröße für Uploads (in Bytes)
  final int maxFileSizeBytes;

  /// Timeout für WebSocket-Verbindungen (in Sekunden)
  final int websocketTimeoutSeconds;

  /// Reconnect-Interval (in Sekunden)
  final int reconnectIntervalSeconds;

  /// Maximaler Reconnect-Versuch
  final int maxReconnectAttempts;

  AppConfig({
    required this.openClawHost,
    required this.openClawPort,
    this.tailscaleHostname,
    required this.appVersion,
    required this.debugMode,
    required this.maxFileSizeBytes,
    required this.websocketTimeoutSeconds,
    required this.reconnectIntervalSeconds,
    required this.maxReconnectAttempts,
  });

  /// Factory-Methode, die Konfiguration aus Umgebungsvariablen lädt
  factory AppConfig.fromEnvironment() {
    // Host-Konfiguration
    final host = Platform.environment['OPENCLAW_HOST'] ??
        (Platform.isAndroid || Platform.isIOS
            ? '192.168.1.100' // Standard-LAN-IP für Mobile
            : 'localhost');

    // Port-Konfiguration
    final port = int.tryParse(Platform.environment['OPENCLAW_PORT'] ?? '18789') ?? 18789;

    // Tailscale-Konfiguration
    final tailscaleHost = Platform.environment['TAILSCALE_HOSTNAME'];

    // Debug-Modus
    final debug = Platform.environment['DEBUG_MODE']?.toLowerCase() == 'true' ||
        const bool.fromEnvironment('DEBUG', defaultValue: false);

    // App-Version
    const version = String.fromEnvironment('APP_VERSION', defaultValue: '1.0.0');

    return AppConfig(
      openClawHost: host,
      openClawPort: port,
      tailscaleHostname: tailscaleHost,
      appVersion: version,
      debugMode: debug,
      maxFileSizeBytes: 10 * 1024 * 1024, // 10 MB
      websocketTimeoutSeconds: 30,
      reconnectIntervalSeconds: 5,
      maxReconnectAttempts: 10,
    );
  }

  /// WebSocket-URL basierend auf aktueller Konfiguration
  String get websocketUrl {
    if (tailscaleHostname != null && tailscaleHostname!.isNotEmpty) {
      // Tailscale-Verbindung
      return 'ws://$tailscaleHostname:$openClawPort';
    } else {
      // Direkte LAN-Verbindung
      return 'ws://$openClawHost:$openClawPort';
    }
  }

  /// HTTP-URL für API-Aufrufe
  String get httpUrl {
    if (tailscaleHostname != null && tailscaleHostname!.isNotEmpty) {
      return 'http://$tailscaleHostname:$openClawPort';
    } else {
      return 'http://$openClawHost:$openClawPort';
    }
  }

  /// Gibt an, ob Tailscale verwendet wird
  bool get usesTailscale => tailscaleHostname != null && tailscaleHostname!.isNotEmpty;

  /// Gibt an, ob lokale Verbindung (localhost/LAN)
  bool get isLocalConnection {
    return openClawHost == 'localhost' ||
        openClawHost == '127.0.0.1' ||
        openClawHost.startsWith('192.168.') ||
        openClawHost.startsWith('10.');
  }

  /// Konfiguration als Map für Debugging
  Map<String, dynamic> toMap() {
    return {
      'openClawHost': openClawHost,
      'openClawPort': openClawPort,
      'tailscaleHostname': tailscaleHostname,
      'appVersion': appVersion,
      'debugMode': debugMode,
      'maxFileSizeBytes': maxFileSizeBytes,
      'websocketTimeoutSeconds': websocketTimeoutSeconds,
      'reconnectIntervalSeconds': reconnectIntervalSeconds,
      'maxReconnectAttempts': maxReconnectAttempts,
      'websocketUrl': websocketUrl,
      'httpUrl': httpUrl,
      'usesTailscale': usesTailscale,
      'isLocalConnection': isLocalConnection,
    };
  }

  @override
  String toString() {
    return 'AppConfig${toMap()}';
  }
}

/// Globale App-Konfigurationsinstanz
final appConfig = AppConfig.fromEnvironment();