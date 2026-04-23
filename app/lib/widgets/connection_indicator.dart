/// Connection Indicator Widget für LehrerAgent
/// Zeigt Netzwerk- und Verbindungsstatus an
library connection_indicator;

import 'dart:async';
import 'package:flutter/material.dart';
import '../services/connection_manager.dart';

/// Connection Indicator Widget
class ConnectionIndicator extends StatefulWidget {
  /// Connection Manager
  final ConnectionManager? connectionManager;

  /// Soll kompakt angezeigt werden? (nur Icon)
  final bool compact;

  /// Soll Tooltip angezeigt werden?
  final bool showTooltip;

  /// Callback bei Tap
  final VoidCallback? onTap;

  /// Größe des Icons
  final double iconSize;

  /// Konstruktor
  const ConnectionIndicator({
    Key? key,
    this.connectionManager,
    this.compact = false,
    this.showTooltip = true,
    this.onTap,
    this.iconSize = 20,
  }) : super(key: key);

  @override
  State<ConnectionIndicator> createState() => _ConnectionIndicatorState();
}

class _ConnectionIndicatorState extends State<ConnectionIndicator> {
  /// Aktueller Status
  ConnectionStatus _currentStatus = ConnectionStatus.disconnected;

  /// Stream Subscription
  StreamSubscription<ConnectionEvent>? _subscription;

  @override
  void initState() {
    super.initState();
    _initialize();
  }

  /// Initialisierung
  void _initialize() {
    final manager = widget.connectionManager;
    if (manager != null) {
      _currentStatus = manager.currentStatus;
      _subscription = manager.statusStream.listen(_onStatusChanged);
    }
  }

  /// Status-Änderung behandeln
  void _onStatusChanged(ConnectionEvent event) {
    if (mounted) {
      setState(() {
        _currentStatus = event.status;
      });
    }
  }

  @override
  void didUpdateWidget(ConnectionIndicator oldWidget) {
    super.didUpdateWidget(oldWidget);
    
    // Wenn Connection Manager geändert wurde
    if (widget.connectionManager != oldWidget.connectionManager) {
      _subscription?.cancel();
      _initialize();
    }
  }

  @override
  void dispose() {
    _subscription?.cancel();
    super.dispose();
  }

  /// Icon basierend auf Status
  IconData _getStatusIcon() {
    return switch (_currentStatus) {
      ConnectionStatus.connected => Icons.wifi,
      ConnectionStatus.localWifi => Icons.wifi,
      ConnectionStatus.tailscale => Icons.vpn_lock,
      ConnectionStatus.disconnected => Icons.wifi_off,
      ConnectionStatus.offline => Icons.signal_wifi_off,
    };
  }

  /// Farbe basierend auf Status
  Color _getStatusColor(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return switch (_currentStatus) {
      ConnectionStatus.connected => Colors.green,
      ConnectionStatus.localWifi => Colors.green,
      ConnectionStatus.tailscale => Colors.blue,
      ConnectionStatus.disconnected => Colors.orange,
      ConnectionStatus.offline => Colors.red,
    };
  }

  /// Tooltip-Text basierend auf Status
  String _getTooltipText() {
    return switch (_currentStatus) {
      ConnectionStatus.connected => 'Mit OpenClaw verbunden',
      ConnectionStatus.localWifi => 'Lokale WLAN-Verbindung',
      ConnectionStatus.tailscale => 'Tailscale VPN-Verbindung',
      ConnectionStatus.disconnected => 'OpenClaw nicht erreichbar',
      ConnectionStatus.offline => 'Offline (keine Netzwerkverbindung)',
    };
  }

  /// Status-Text für erweiterte Ansicht
  String _getStatusText() {
    return switch (_currentStatus) {
      ConnectionStatus.connected => 'Verbunden',
      ConnectionStatus.localWifi => 'Lokales WLAN',
      ConnectionStatus.tailscale => 'Tailscale VPN',
      ConnectionStatus.disconnected => 'Getrennt',
      ConnectionStatus.offline => 'Offline',
    };
  }

  /// Widget bauen
  @override
  Widget build(BuildContext context) {
    final icon = _getStatusIcon();
    final color = _getStatusColor(context);
    final tooltipText = _getTooltipText();
    final statusText = _getStatusText();

    final indicator = GestureDetector(
      onTap: widget.onTap,
      child: widget.compact
          ? _buildCompactIndicator(icon, color, tooltipText)
          : _buildExpandedIndicator(icon, color, statusText, tooltipText),
    );

    if (widget.showTooltip && !widget.compact) {
      return Tooltip(
        message: tooltipText,
        child: indicator,
      );
    }

    return indicator;
  }

  /// Kompakte Ansicht (nur Icon)
  Widget _buildCompactIndicator(
    IconData icon,
    Color color,
    String tooltipText,
  ) {
    final iconWidget = Icon(
      icon,
      size: widget.iconSize,
      color: color,
    );

    if (widget.showTooltip) {
      return Tooltip(
        message: tooltipText,
        child: iconWidget,
      );
    }

    return iconWidget;
  }

  /// Erweiterte Ansicht (Icon + Text)
  Widget _buildExpandedIndicator(
    IconData icon,
    Color color,
    String statusText,
    String tooltipText,
  ) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withOpacity(0.3), width: 1),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            icon,
            size: widget.iconSize,
            color: color,
          ),
          const SizedBox(width: 6),
          Text(
            statusText,
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w500,
              color: color,
            ),
          ),
        ],
      ),
    );
  }
}

/// Connection Indicator mit Auto-Refresh
class AutoRefreshConnectionIndicator extends StatefulWidget {
  final bool compact;
  final bool showTooltip;
  final VoidCallback? onTap;
  final double iconSize;
  final Duration refreshInterval;

  const AutoRefreshConnectionIndicator({
    Key? key,
    this.compact = false,
    this.showTooltip = true,
    this.onTap,
    this.iconSize = 20,
    this.refreshInterval = const Duration(seconds: 30),
  }) : super(key: key);

  @override
  State<AutoRefreshConnectionIndicator> createState() =>
      _AutoRefreshConnectionIndicatorState();
}

class _AutoRefreshConnectionIndicatorState
    extends State<AutoRefreshConnectionIndicator> {
  ConnectionManager? _connectionManager;
  Timer? _refreshTimer;

  @override
  void initState() {
    super.initState();
    _initialize();
    _startRefreshTimer();
  }

  /// Initialisierung
  void _initialize() {
    try {
      _connectionManager = connectionManager;
    } catch (e) {
      // ConnectionManager noch nicht initialisiert
      _connectionManager = null;
    }
  }

  /// Refresh-Timer starten
  void _startRefreshTimer() {
    _refreshTimer?.cancel();
    _refreshTimer = Timer.periodic(widget.refreshInterval, (_) {
      if (mounted) {
        setState(() {
          _initialize();
        });
      }
    });
  }

  @override
  void dispose() {
    _refreshTimer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ConnectionIndicator(
      connectionManager: _connectionManager,
      compact: widget.compact,
      showTooltip: widget.showTooltip,
      onTap: widget.onTap,
      iconSize: widget.iconSize,
    );
  }
}

/// Connection Status Badge (für AppBar)
class ConnectionStatusBadge extends StatelessWidget {
  final ConnectionManager? connectionManager;
  final double size;

  const ConnectionStatusBadge({
    Key? key,
    this.connectionManager,
    this.size = 10,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return StreamBuilder<ConnectionEvent>(
      stream: connectionManager?.statusStream,
      initialData: ConnectionEvent(
        status: connectionManager?.currentStatus ?? ConnectionStatus.disconnected,
        previousStatus: ConnectionStatus.disconnected,
      ),
      builder: (context, snapshot) {
        final status = snapshot.data?.status ?? ConnectionStatus.disconnected;
        final color = _getBadgeColor(status);

        return Container(
          width: size,
          height: size,
          decoration: BoxDecoration(
            color: color,
            shape: BoxShape.circle,
            border: Border.all(
              color: Theme.of(context).scaffoldBackgroundColor,
              width: 1.5,
            ),
          ),
        );
      },
    );
  }

  /// Badge-Farbe basierend auf Status
  Color _getBadgeColor(ConnectionStatus status) {
    return switch (status) {
      ConnectionStatus.connected => Colors.green,
      ConnectionStatus.localWifi => Colors.green,
      ConnectionStatus.tailscale => Colors.blue,
      ConnectionStatus.disconnected => Colors.orange,
      ConnectionStatus.offline => Colors.red,
    };
  }
}

/// Connection Info Dialog
class ConnectionInfoDialog extends StatelessWidget {
  final ConnectionManager connectionManager;

  const ConnectionInfoDialog({
    Key? key,
    required this.connectionManager,
  }) : super(key: key);

  /// Dialog anzeigen
  static Future<void> show({
    required BuildContext context,
    required ConnectionManager connectionManager,
  }) async {
    await showDialog(
      context: context,
      builder: (context) => ConnectionInfoDialog(
        connectionManager: connectionManager,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final stats = connectionManager.getStatistics();

    return AlertDialog(
      title: const Row(
        children: [
          Icon(Icons.network_check),
          SizedBox(width: 12),
          Text('Verbindungsinformationen'),
        ],
      ),
      content: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            // Aktueller Status
            _buildInfoRow('Status', stats['currentStatus']),
            const SizedBox(height: 12),

            // Konfiguration
            const Text(
              'Konfiguration:',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            _buildInfoRow('Host', stats['config']['host']),
            _buildInfoRow('Port', stats['config']['port'].toString()),
            if (stats['config']['tailscale'] != null)
              _buildInfoRow('Tailscale', stats['config']['tailscale']),
            _buildInfoRow(
                'Lokal', stats['config']['isLocal'] ? 'Ja' : 'Nein'),
            const SizedBox(height: 12),

            // Statistiken
            const Text(
              'Statistiken:',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            _buildInfoRow(
                'Fehlgeschlagene Prüfungen', stats['failedChecks'].toString()),
            _buildInfoRow('Max. fehlgeschlagene Prüfungen',
                stats['maxFailedChecks'].toString()),
            _buildInfoRow('Prüf-Intervall',
                '${stats['checkIntervalSeconds']} Sekunden'),
            if (stats['lastSuccessfulCheck'] != null)
              _buildInfoRow('Letzte erfolgreiche Prüfung',
                  stats['lastSuccessfulCheck']),
            const SizedBox(height: 12),

            // Beste verfügbare URL
            _buildInfoRow(
                'Beste verfügbare URL', connectionManager.getBestAvailableUrl()),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Schließen'),
        ),
        ElevatedButton(
          onPressed: () async {
            await connectionManager.checkConnectionManually();
            // Dialog neu aufbauen
            if (context.mounted) {
              Navigator.of(context).pop();
              await show(context: context, connectionManager: connectionManager);
            }
          },
          child: const Text('Manuell prüfen'),
        ),
      ],
    );
  }

  /// Info-Zeile bauen
  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 180,
            child: Text(
              '$label:',
              style: const TextStyle(fontWeight: FontWeight.w500),
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: SelectableText(
              value,
              style: const TextStyle(fontFamily: 'Monospace'),
            ),
          ),
        ],
      ),
    );
  }
}

/// Connection Status Banner (für Offline-Warnung)
class ConnectionStatusBanner extends StatelessWidget {
  final ConnectionManager connectionManager;
  final VoidCallback? onRetry;
  final bool showWhenOnline;

  const ConnectionStatusBanner({
    Key? key,
    required this.connectionManager,
    this.onRetry,
    this.showWhenOnline = false,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return StreamBuilder<ConnectionEvent>(
      stream: connectionManager.statusStream,
      initialData: ConnectionEvent(
        status: connectionManager.currentStatus,
        previousStatus: connectionManager.currentStatus,
      ),
      builder: (context, snapshot) {
        final status = snapshot.data?.status ?? ConnectionStatus.disconnected;
        final error = snapshot.data?.error;

        // Nur anzeigen wenn offline/disconnected oder showWhenOnline true
        if ((status == ConnectionStatus.connected ||
                status == ConnectionStatus.localWifi ||
                status == ConnectionStatus.tailscale) &&
            !showWhenOnline) {
          return const SizedBox.shrink();
        }

        return _buildBanner(context, status, error);
      },
    );
  }

  /// Banner bauen
  Widget _buildBanner(
    BuildContext context,
    ConnectionStatus status,
    String? error,
  ) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    final (color, icon, title, message) = switch (status) {
      ConnectionStatus.connected => (
          Colors.green,
          Icons.wifi,
          'Verbunden',
          'Mit OpenClaw verbunden'
        ),
      ConnectionStatus.localWifi => (
          Colors.green,
          Icons.wifi,
          'Lokales WLAN',
          'Direkte Verbindung zum lokalen Netzwerk'
        ),
      ConnectionStatus.tailscale => (
          Colors.blue,
          Icons.vpn_lock,
          'Tailscale VPN',
          'Sichere VPN-Verbindung aktiv'
        ),
      ConnectionStatus.disconnected => (
          Colors.orange,
          Icons.wifi_off,
          'Getrennt',
          error ?? 'OpenClaw nicht erreichbar'
        ),
      ConnectionStatus.offline => (
          Colors.red,
          Icons.signal_wifi_off,
          'Offline',
          error ?? 'Keine Netzwerkverbindung verfügbar'
        ),
    };

    return Material(
      color: color.withOpacity(isDark ? 0.2 : 0.1),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        child: Row(
          children: [
            Icon(icon, color: color),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      color: color,
                    ),
                  ),
                  if (message.isNotEmpty)
                    Text(
                      message,
                      style: TextStyle(
                        fontSize: 12,
                        color: color.withOpacity(0.8),
                      ),
                    ),
                ],
              ),
            ),
            if (onRetry != null &&
                (status == ConnectionStatus.disconnected ||
                    status == ConnectionStatus.offline))
              IconButton(
                icon: const Icon(Icons.refresh),
                onPressed: onRetry,
                iconSize: 20,
                color: color,
              ),
          ],
        ),
      ),
    );
  }
}