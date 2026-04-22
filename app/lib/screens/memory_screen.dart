/// Memory-Screen für LehrerAgent
/// Zeigt Lehrerprofil und Memory-Übersicht an (primär für Desktop)
library memory_screen;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../services/openclaw_service.dart';
import '../config/app_config.dart';

/// Memory-Screen Widget
class MemoryScreen extends StatefulWidget {
  /// Konstruktor
  const MemoryScreen({Key? key}) : super(key: key);

  @override
  State<MemoryScreen> createState() => _MemoryScreenState();
}

class _MemoryScreenState extends State<MemoryScreen> {
  /// OpenClaw Service
  final OpenClawService _openClawService = OpenClawService();

  /// Lade-Status
  bool _isLoading = true;

  /// Memory-Daten
  Map<String, dynamic> _memoryData = {};

  /// Fehler-Nachricht
  String? _errorMessage;

  /// Initialisierung
  @override
  void initState() {
    super.initState();
    _loadMemoryData();
  }

  /// Memory-Daten laden
  Future<void> _loadMemoryData() async {
    if (!_openClawService.isConnected) {
      setState(() {
        _isLoading = false;
        _errorMessage = 'Nicht mit OpenClaw verbunden';
      });
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      // Lehrerprofil laden
      final profileResult = await _openClawService.callTool(
        'memory_reader',
        {'filepath': 'lehrerprofil.md'},
      );

      if (profileResult['success'] == true) {
        _memoryData['profile'] = _parseProfile(profileResult['content']);
      }

      // Lehrplan-Status laden
      final lehrplanResult = await _openClawService.callTool(
        'memory_reader',
        {'filepath': 'lehrplan_index.md'},
      );

      if (lehrplanResult['success'] == true) {
        _memoryData['lehrplan'] = lehrplanResult['content'];
      }

      // Onboarding-Status prüfen
      final onboardingResult = await _openClawService.callTool(
        'memory_reader',
        {'filepath': 'onboarding_complete.md'},
      );

      _memoryData['onboardingComplete'] = onboardingResult['exists'] == true;

      // Bewertungsraster zählen
      final bewertungsrasterResult = await _openClawService.callTool(
        'memory_reader',
        {'filepath': 'bewertungsraster/README.md'},
      );

      _memoryData['hasBewertungsraster'] = bewertungsrasterResult['exists'] == true;
    } catch (e) {
      setState(() {
        _errorMessage = 'Fehler beim Laden: $e';
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  /// Lehrerprofil parsen
  Map<String, dynamic> _parseProfile(String content) {
    final profile = <String, dynamic>{};

    // Name extrahieren
    final nameMatch = RegExp(r'- \*\*Name:\*\*\s*(.+)$', multiLine: true).firstMatch(content);
    if (nameMatch != null) {
      profile['name'] = nameMatch.group(1)?.trim() ?? '(nicht angegeben)';
    }

    // Bundesland extrahieren
    final bundeslandMatch = RegExp(r'- \*\*Bundesland:\*\*\s*(.+)$', multiLine: true).firstMatch(content);
    if (bundeslandMatch != null) {
      profile['bundesland'] = bundeslandMatch.group(1)?.trim() ?? '(nicht angegeben)';
    }

    // Schulform extrahieren
    final schulformMatch = RegExp(r'- \*\*Schulform:\*\*\s*(.+)$', multiLine: true).firstMatch(content);
    if (schulformMatch != null) {
      profile['schulform'] = schulformMatch.group(1)?.trim() ?? '(nicht angegeben)';
    }

    // Fächer extrahieren (vereinfacht)
    final faecherSection = _extractSection(content, 'Unterrichtsfächer');
    if (faecherSection.isNotEmpty) {
      final rows = faecherSection.split('\n');
      final faecher = <Map<String, String>>[];
      
      for (final row in rows) {
        if (row.contains('|') && !row.contains('Fach') && !row.contains('---')) {
          final cells = row.split('|').where((cell) => cell.trim().isNotEmpty).toList();
          if (cells.length >= 2) {
            faecher.add({
              'fach': cells[0].trim(),
              'klassen': cells[1].trim(),
              'besonderheiten': cells.length >= 3 ? cells[2].trim() : '',
            });
          }
        }
      }
      
      profile['faecher'] = faecher;
    }

    return profile;
  }

  /// Abschnitt aus Markdown extrahieren
  String _extractSection(String content, String sectionName) {
    final pattern = RegExp(r'^##\s*' + RegExp.escape(sectionName) + r'\s*$(.*?)(?=^##|\Z)', multiLine: true, dotAll: true);
    final match = pattern.firstMatch(content);
    return match?.group(1)?.trim() ?? '';
  }

  /// Memory-Daten aktualisieren
  Future<void> _refreshData() async {
    await _loadMemoryData();
  }

  /// Profil aktualisieren
  void _updateProfile() {
    // Hier könnte man einen Dialog öffnen oder zur Chat-Screen navigieren
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Sage "Profil aktualisieren" im Chat, um dein Profil zu ändern'),
        duration: Duration(seconds: 3),
      ),
    );
  }

  /// In Chat navigieren
  void _navigateToChat() {
    Navigator.of(context).pop(); // Zurück zur Chat-Screen
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final isDesktop = MediaQuery.of(context).size.width >= 768;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Memory & Profil'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _isLoading ? null : _refreshData,
            tooltip: 'Aktualisieren',
          ),
          IconButton(
            icon: const Icon(Icons.chat),
            onPressed: _navigateToChat,
            tooltip: 'Zum Chat',
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _errorMessage != null
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.error_outline, size: 64, color: Colors.red),
                      const SizedBox(height: 16),
                      Text(
                        _errorMessage!,
                        style: const TextStyle(fontSize: 16),
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: _refreshData,
                        child: const Text('Erneut versuchen'),
                      ),
                    ],
                  ),
                )
              : SingleChildScrollView(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Status-Karten
                      if (!_memoryData['onboardingComplete'])
                        _buildStatusCard(
                          '⚠️ Onboarding nicht abgeschlossen',
                          'Bitte führe das Onboarding im Chat durch, um alle Funktionen nutzen zu können.',
                          Colors.orange.shade100,
                          Colors.orange.shade800,
                        ),

                      const SizedBox(height: 16),

                      // Lehrerprofil
                      Card(
                        elevation: 2,
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  Text(
                                    '👤 Lehrerprofil',
                                    style: theme.textTheme.headlineSmall,
                                  ),
                                  IconButton(
                                    icon: const Icon(Icons.edit),
                                    onPressed: _updateProfile,
                                    tooltip: 'Profil aktualisieren',
                                  ),
                                ],
                              ),
                              const SizedBox(height: 16),
                              _buildProfileInfo(),
                            ],
                          ),
                        ),
                      ),

                      const SizedBox(height: 16),

                      // Memory-Übersicht
                      Card(
                        elevation: 2,
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                '📁 Memory-Übersicht',
                                style: theme.textTheme.headlineSmall,
                              ),
                              const SizedBox(height: 16),
                              _buildMemoryOverview(),
                            ],
                          ),
                        ),
                      ),

                      const SizedBox(height: 16),

                      // System-Info
                      if (isDesktop)
                        Card(
                          elevation: 2,
                          child: Padding(
                            padding: const EdgeInsets.all(16),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  '⚙️ System-Information',
                                  style: theme.textTheme.headlineSmall,
                                ),
                                const SizedBox(height: 16),
                                _buildSystemInfo(),
                              ],
                            ),
                          ),
                        ),
                    ],
                  ),
                ),
    );
  }

  /// Status-Karte bauen
  Widget _buildStatusCard(String title, String message, Color bgColor, Color textColor) {
    return Card(
      color: bgColor,
      elevation: 1,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            const Icon(Icons.info_outline, color: Colors.orange),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      color: textColor,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    message,
                    style: TextStyle(color: textColor),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// Profil-Info bauen
  Widget _buildProfileInfo() {
    final profile = _memoryData['profile'] ?? {};
    final faecher = profile['faecher'] as List<dynamic>? ?? [];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Grundinformationen
        _buildInfoRow('Name', profile['name'] ?? '(nicht angegeben)'),
        _buildInfoRow('Bundesland', profile['bundesland'] ?? '(nicht angegeben)'),
        _buildInfoRow('Schulform', profile['schulform'] ?? '(nicht angegeben)'),

        const SizedBox(height: 16),

        // Fächer
        if (faecher.isNotEmpty) ...[
          Text(
            'Unterrichtsfächer:',
            style: TextStyle(
              fontWeight: FontWeight.bold,
              fontSize: 16,
            ),
          ),
          const SizedBox(height: 8),
          ...faecher.map((fach) {
            return Padding(
              padding: const EdgeInsets.only(bottom: 4),
              child: Text(
                '• ${fach['fach']} – ${fach['klassen']}',
                style: const TextStyle(fontSize: 14),
              ),
            );
          }).toList(),
        ] else ...[
          Text(
            'Keine Fächer konfiguriert',
            style: TextStyle(
              fontStyle: FontStyle.italic,
              color: Colors.grey.shade600,
            ),
          ),
        ],
      ],
    );
  }

  /// Info-Zeile bauen
  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 100,
            child: Text(
              '$label:',
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(value),
          ),
        ],
      ),
    );
  }

  /// Memory-Übersicht bauen
  Widget _buildMemoryOverview() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildMemoryItem(
          '📄 Lehrerprofil',
          'lehrerprofil.md',
          _memoryData['profile'] != null ? '✅ Konfiguriert' : '❌ Nicht konfiguriert',
        ),
        _buildMemoryItem(
          '📚 Lehrplan',
          'lehrplan_index.md',
          _memoryData['lehrplan']?.isNotEmpty == true ? '✅ Vorhanden' : '❌ Nicht eingerichtet',
        ),
        _buildMemoryItem(
          '📋 Bewertungsraster',
          'bewertungsraster/',
          _memoryData['hasBewertungsraster'] == true ? '✅ Verzeichnis vorhanden' : '❌ Noch keine',
        ),
        _buildMemoryItem(
          '✅ Onboarding',
          'onboarding_complete.md',
          _memoryData['onboardingComplete'] == true ? '✅ Abgeschlossen' : '❌ Ausstehend',
        ),
      ],
    );
  }

  /// Memory-Item bauen
  Widget _buildMemoryItem(String title, String path, String status) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(fontWeight: FontWeight.bold),
                ),
                Text(
                  path,
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.grey.shade600,
                  ),
                ),
              ],
            ),
          ),
          Text(
            status,
            style: TextStyle(
              color: status.contains('✅') ? Colors.green : Colors.red,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }

  /// System-Info bauen
  Widget _buildSystemInfo() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildSystemInfoRow('App-Version', appConfig.appVersion),
        _buildSystemInfoRow('OpenClaw Host', appConfig.openClawHost),
        _buildSystemInfoRow('OpenClaw Port', appConfig.openClawPort.toString()),
        _buildSystemInfoRow('Verbindung', appConfig.isLocalConnection ? 'Lokal (LAN)' : 'Remote'),
        _buildSystemInfoRow('Tailscale', appConfig.usesTailscale ? '✅ Aktiv' : '❌ Inaktiv'),
        _buildSystemInfoRow('Debug-Modus', appConfig.debugMode ? '✅ Aktiv' : '❌ Inaktiv'),
      ],
    );
  }

  /// System-Info-Zeile bauen
  Widget _buildSystemInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        children: [
          SizedBox(
            width: 120,
            child: Text(
              '$label:',
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
          ),
          const SizedBox(width: 8),
          SelectableText(
            value,
            style: const TextStyle(fontFamily: 'Monospace'),
          ),
          if (label == 'OpenClaw Host' || label == 'App-Version')
            IconButton(
              icon: const Icon(Icons.content_copy, size: 16),
              onPressed: () {
                Clipboard.setData(ClipboardData(text: value));
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text('$label kopiert: $value'),
                    duration: const Duration(seconds: 1),
                  ),
                );
              },
              padding: EdgeInsets.zero,
              constraints: const BoxConstraints(),
            ),
        ],
      ),
    );
  }
}