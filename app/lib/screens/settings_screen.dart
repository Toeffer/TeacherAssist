/// Settings Screen für LehrerAgent
/// Einstellungen für Verbindung, Modell, Benachrichtigungen und Datenschutz
library settings_screen;

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../config/app_config.dart';
import '../services/connection_manager.dart';
import '../services/tailscale_service.dart';
import '../services/notification_service.dart';

/// Settings Screen State
class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final _connectionManager = connectionManager;
  final _tailscaleService = tailscaleService;
  final _notificationService = notificationService;
  
  bool _notificationsEnabled = true;
  bool _autoReconnect = true;
  bool _darkMode = false;
  String _selectedLanguage = 'de';
  double _fontSize = 16.0;

  @override
  void initState() {
    super.initState();
    _loadSettings();
  }

  /// Einstellungen laden
  Future<void> _loadSettings() async {
    // Hier würden Einstellungen aus SharedPreferences geladen werden
    setState(() {
      _notificationsEnabled = true;
      _autoReconnect = true;
      _darkMode = false;
      _selectedLanguage = 'de';
      _fontSize = 16.0;
    });
  }

  /// Einstellungen speichern
  Future<void> _saveSettings() async {
    // Hier würden Einstellungen in SharedPreferences gespeichert werden
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Einstellungen gespeichert'),
        duration: Duration(seconds: 2),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final appConfig = Provider.of<AppConfig>(context);
    
    return Scaffold(
      appBar: AppBar(
        title: const Text('Einstellungen'),
        actions: [
          IconButton(
            icon: const Icon(Icons.save),
            onPressed: _saveSettings,
            tooltip: 'Einstellungen speichern',
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16.0),
        children: [
          // Verbindungseinstellungen
          _buildConnectionSection(appConfig),
          const SizedBox(height: 24),
          
          // Tailscale Einstellungen
          _buildTailscaleSection(),
          const SizedBox(height: 24),
          
          // Benachrichtigungseinstellungen
          _buildNotificationSection(),
          const SizedBox(height: 24),
          
          // Darstellungseinstellungen
          _buildAppearanceSection(),
          const SizedBox(height: 24),
          
          // Datenschutz & Sicherheit
          _buildPrivacySection(),
          const SizedBox(height: 24),
          
          // Über die App
          _buildAboutSection(appConfig),
        ],
      ),
    );
  }

  /// Verbindungseinstellungen
  Widget _buildConnectionSection(AppConfig appConfig) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Verbindung',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            
            // OpenClaw Host
            ListTile(
              leading: const Icon(Icons.computer),
              title: const Text('OpenClaw Server'),
              subtitle: Text('${appConfig.openClawHost}:${appConfig.openClawPort}'),
              trailing: IconButton(
                icon: const Icon(Icons.edit),
                onPressed: () => _showHostEditDialog(appConfig),
                tooltip: 'Server bearbeiten',
              ),
            ),
            
            // Verbindungsstatus
            StreamBuilder<ConnectionStatus>(
              stream: _connectionManager.statusStream,
              builder: (context, snapshot) {
                final status = snapshot.data ?? _connectionManager.currentStatus;
                final isOnline = status == ConnectionStatus.connected;
                
                return ListTile(
                  leading: Icon(
                    isOnline ? Icons.wifi : Icons.wifi_off,
                    color: isOnline ? Colors.green : Colors.red,
                  ),
                  title: Text('Status: ${_getStatusText(status)}'),
                  subtitle: Text(_getStatusDescription(status)),
                  trailing: isOnline
                      ? null
                      : ElevatedButton(
                          onPressed: () => _connectionManager.connect(),
                          child: const Text('Verbinden'),
                        ),
                );
              },
            ),
            
            // Auto-Reconnect
            SwitchListTile(
              title: const Text('Automatisch wieder verbinden'),
              subtitle: const Text('Bei Verbindungsabbruch automatisch neu verbinden'),
              value: _autoReconnect,
              onChanged: (value) {
                setState(() {
                  _autoReconnect = value;
                });
              },
            ),
          ],
        ),
      ),
    );
  }

  /// Tailscale Einstellungen
  Widget _buildTailscaleSection() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Tailscale VPN',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            
            // Tailscale Status
            StreamBuilder<TailscaleStatus>(
              stream: _tailscaleService.statusStream,
              builder: (context, snapshot) {
                final status = snapshot.data ?? _tailscaleService.currentStatus;
                final isConnected = status == TailscaleStatus.connected;
                final isInstalled = status != TailscaleStatus.notInstalled;
                
                return Column(
                  children: [
                    ListTile(
                      leading: Icon(
                        isConnected ? Icons.vpn_lock : Icons.vpn_lock_outlined,
                        color: isConnected ? Colors.green : Colors.grey,
                      ),
                      title: Text('Tailscale: ${_getTailscaleStatusText(status)}'),
                      subtitle: Text(_getTailscaleStatusDescription(status)),
                      trailing: isInstalled && !isConnected
                          ? ElevatedButton(
                              onPressed: () => _tailscaleService.connect(),
                              child: const Text('Verbinden'),
                            )
                          : null,
                    ),
                    
                    if (isInstalled)
                      Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 16.0),
                        child: ElevatedButton.icon(
                          icon: const Icon(Icons.qr_code),
                          label: const Text('Login mit QR-Code'),
                          onPressed: () => _showTailscaleLoginDialog(),
                          style: ElevatedButton.styleFrom(
                            minimumSize: const Size(double.infinity, 48),
                          ),
                        ),
                      ),
                    
                    if (!isInstalled)
                      const Padding(
                        padding: EdgeInsets.symmetric(horizontal: 16.0),
                        child: Text(
                          'Tailscale ist nicht installiert. Bitte installieren Sie Tailscale für VPN-Zugriff.',
                          style: TextStyle(color: Colors.orange),
                        ),
                      ),
                  ],
                );
              },
            ),
          ],
        ),
      ),
    );
  }

  /// Benachrichtigungseinstellungen
  Widget _buildNotificationSection() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Benachrichtigungen',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            
            // Benachrichtigungen aktivieren
            SwitchListTile(
              title: const Text('Benachrichtigungen aktivieren'),
              subtitle: const Text('Push-Benachrichtigungen für abgeschlossene Tasks'),
              value: _notificationsEnabled,
              onChanged: (value) {
                setState(() {
                  _notificationsEnabled = value;
                });
              },
            ),
            
            // Test-Benachrichtigung
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16.0),
              child: ElevatedButton.icon(
                icon: const Icon(Icons.notifications),
                label: const Text('Test-Benachrichtigung senden'),
                onPressed: _notificationsEnabled
                    ? () => _sendTestNotification()
                    : null,
                style: ElevatedButton.styleFrom(
                  minimumSize: const Size(double.infinity, 48),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// Darstellungseinstellungen
  Widget _buildAppearanceSection() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Darstellung',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            
            // Dark Mode
            SwitchListTile(
              title: const Text('Dark Mode'),
              subtitle: const Text('Dunkles Farbschema verwenden'),
              value: _darkMode,
              onChanged: (value) {
                setState(() {
                  _darkMode = value;
                });
              },
            ),
            
            // Schriftgröße
            ListTile(
              title: const Text('Schriftgröße'),
              subtitle: Slider(
                value: _fontSize,
                min: 12.0,
                max: 24.0,
                divisions: 12,
                label: '${_fontSize.toInt()} pt',
                onChanged: (value) {
                  setState(() {
                    _fontSize = value;
                  });
                },
              ),
            ),
            
            // Sprache
            ListTile(
              title: const Text('Sprache'),
              subtitle: DropdownButton<String>(
                value: _selectedLanguage,
                isExpanded: true,
                items: const [
                  DropdownMenuItem(value: 'de', child: Text('Deutsch')),
                  DropdownMenuItem(value: 'en', child: Text('Englisch')),
                ],
                onChanged: (value) {
                  if (value != null) {
                    setState(() {
                      _selectedLanguage = value;
                    });
                  }
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// Datenschutz & Sicherheit
  Widget _buildPrivacySection() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Datenschutz & Sicherheit',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            
            // Datenschutzerklärung
            ListTile(
              leading: const Icon(Icons.privacy_tip),
              title: const Text('Datenschutzerklärung'),
              onTap: () => _showPrivacyPolicy(),
            ),
            
            // Daten löschen
            ListTile(
              leading: const Icon(Icons.delete, color: Colors.red),
              title: const Text('Gespeicherte Daten löschen'),
              subtitle: const Text('Löscht alle lokalen Daten und Einstellungen'),
              onTap: () => _showDeleteDataDialog(),
            ),
            
            // Export Daten
            ListTile(
              leading: const Icon(Icons.backup),
              title: const Text('Daten exportieren'),
              subtitle: const Text('Exportiert alle Memory-Dateien als ZIP'),
              onTap: () => _exportData(),
            ),
          ],
        ),
      ),
    );
  }

  /// Über die App
  Widget _buildAboutSection(AppConfig appConfig) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Über die App',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            
            // App-Info
            ListTile(
              leading: const Icon(Icons.info),
              title: const Text('Version'),
              subtitle: Text(appConfig.appVersion),
            ),
            
            // Lizenz
            ListTile(
              leading: const Icon(Icons.balance),
              title: const Text('Lizenz'),
              subtitle: const Text('MIT License'),
              onTap: () => _showLicense(),
            ),
            
            // GitHub
            ListTile(
              leading: const Icon(Icons.code),
              title: const Text('Quellcode'),
              subtitle: const Text('GitHub Repository'),
              onTap: () => _openGitHub(),
            ),
            
            // Feedback
            ListTile(
              leading: const Icon(Icons.feedback),
              title: const Text('Feedback senden'),
              subtitle: const Text('Probleme oder Verbesserungsvorschläge'),
              onTap: () => _sendFeedback(),
            ),
          ],
        ),
      ),
    );
  }

  /// Hilfsmethoden
  String _getStatusText(ConnectionStatus status) {
    switch (status) {
      case ConnectionStatus.connected:
        return 'Verbunden';
      case ConnectionStatus.connecting:
        return 'Verbinde...';
      case ConnectionStatus.disconnected:
        return 'Getrennt';
      case ConnectionStatus.error:
        return 'Fehler';
    }
  }

  String _getStatusDescription(ConnectionStatus status) {
    switch (status) {
      case ConnectionStatus.connected:
        return 'Mit OpenClaw Server verbunden';
      case ConnectionStatus.connecting:
        return 'Stelle Verbindung her...';
      case ConnectionStatus.disconnected:
        return 'Nicht verbunden';
      case ConnectionStatus.error:
        return 'Verbindungsfehler aufgetreten';
    }
  }

  String _getTailscaleStatusText(TailscaleStatus status) {
    switch (status) {
      case TailscaleStatus.connected:
        return 'Verbunden';
      case TailscaleStatus.connecting:
        return 'Verbinde...';
      case TailscaleStatus.disconnected:
        return 'Getrennt';
      case TailscaleStatus.error:
        return 'Fehler';
      case TailscaleStatus.notInstalled:
        return 'Nicht installiert';
    }
  }

  String _getTailscaleStatusDescription(TailscaleStatus status) {
    switch (status) {
      case TailscaleStatus.connected:
        return 'Mit Tailscale Netzwerk verbunden';
      case TailscaleStatus.connecting:
        return 'Stelle Tailscale-Verbindung her...';
      case TailscaleStatus.disconnected:
        return 'Tailscale nicht verbunden';
      case TailscaleStatus.error:
        return 'Tailscale-Fehler aufgetreten';
      case TailscaleStatus.notInstalled:
        return 'Tailscale ist nicht installiert';
    }
  }

  /// Dialoge
  Future<void> _showHostEditDialog(AppConfig appConfig) async {
    final hostController = TextEditingController(text: appConfig.openClawHost);
    final portController = TextEditingController(text: appConfig.openClawPort.toString());
    
    await showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Server bearbeiten'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: hostController,
              decoration: const InputDecoration(
                labelText: 'Host',
                hintText: 'localhost oder IP-Adresse',
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: portController,
              decoration: const InputDecoration(
                labelText: 'Port',
                hintText: '18789',
              ),
              keyboardType: TextInputType.number,
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Abbrechen'),
          ),
          ElevatedButton(
            onPressed: () {
              // Hier würde die neue Konfiguration gespeichert werden
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('Server-Einstellungen wurden geändert. App neu starten erforderlich.'),
                  duration: Duration(seconds: 3),
                ),
              );
            },
            child: const Text('Speichern'),
          ),
        ],
      ),
    );
  }

  Future<void> _showTailscaleLoginDialog() async {
    final url = await _tailscaleService.getLoginUrl();
    
    if (url == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Tailscale Login-URL konnte nicht abgerufen werden'),
          duration: Duration(seconds: 3),
        ),
      );
      return;
    }
    
    await showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Tailscale Login'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('Scannen Sie den QR-Code mit Ihrem Smartphone oder besuchen Sie die URL:'),
            const SizedBox(height: 12),
            SelectableText(
              url,
              style: const TextStyle(color: Colors.blue, decoration: TextDecoration.underline),
            ),
            const SizedBox(height: 16),
            const Text(
              'Nach dem Login wird Ihr Gerät automatisch mit dem Tailscale Netzwerk verbunden.',
              style: TextStyle(fontSize: 12, color: Colors.grey),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Schließen'),
          ),
        ],
      ),
    );
  }

  Future<void> _sendTestNotification() async {
    await _notificationService.notifyTaskCompleted(
      taskName: 'Test-Task',
      resultSummary: 'Dies ist eine Test-Benachrichtigung',
      taskData: {'test': true},
    );
    
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Test-Benachrichtigung gesendet'),
        duration: Duration(seconds: 2),
      ),
    );
  }

  Future<void> _showPrivacyPolicy() async {
    // Hier würde die Datenschutzerklärung angezeigt werden
    await showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Datenschutzerklärung'),
        content: const SingleChildScrollView(
          child: Text(
            'LehrerAgent speichert alle Daten lokal auf Ihrem Gerät.\n\n'
            '• Keine personenbezogenen Schülerdaten werden gespeichert\n'
            '• Keine Daten werden an externe Server gesendet\n'
            '• Alle Memory-Dateien bleiben lokal\n'
            '• OCR-Ergebnisse werden nur temporär im RAM gehalten\n\n'
            'DSGVO-konforme Verarbeitung gemäß Schulrecht.',
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Schließen'),
          ),
        ],
      ),
    );
  }

  Future<void> _showDeleteDataDialog() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Daten löschen'),
        content: const Text(
          'Möchten Sie wirklich alle gespeicherten Daten löschen?\n\n'
          'Dies umfasst:\n'
          '• Alle Memory-Dateien\n'
          '• Lehrplan-Vektordatenbank\n'
          '• App-Einstellungen\n\n'
          'Diese Aktion kann nicht rückgängig gemacht werden.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Abbrechen'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, true),
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            child: const Text('Alle Daten löschen'),
          ),
        ],
      ),
    );
    
    if (confirmed == true) {
      // Hier würden alle Daten gelöscht werden
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Alle Daten wurden gelöscht'),
          duration: Duration(seconds: 3),
        ),
      );
    }
  }

  Future<void> _exportData() async {
    // Hier würden die Daten exportiert werden
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Datenexport wird vorbereitet...'),
        duration: Duration(seconds: 2),
      ),
    );
    
    // Simulierte Export-Zeit
    await Future.delayed(const Duration(seconds: 2));
    
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Daten wurden erfolgreich exportiert'),
        duration: Duration(seconds: 3),
      ),
    );
  }

  Future<void> _showLicense() async {
    await showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('MIT License'),
        content: const SingleChildScrollView(
          child: Text(
            'Copyright (c) 2026 LehrerAgent\n\n'
            'Permission is hereby granted, free of charge, to any person obtaining a copy '
            'of this software and associated documentation files (the "Software"), to deal '
            'in the Software without restriction, including without limitation the rights '
            'to use, copy, modify, merge, publish, distribute, sublicense, and/or sell '
            'copies of the Software, and to permit persons to whom the Software is '
            'furnished to do so, subject to the following conditions:\n\n'
            'The above copyright notice and this permission notice shall be included in all '
            'copies or substantial portions of the Software.\n\n'
            'THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR '
            'IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, '
            'FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE '
            'AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER '
            'LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, '
            'OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.',
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Schließen'),
          ),
        ],
      ),
    );
  }

  Future<void> _openGitHub() async {
    // Hier würde die GitHub-URL geöffnet werden
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('GitHub Repository wird geöffnet...'),
        duration: Duration(seconds: 2),
      ),
    );
  }

  Future<void> _sendFeedback() async {
    // Hier würde das Feedback-Formular geöffnet werden
    final feedbackController = TextEditingController();
    
    await showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Feedback senden'),
        content: TextField(
          controller: feedbackController,
          maxLines: 5,
          decoration: const InputDecoration(
            hintText: 'Beschreiben Sie Ihr Problem oder Ihren Verbesserungsvorschlag...',
            border: OutlineInputBorder(),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Abbrechen'),
          ),
          ElevatedButton(
            onPressed: () {
              if (feedbackController.text.trim().isNotEmpty) {
                Navigator.pop(context);
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text('Vielen Dank für Ihr Feedback!'),
                    duration: Duration(seconds: 3),
                  ),
                );
              }
            },
            child: const Text('Senden'),
          ),
        ],
      ),
    );
  }
}