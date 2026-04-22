/// Results Screen für LehrerAgent
/// Zeigt fertige Ergebnisse an mit Druck-/Export-Funktionen
library results_screen;

import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';
import 'package:printing/printing.dart';
import 'package:pdf/widgets.dart' as pw;
import '../services/openclaw_service.dart';

/// Ergebnis-Typen
enum ResultType {
  lessonPlan,      // Stundenentwurf
  assessment,      // Bewertungsraster
  correction,      // Korrekturprotokoll
  curriculum,      // Lehrplan-Extraktion
  other,           // Sonstiges
}

/// Ergebnis-Daten
class ResultData {
  final String id;
  final String title;
  final String content;
  final ResultType type;
  final DateTime createdAt;
  final Map<String, dynamic> metadata;
  final bool isFavorite;

  ResultData({
    required this.id,
    required this.title,
    required this.content,
    required this.type,
    required this.createdAt,
    this.metadata = const {},
    this.isFavorite = false,
  });

  factory ResultData.fromJson(Map<String, dynamic> json) {
    return ResultData(
      id: json['id'],
      title: json['title'],
      content: json['content'],
      type: ResultType.values.firstWhere(
        (e) => e.toString() == json['type'],
        orElse: () => ResultType.other,
      ),
      createdAt: DateTime.parse(json['createdAt']),
      metadata: json['metadata'] ?? {},
      isFavorite: json['isFavorite'] ?? false,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'content': content,
      'type': type.toString(),
      'createdAt': createdAt.toIso8601String(),
      'metadata': metadata,
      'isFavorite': isFavorite,
    };
  }

  /// Icon basierend auf Typ
  IconData get icon {
    switch (type) {
      case ResultType.lessonPlan:
        return Icons.school;
      case ResultType.assessment:
        return Icons.grading;
      case ResultType.correction:
        return Icons.edit_note;
      case ResultType.curriculum:
        return Icons.menu_book;
      case ResultType.other:
        return Icons.description;
    }
  }

  /// Farbe basierend auf Typ
  Color get color {
    switch (type) {
      case ResultType.lessonPlan:
        return Colors.blue;
      case ResultType.assessment:
        return Colors.green;
      case ResultType.correction:
        return Colors.orange;
      case ResultType.curriculum:
        return Colors.purple;
      case ResultType.other:
        return Colors.grey;
    }
  }
}

/// Results Screen State
class ResultsScreen extends StatefulWidget {
  const ResultsScreen({super.key});

  @override
  State<ResultsScreen> createState() => _ResultsScreenState();
}

class _ResultsScreenState extends State<ResultsScreen> {
  final List<ResultData> _results = [];
  final List<ResultData> _filteredResults = [];
  bool _isLoading = true;
  String _searchQuery = '';
  ResultType? _selectedType;
  bool _showFavoritesOnly = false;
  final TextEditingController _searchController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _loadResults();
  }

  /// Ergebnisse laden
  Future<void> _loadResults() async {
    setState(() {
      _isLoading = true;
    });

    try {
      // Hier würden Ergebnisse aus einer lokalen Datenbank geladen werden
      // Für Demo-Zwecke werden Beispiel-Ergebnisse erstellt
      await Future.delayed(const Duration(seconds: 1));
      
      final exampleResults = [
        ResultData(
          id: '1',
          title: 'Mathematik Klasse 7 - Bruchrechnung',
          content: 'Stundenentwurf für die Einführung in die Bruchrechnung...',
          type: ResultType.lessonPlan,
          createdAt: DateTime.now().subtract(const Duration(days: 1)),
          metadata: {
            'fach': 'Mathematik',
            'klasse': '7',
            'thema': 'Bruchrechnung',
            'dauer': '45 Minuten',
          },
          isFavorite: true,
        ),
        ResultData(
          id: '2',
          title: 'Deutsch Klasse 8 - Gedichtanalyse',
          content: 'Bewertungsraster für die Analyse von Gedichten...',
          type: ResultType.assessment,
          createdAt: DateTime.now().subtract(const Duration(days: 2)),
          metadata: {
            'fach': 'Deutsch',
            'klasse': '8',
            'thema': 'Gedichtanalyse',
            'kriterien': 5,
          },
        ),
        ResultData(
          id: '3',
          title: 'Englisch Klasse 9 - Present Perfect',
          content: 'Korrekturprotokoll für die Klassenarbeit...',
          type: ResultType.correction,
          createdAt: DateTime.now().subtract(const Duration(days: 3)),
          metadata: {
            'fach': 'Englisch',
            'klasse': '9',
            'thema': 'Present Perfect',
            'anzahl_schueler': 28,
          },
        ),
        ResultData(
          id: '4',
          title: 'Bayern Lehrplan Mathematik Klasse 7',
          content: 'Extrahiertes Curriculum für Mathematik Klasse 7...',
          type: ResultType.curriculum,
          createdAt: DateTime.now().subtract(const Duration(days: 4)),
          metadata: {
            'bundesland': 'Bayern',
            'fach': 'Mathematik',
            'klasse': '7',
            'quelle': 'Kultusministerium Bayern',
          },
        ),
      ];

      setState(() {
        _results.clear();
        _results.addAll(exampleResults);
        _applyFilters();
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
      _showError('Fehler beim Laden der Ergebnisse: $e');
    }
  }

  /// Filter anwenden
  void _applyFilters() {
    List<ResultData> filtered = List.from(_results);

    // Suchfilter
    if (_searchQuery.isNotEmpty) {
      final query = _searchQuery.toLowerCase();
      filtered = filtered.where((result) {
        return result.title.toLowerCase().contains(query) ||
            result.content.toLowerCase().contains(query) ||
            result.metadata.values.any((value) =>
                value.toString().toLowerCase().contains(query));
      }).toList();
    }

    // Typfilter
    if (_selectedType != null) {
      filtered = filtered.where((result) => result.type == _selectedType).toList();
    }

    // Favoritenfilter
    if (_showFavoritesOnly) {
      filtered = filtered.where((result) => result.isFavorite).toList();
    }

    setState(() {
      _filteredResults.clear();
      _filteredResults.addAll(filtered);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Ergebnisse'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadResults,
            tooltip: 'Aktualisieren',
          ),
          IconButton(
            icon: const Icon(Icons.filter_list),
            onPressed: _showFilterDialog,
            tooltip: 'Filter',
          ),
        ],
      ),
      body: Column(
        children: [
          // Suchleiste
          Padding(
            padding: const EdgeInsets.all(8.0),
            child: TextField(
              controller: _searchController,
              decoration: InputDecoration(
                hintText: 'Ergebnisse suchen...',
                prefixIcon: const Icon(Icons.search),
                suffixIcon: _searchQuery.isNotEmpty
                    ? IconButton(
                        icon: const Icon(Icons.clear),
                        onPressed: () {
                          _searchController.clear();
                          _searchQuery = '';
                          _applyFilters();
                        },
                      )
                    : null,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(8.0),
                ),
              ),
              onChanged: (value) {
                _searchQuery = value;
                _applyFilters();
              },
            ),
          ),

          // Filter-Info
          if (_selectedType != null || _showFavoritesOnly)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 8.0),
              child: Row(
                children: [
                  Chip(
                    label: Text(
                      _selectedType != null
                          ? 'Typ: ${_getTypeName(_selectedType!)}'
                          : 'Favoriten',
                    ),
                    onDeleted: () {
                      if (_selectedType != null) {
                        _selectedType = null;
                      } else {
                        _showFavoritesOnly = false;
                      }
                      _applyFilters();
                    },
                  ),
                  const Spacer(),
                  TextButton(
                    onPressed: _clearFilters,
                    child: const Text('Alle Filter löschen'),
                  ),
                ],
              ),
            ),

          // Ergebnisse Liste
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : _filteredResults.isEmpty
                    ? const Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.inbox, size: 64, color: Colors.grey),
                            SizedBox(height: 16),
                            Text(
                              'Keine Ergebnisse gefunden',
                              style: TextStyle(
                                fontSize: 18,
                                color: Colors.grey,
                              ),
                            ),
                            SizedBox(height: 8),
                            Text(
                              'Ändern Sie Ihre Suchkriterien oder erstellen Sie neue Ergebnisse',
                              textAlign: TextAlign.center,
                              style: TextStyle(color: Colors.grey),
                            ),
                          ],
                        ),
                      )
                    : ListView.builder(
                        itemCount: _filteredResults.length,
                        itemBuilder: (context, index) {
                          final result = _filteredResults[index];
                          return _buildResultCard(result);
                        },
                      ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _exportAllResults,
        icon: const Icon(Icons.download),
        label: const Text('Alle exportieren'),
        tooltip: 'Alle Ergebnisse als PDF exportieren',
      ),
    );
  }

  /// Ergebnis-Karte erstellen
  Widget _buildResultCard(ResultData result) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 4.0),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: result.color.withOpacity(0.2),
          child: Icon(result.icon, color: result.color),
        ),
        title: Text(
          result.title,
          style: TextStyle(
            fontWeight: FontWeight.bold,
            decoration: result.isFavorite
                ? TextDecoration.underline
                : TextDecoration.none,
          ),
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              result.content.length > 100
                  ? '${result.content.substring(0, 100)}...'
                  : result.content,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
            const SizedBox(height: 4),
            Text(
              'Erstellt: ${_formatDate(result.createdAt)}',
              style: const TextStyle(fontSize: 12, color: Colors.grey),
            ),
            if (result.metadata.isNotEmpty)
              Wrap(
                spacing: 4.0,
                children: result.metadata.entries
                    .take(3)
                    .map((entry) => Chip(
                          label: Text('${entry.key}: ${entry.value}'),
                          labelStyle: const TextStyle(fontSize: 10),
                          visualDensity: VisualDensity.compact,
                        ))
                    .toList(),
              ),
          ],
        ),
        trailing: PopupMenuButton<String>(
          onSelected: (value) => _handleResultAction(value, result),
          itemBuilder: (context) => [
            const PopupMenuItem(
              value: 'view',
              child: ListTile(
                leading: Icon(Icons.visibility),
                title: Text('Anzeigen'),
              ),
            ),
            const PopupMenuItem(
              value: 'edit',
              child: ListTile(
                leading: Icon(Icons.edit),
                title: Text('Bearbeiten'),
              ),
            ),
            PopupMenuItem(
              value: 'favorite',
              child: ListTile(
                leading: Icon(
                  result.isFavorite ? Icons.star : Icons.star_border,
                  color: result.isFavorite ? Colors.amber : null,
                ),
                title: Text(
                  result.isFavorite ? 'Favorit entfernen' : 'Als Favorit',
                ),
              ),
            ),
            const PopupMenuDivider(),
            const PopupMenuItem(
              value: 'print',
              child: ListTile(
                leading: Icon(Icons.print),
                title: Text('Drucken'),
              ),
            ),
            const PopupMenuItem(
              value: 'export_pdf',
              child: ListTile(
                leading: Icon(Icons.picture_as_pdf),
                title: Text('Als PDF exportieren'),
              ),
            ),
            const PopupMenuItem(
              value: 'export_txt',
              child: ListTile(
                leading: Icon(Icons.text_snippet),
                title: Text('Als Text exportieren'),
              ),
            ),
            const PopupMenuDivider(),
            const PopupMenuItem(
              value: 'share',
              child: ListTile(
                leading: Icon(Icons.share),
                title: Text('Teilen'),
              ),
            ),
            const PopupMenuItem(
              value: 'delete',
              child: ListTile(
                leading: Icon(Icons.delete, color: Colors.red),
                title: Text('Löschen', style: TextStyle(color: Colors.red)),
              ),
            ),
          ],
        ),
        onTap: () => _viewResultDetails(result),
      ),
    );
  }

  /// Ergebnis-Aktion behandeln
  void _handleResultAction(String action, ResultData result) {
    switch (action) {
      case 'view':
        _viewResultDetails(result);
        break;
      case 'edit':
        _editResult(result);
        break;
      case 'favorite':
        _toggleFavorite(result);
        break;
      case 'print':
        _printResult(result);
        break;
      case 'export_pdf':
        _exportResultAsPdf(result);
        break;
      case 'export_txt':
        _exportResultAsText(result);
        break;
      case 'share':
        _shareResult(result);
        break;
      case 'delete':
        _deleteResult(result);
        break;
    }
  }

  /// Ergebnis-Details anzeigen
  void _viewResultDetails(ResultData result) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => ResultDetailScreen(result: result),
      ),
    );
  }

  /// Ergebnis bearbeiten
  void _editResult(ResultData result) {
    // Hier würde der Bearbeitungsdialog geöffnet werden
    _showInfo('Bearbeitungsfunktion für "${result.title}" wird geöffnet...');
  }

  /// Favorit umschalten
  void _toggleFavorite(ResultData result) {
    setState(() {
      final index = _results.indexWhere((r) => r.id == result.id);
      if (index != -1) {
        _results[index] = ResultData(
          id: result.id,
          title: result.title,
          content: result.content,
          type: result.type,
          createdAt: result.createdAt,
          metadata: result.metadata,
          isFavorite: !result.isFavorite,
        );
        _applyFilters();
      }
    });
  }

  /// Ergebnis drucken
  Future<void> _printResult(ResultData result) async {
    try {
      final pdf = await _createPdf(result);
      await Printing.layoutPdf(
        onLayout: (format) => pdf.save(),
      );
    } catch (e) {
      _showError('Drucken fehlgeschlagen: $e');
    }
  }

  /// Ergebnis als PDF exportieren
  Future<void> _exportResultAsPdf(ResultData result) async {
    try {
      final pdf = await _createPdf(result);
      final dir = await getTemporaryDirectory();
      final file = File('${dir.path}/${result.title}_${result.id}.pdf');
      await file.writeAsBytes(await pdf.save());
      
      await Share.shareXFiles([XFile(file.path)]);
      _showInfo('PDF wurde exportiert und kann geteilt werden');
    } catch (e) {
      _showError('PDF-Export fehlgeschlagen: $e');
    }
  }

  /// Ergebnis als Text exportieren
  Future<void> _exportResultAsText(ResultData result) async {
    try {
      final content = '''
Titel: ${result.title}
Typ: ${_getTypeName(result.type)}
Erstellt: ${_formatDate(result.createdAt)}

${result.content}

Metadaten:
${result.metadata.entries.map((e) => '  ${e.key}: ${e.value}').join('\n')}
''';

      final dir = await getTemporaryDirectory();
      final file = File('${dir.path}/${result.title}_${result.id}.txt');
      await file.writeAsString(content, encoding: utf8);
      
      await Share.shareXFiles([XFile(file.path)]);
      _showInfo('Text wurde exportiert und kann geteilt werden');
    } catch (e) {
      _showError('Text-Export fehlgeschlagen: $e');
    }
  }

  /// Ergebnis teilen
  Future<void> _shareResult(ResultData result) async {
    try {
      final text = '${result.title}\n\n${result.content}';
      await Share.share(text, subject: result.title);
    } catch (e) {
      _showError('Teilen fehlgeschlagen: $e');
    }
  }

  /// Ergebnis löschen
  void _deleteResult(ResultData result) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Ergebnis löschen'),
        content: Text('Möchten Sie "${result.title}" wirklich löschen?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Abbrechen'),
          ),
          ElevatedButton(
            onPressed: () {
              setState(() {
                _results.removeWhere((r) => r.id == result.id);
                _applyFilters();
              });
              Navigator.pop(context);
              _showInfo('Ergebnis wurde gelöscht');
            },
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            child: const Text('Löschen'),
          ),
        ],
      ),
    );
  }

  /// Alle Ergebnisse exportieren
  Future<void> _exportAllResults() async {
    try {
      _showInfo('Exportiere alle Ergebnisse als PDF...');
      
      final pdf = pw.Document();
      
      for (final result in _filteredResults) {
        pdf.addPage(
          pw.Page(
            build: (pw.Context context) => pw.Column(
              crossAxisAlignment: pw.CrossAxisAlignment.start,
              children: [
                pw.Header(level: 0, text: result.title),
                pw.Paragraph(text: 'Typ: ${_getTypeName(result.type)}'),
                pw.Paragraph(text: 'Erstellt: ${_formatDate(result.createdAt)}'),
                pw.Divider(),
                pw.Paragraph(text: result.content),
                if (result.metadata.isNotEmpty) ...[
                  pw.Divider(),
                  pw.Header(level: 1, text: 'Metadaten'),
                  for (final entry in result.metadata.entries)
                    pw.Paragraph(text: '${entry.key}: ${entry.value}'),
                ],
                pw.Divider(thickness: 2),
              ],
            ),
          ),
        );
      }
      
      final dir = await getTemporaryDirectory();
      final file = File('${dir.path}/alle_ergebnisse_${DateTime.now().millisecondsSinceEpoch}.pdf');
      await file.writeAsBytes(await pdf.save());
      
      await Share.shareXFiles([XFile(file.path)]);
      _showInfo('Alle Ergebnisse wurden als PDF exportiert');
    } catch (e) {
      _showError('Export aller Ergebnisse fehlgeschlagen: $e');
    }
  }

  /// Filter-Dialog anzeigen
  void _showFilterDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Filter'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Typ-Filter
            DropdownButtonFormField<ResultType?>(
              value: _selectedType,
              decoration: const InputDecoration(
                labelText: 'Ergebnis-Typ',
                border: OutlineInputBorder(),
              ),
              items: [
                const DropdownMenuItem(
                  value: null,
                  child: Text('Alle Typen'),
                ),
                ...ResultType.values.map((type) => DropdownMenuItem(
                      value: type,
                      child: Row(
                        children: [
                          Icon(_getTypeIcon(type), color: _getTypeColor(type)),
                          const SizedBox(width: 8),
                          Text(_getTypeName(type)),
                        ],
                      ),
                    )),
              ],
              onChanged: (value) {
                setState(() {
                  _selectedType = value;
                });
              },
            ),
            const SizedBox(height: 16),
            
            // Favoriten-Filter
            SwitchListTile(
              title: const Text('Nur Favoriten anzeigen'),
              value: _showFavoritesOnly,
              onChanged: (value) {
                setState(() {
                  _showFavoritesOnly = value;
                });
              },
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
              _applyFilters();
              Navigator.pop(context);
            },
            child: const Text('Filter anwenden'),
          ),
        ],
      ),
    );
  }

  /// Alle Filter löschen
  void _clearFilters() {
    setState(() {
      _searchQuery = '';
      _searchController.clear();
      _selectedType = null;
      _showFavoritesOnly = false;
      _applyFilters();
    });
  }

  /// PDF erstellen
  Future<pw.Document> _createPdf(ResultData result) async {
    final pdf = pw.Document();
    
    pdf.addPage(
      pw.Page(
        build: (pw.Context context) => pw.Column(
          crossAxisAlignment: pw.CrossAxisAlignment.start,
          children: [
            pw.Header(level: 0, text: result.title),
            pw.Paragraph(text: 'Typ: ${_getTypeName(result.type)}'),
            pw.Paragraph(text: 'Erstellt: ${_formatDate(result.createdAt)}'),
            pw.Divider(),
            pw.Paragraph(text: result.content),
            if (result.metadata.isNotEmpty) ...[
              pw.Divider(),
              pw.Header(level: 1, text: 'Metadaten'),
              for (final entry in result.metadata.entries)
                pw.Paragraph(text: '${entry.key}: ${entry.value}'),
            ],
          ],
        ),
      ),
    );
    
    return pdf;
  }

  /// Hilfsmethoden
  String _formatDate(DateTime date) {
    return '${date.day}.${date.month}.${date.year} ${date.hour}:${date.minute.toString().padLeft(2, '0')}';
  }

  String _getTypeName(ResultType type) {
    switch (type) {
      case ResultType.lessonPlan:
        return 'Stundenentwurf';
      case ResultType.assessment:
        return 'Bewertungsraster';
      case ResultType.correction:
        return 'Korrekturprotokoll';
      case ResultType.curriculum:
        return 'Lehrplan';
      case ResultType.other:
        return 'Sonstiges';
    }
  }

  IconData _getTypeIcon(ResultType type) {
    switch (type) {
      case ResultType.lessonPlan:
        return Icons.school;
      case ResultType.assessment:
        return Icons.grading;
      case ResultType.correction:
        return Icons.edit_note;
      case ResultType.curriculum:
        return Icons.menu_book;
      case ResultType.other:
        return Icons.description;
    }
  }

  Color _getTypeColor(ResultType type) {
    switch (type) {
      case ResultType.lessonPlan:
        return Colors.blue;
      case ResultType.assessment:
        return Colors.green;
      case ResultType.correction:
        return Colors.orange;
      case ResultType.curriculum:
        return Colors.purple;
      case ResultType.other:
        return Colors.grey;
    }
  }

  void _showInfo(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        duration: const Duration(seconds: 2),
      ),
    );
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.red,
        duration: const Duration(seconds: 3),
      ),
    );
  }
}

/// Ergebnis-Detail-Screen
class ResultDetailScreen extends StatelessWidget {
  final ResultData result;

  const ResultDetailScreen({super.key, required this.result});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(result.title),
        actions: [
          IconButton(
            icon: const Icon(Icons.print),
            onPressed: () async {
              try {
                final pdf = await _createPdf(result);
                await Printing.layoutPdf(
                  onLayout: (format) => pdf.save(),
                );
              } catch (e) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text('Drucken fehlgeschlagen: $e'),
                    backgroundColor: Colors.red,
                  ),
                );
              }
            },
            tooltip: 'Drucken',
          ),
          IconButton(
            icon: const Icon(Icons.share),
            onPressed: () async {
              try {
                await Share.share(
                  '${result.title}\n\n${result.content}',
                  subject: result.title,
                );
              } catch (e) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text('Teilen fehlgeschlagen: $e'),
                    backgroundColor: Colors.red,
                  ),
                );
              }
            },
            tooltip: 'Teilen',
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header
            Row(
              children: [
                CircleAvatar(
                  backgroundColor: result.color.withOpacity(0.2),
                  child: Icon(result.icon, color: result.color),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        result.title,
                        style: const TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      Text(
                        'Typ: ${_getTypeName(result.type)}',
                        style: TextStyle(color: Colors.grey[600]),
                      ),
                    ],
                  ),
                ),
                if (result.isFavorite)
                  const Icon(Icons.star, color: Colors.amber),
              ],
            ),
            const SizedBox(height: 16),
            
            // Metadaten
            if (result.metadata.isNotEmpty)
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(12.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Metadaten',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 16,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Wrap(
                        spacing: 8.0,
                        runSpacing: 4.0,
                        children: result.metadata.entries.map((entry) {
                          return Chip(
                            label: Text('${entry.key}: ${entry.value}'),
                          );
                        }).toList(),
                      ),
                    ],
                  ),
                ),
              ),
            
            const SizedBox(height: 16),
            
            // Inhalt
            Card(
              child: Padding(
                padding: const EdgeInsets.all(12.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Inhalt',
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      result.content,
                      style: const TextStyle(fontSize: 14, height: 1.5),
                    ),
                  ],
                ),
              ),
            ),
            
            const SizedBox(height: 16),
            
            // Erstellungsdatum
            Text(
              'Erstellt: ${_formatDate(result.createdAt)}',
              style: TextStyle(color: Colors.grey[600], fontSize: 12),
            ),
          ],
        ),
      ),
    );
  }

  String _formatDate(DateTime date) {
    return '${date.day}.${date.month}.${date.year} ${date.hour}:${date.minute.toString().padLeft(2, '0')}';
  }

  String _getTypeName(ResultType type) {
    switch (type) {
      case ResultType.lessonPlan:
        return 'Stundenentwurf';
      case ResultType.assessment:
        return 'Bewertungsraster';
      case ResultType.correction:
        return 'Korrekturprotokoll';
      case ResultType.curriculum:
        return 'Lehrplan';
      case ResultType.other:
        return 'Sonstiges';
    }
  }

  Future<pw.Document> _createPdf(ResultData result) async {
    final pdf = pw.Document();
    
    pdf.addPage(
      pw.Page(
        build: (pw.Context context) => pw.Column(
          crossAxisAlignment: pw.CrossAxisAlignment.start,
          children: [
            pw.Header(level: 0, text: result.title),
            pw.Paragraph(text: 'Typ: ${_getTypeName(result.type)}'),
            pw.Paragraph(text: 'Erstellt: ${_formatDate(result.createdAt)}'),
            pw.Divider(),
            pw.Paragraph(text: result.content),
            if (result.metadata.isNotEmpty) ...[
              pw.Divider(),
              pw.Header(level: 1, text: 'Metadaten'),
              for (final entry in result.metadata.entries)
                pw.Paragraph(text: '${entry.key}: ${entry.value}'),
            ],
          ],
        ),
      ),
    );
    
    return pdf;
  }
}