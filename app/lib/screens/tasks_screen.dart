/// Tasks Screen für LehrerAgent
/// Zeigt laufende Agentenaufgaben und deren Status
library tasks_screen;

import 'dart:async';
import 'package:flutter/material.dart';
import '../services/openclaw_service.dart';

/// Task-Status
enum TaskStatus {
  pending,      // Ausstehend
  running,      // Läuft
  completed,    // Abgeschlossen
  failed,       // Fehlgeschlagen
  cancelled,    // Abgebrochen
}

/// Task-Daten
class TaskData {
  final String id;
  final String name;
  final String description;
  final TaskStatus status;
  final DateTime createdAt;
  final DateTime? startedAt;
  final DateTime? completedAt;
  final double progress; // 0.0 - 1.0
  final Map<String, dynamic> parameters;
  final Map<String, dynamic>? result;
  final String? error;

  TaskData({
    required this.id,
    required this.name,
    required this.description,
    required this.status,
    required this.createdAt,
    this.startedAt,
    this.completedAt,
    this.progress = 0.0,
    this.parameters = const {},
    this.result,
    this.error,
  });

  factory TaskData.fromJson(Map<String, dynamic> json) {
    return TaskData(
      id: json['id'],
      name: json['name'],
      description: json['description'],
      status: TaskStatus.values.firstWhere(
        (e) => e.toString() == json['status'],
        orElse: () => TaskStatus.pending,
      ),
      createdAt: DateTime.parse(json['createdAt']),
      startedAt: json['startedAt'] != null ? DateTime.parse(json['startedAt']) : null,
      completedAt: json['completedAt'] != null ? DateTime.parse(json['completedAt']) : null,
      progress: (json['progress'] ?? 0.0).toDouble(),
      parameters: json['parameters'] ?? {},
      result: json['result'],
      error: json['error'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'description': description,
      'status': status.toString(),
      'createdAt': createdAt.toIso8601String(),
      'startedAt': startedAt?.toIso8601String(),
      'completedAt': completedAt?.toIso8601String(),
      'progress': progress,
      'parameters': parameters,
      'result': result,
      'error': error,
    };
  }

  /// Dauer in Sekunden
  Duration? get duration {
    if (startedAt == null) return null;
    final end = completedAt ?? DateTime.now();
    return end.difference(startedAt!);
  }

  /// Fortschrittstext
  String get progressText {
    switch (status) {
      case TaskStatus.pending:
        return 'Ausstehend';
      case TaskStatus.running:
        return '${(progress * 100).toStringAsFixed(0)}%';
      case TaskStatus.completed:
        return 'Abgeschlossen';
      case TaskStatus.failed:
        return 'Fehlgeschlagen';
      case TaskStatus.cancelled:
        return 'Abgebrochen';
    }
  }

  /// Icon basierend auf Status
  IconData get icon {
    switch (status) {
      case TaskStatus.pending:
        return Icons.pending;
      case TaskStatus.running:
        return Icons.play_circle_filled;
      case TaskStatus.completed:
        return Icons.check_circle;
      case TaskStatus.failed:
        return Icons.error;
      case TaskStatus.cancelled:
        return Icons.cancel;
    }
  }

  /// Farbe basierend auf Status
  Color get color {
    switch (status) {
      case TaskStatus.pending:
        return Colors.orange;
      case TaskStatus.running:
        return Colors.blue;
      case TaskStatus.completed:
        return Colors.green;
      case TaskStatus.failed:
        return Colors.red;
      case TaskStatus.cancelled:
        return Colors.grey;
    }
  }
}

/// Tasks Screen State
class TasksScreen extends StatefulWidget {
  const TasksScreen({super.key});

  @override
  State<TasksScreen> createState() => _TasksScreenState();
}

class _TasksScreenState extends State<TasksScreen> {
  final List<TaskData> _tasks = [];
  final List<TaskData> _filteredTasks = [];
  bool _isLoading = true;
  String _searchQuery = '';
  TaskStatus? _selectedStatus;
  final TextEditingController _searchController = TextEditingController();
  Timer? _refreshTimer;

  @override
  void initState() {
    super.initState();
    _loadTasks();
    // Alle 10 Sekunden aktualisieren
    _refreshTimer = Timer.periodic(
      const Duration(seconds: 10),
      (_) => _loadTasks(),
    );
  }

  @override
  void dispose() {
    _refreshTimer?.cancel();
    super.dispose();
  }

  /// Tasks laden
  Future<void> _loadTasks() async {
    try {
      // Hier würden Tasks aus OpenClaw oder lokaler Datenbank geladen werden
      // Für Demo-Zwecke werden Beispiel-Tasks erstellt
      
      final exampleTasks = [
        TaskData(
          id: '1',
          name: 'Unterricht planen',
          description: 'Stundenentwurf für Mathematik Klasse 7 - Bruchrechnung',
          status: TaskStatus.completed,
          createdAt: DateTime.now().subtract(const Duration(minutes: 30)),
          startedAt: DateTime.now().subtract(const Duration(minutes: 32)),
          completedAt: DateTime.now().subtract(const Duration(minutes: 28)),
          progress: 1.0,
          parameters: {
            'fach': 'Mathematik',
            'klasse': '7',
            'thema': 'Bruchrechnung',
          },
          result: {
            'stundenentwurf': 'Erfolgreich erstellt',
            'dauer': '45 Minuten',
            'materialien': ['Tafel', 'Arbeitsblätter', 'Beamer'],
          },
        ),
        TaskData(
          id: '2',
          name: 'Bewertungsraster erstellen',
          description: 'Erwartungshorizont für Deutsch Gedichtanalyse',
          status: TaskStatus.running,
          createdAt: DateTime.now().subtract(const Duration(minutes: 5)),
          startedAt: DateTime.now().subtract(const Duration(minutes: 4)),
          progress: 0.65,
          parameters: {
            'fach': 'Deutsch',
            'klasse': '8',
            'thema': 'Gedichtanalyse',
          },
        ),
        TaskData(
          id: '3',
          name: 'Lehrplan einlesen',
          description: 'Bayern Mathematik Klasse 7 Curriculum',
          status: TaskStatus.pending,
          createdAt: DateTime.now().subtract(const Duration(minutes: 2)),
          progress: 0.0,
          parameters: {
            'bundesland': 'Bayern',
            'fach': 'Mathematik',
            'klasse': '7',
            'datei': 'lehrplan_bayern_mathematik_7.pdf',
          },
        ),
        TaskData(
          id: '4',
          name: 'Schülerarbeit bewerten',
          description: 'Korrektur von Klassenarbeit Englisch Present Perfect',
          status: TaskStatus.failed,
          createdAt: DateTime.now().subtract(const Duration(minutes: 15)),
          startedAt: DateTime.now().subtract(const Duration(minutes: 14)),
          completedAt: DateTime.now().subtract(const Duration(minutes: 10)),
          progress: 0.3,
          parameters: {
            'fach': 'Englisch',
            'klasse': '9',
            'thema': 'Present Perfect',
          },
          error: 'OCR konnte Handschrift nicht lesen - Konfidenz zu niedrig',
        ),
        TaskData(
          id: '5',
          name: 'Onboarding abschließen',
          description: 'Lehrerprofil und Grundeinstellungen',
          status: TaskStatus.cancelled,
          createdAt: DateTime.now().subtract(const Duration(minutes: 20)),
          startedAt: DateTime.now().subtract(const Duration(minutes: 19)),
          completedAt: DateTime.now().subtract(const Duration(minutes: 18)),
          progress: 0.5,
          parameters: {
            'aktion': 'onboarding',
          },
          error: 'Vom Benutzer abgebrochen',
        ),
      ];

      setState(() {
        _tasks.clear();
        _tasks.addAll(exampleTasks);
        _applyFilters();
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
      _showError('Fehler beim Laden der Tasks: $e');
    }
  }

  /// Filter anwenden
  void _applyFilters() {
    List<TaskData> filtered = List.from(_tasks);

    // Suchfilter
    if (_searchQuery.isNotEmpty) {
      final query = _searchQuery.toLowerCase();
      filtered = filtered.where((task) {
        return task.name.toLowerCase().contains(query) ||
            task.description.toLowerCase().contains(query) ||
            task.parameters.values.any((value) =>
                value.toString().toLowerCase().contains(query));
      }).toList();
    }

    // Statusfilter
    if (_selectedStatus != null) {
      filtered = filtered.where((task) => task.status == _selectedStatus).toList();
    }

    setState(() {
      _filteredTasks.clear();
      _filteredTasks.addAll(filtered);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Laufende Tasks'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadTasks,
            tooltip: 'Aktualisieren',
          ),
          IconButton(
            icon: const Icon(Icons.filter_list),
            onPressed: _showFilterDialog,
            tooltip: 'Filter',
          ),
          IconButton(
            icon: const Icon(Icons.add),
            onPressed: _createNewTask,
            tooltip: 'Neuen Task erstellen',
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
                hintText: 'Tasks suchen...',
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
          if (_selectedStatus != null)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 8.0),
              child: Row(
                children: [
                  Chip(
                    label: Text('Status: ${_getStatusName(_selectedStatus!)}'),
                    onDeleted: () {
                      _selectedStatus = null;
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

          // Tasks Liste
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : _filteredTasks.isEmpty
                    ? const Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.task, size: 64, color: Colors.grey),
                            SizedBox(height: 16),
                            Text(
                              'Keine Tasks gefunden',
                              style: TextStyle(
                                fontSize: 18,
                                color: Colors.grey,
                              ),
                            ),
                            SizedBox(height: 8),
                            Text(
                              'Erstellen Sie einen neuen Task oder ändern Sie Ihre Suchkriterien',
                              textAlign: TextAlign.center,
                              style: TextStyle(color: Colors.grey),
                            ),
                          ],
                        ),
                      )
                    : ListView.builder(
                        itemCount: _filteredTasks.length,
                        itemBuilder: (context, index) {
                          final task = _filteredTasks[index];
                          return _buildTaskCard(task);
                        },
                      ),
          ),

          // Statistik
          if (_filteredTasks.isNotEmpty)
            Container(
              padding: const EdgeInsets.all(8.0),
              decoration: BoxDecoration(
                color: Colors.grey[100],
                border: Border(top: BorderSide(color: Colors.grey[300]!)),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceAround,
                children: [
                  _buildStatItem(
                    'Gesamt',
                    _filteredTasks.length.toString(),
                    Icons.list,
                    Colors.blue,
                  ),
                  _buildStatItem(
                    'Laufend',
                    _filteredTasks.where((t) => t.status == TaskStatus.running).length.toString(),
                    Icons.play_arrow,
                    Colors.green,
                  ),
                  _buildStatItem(
                    'Fehler',
                    _filteredTasks.where((t) => t.status == TaskStatus.failed).length.toString(),
                    Icons.error,
                    Colors.red,
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }

  /// Task-Karte erstellen
  Widget _buildTaskCard(TaskData task) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 4.0),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: task.color.withOpacity(0.2),
          child: Icon(task.icon, color: task.color),
        ),
        title: Text(
          task.name,
          style: TextStyle(
            fontWeight: FontWeight.bold,
            color: task.status == TaskStatus.failed ? Colors.red : null,
          ),
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              task.description,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
            const SizedBox(height: 4),
            Row(
              children: [
                Expanded(
                  child: LinearProgressIndicator(
                    value: task.progress,
                    backgroundColor: Colors.grey[200],
                    color: task.color,
                  ),
                ),
                const SizedBox(width: 8),
                Text(
                  task.progressText,
                  style: TextStyle(
                    fontSize: 12,
                    color: task.color,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 4),
            Row(
              children: [
                Icon(Icons.schedule, size: 12, color: Colors.grey),
                const SizedBox(width: 4),
                Text(
                  'Erstellt: ${_formatTime(task.createdAt)}',
                  style: const TextStyle(fontSize: 11, color: Colors.grey),
                ),
                if (task.duration != null) ...[
                  const SizedBox(width: 12),
                  Icon(Icons.timer, size: 12, color: Colors.grey),
                  const SizedBox(width: 4),
                  Text(
                    'Dauer: ${_formatDuration(task.duration!)}',
                    style: const TextStyle(fontSize: 11, color: Colors.grey),
                  ),
                ],
              ],
            ),
            if (task.parameters.isNotEmpty)
              Wrap(
                spacing: 4.0,
                children: task.parameters.entries
                    .take(2)
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
          onSelected: (value) => _handleTaskAction(value, task),
          itemBuilder: (context) => _buildTaskMenuItems(task),
        ),
        onTap: () => _viewTaskDetails(task),
      ),
    );
  }

  /// Task-Menü-Items erstellen
  List<PopupMenuEntry<String>> _buildTaskMenuItems(TaskData task) {
    final items = <PopupMenuEntry<String>>[];

    items.add(const PopupMenuItem(
      value: 'view',
      child: ListTile(
        leading: Icon(Icons.visibility),
        title: Text('Details'),
      ),
    ));

    if (task.status == TaskStatus.pending || task.status == TaskStatus.running) {
      items.add(PopupMenuItem(
        value: 'cancel',
        child: ListTile(
          leading: const Icon(Icons.cancel, color: Colors.orange),
          title: const Text('Abbrechen', style: TextStyle(color: Colors.orange)),
        ),
      ));
    }

    if (task.status == TaskStatus.running) {
      items.add(PopupMenuItem(
        value: 'pause',
        child: ListTile(
          leading: const Icon(Icons.pause),
          title: const Text('Pausieren'),
        ),
      ));
    }

    if (task.status == TaskStatus.pending) {
      items.add(PopupMenuItem(
        value: 'start',
        child: ListTile(
          leading: const Icon(Icons.play_arrow),
          title: const Text('Starten'),
        ),
      ));
    }

    if (task.status == TaskStatus.completed && task.result != null) {
      items.add(const PopupMenuDivider());
      items.add(const PopupMenuItem(
        value: 'view_result',
        child: ListTile(
          leading: Icon(Icons.description),
          title: Text('Ergebnis anzeigen'),
        ),
      ));
    }

    items.add(const PopupMenuDivider());
    items.add(PopupMenuItem(
      value: 'delete',
      child: ListTile(
        leading: const Icon(Icons.delete, color: Colors.red),
        title: const Text('Löschen', style: TextStyle(color: Colors.red)),
      ),
    ));

    return items;
  }

  /// Task-Aktion behandeln
  void _handleTaskAction(String action, TaskData task) {
    switch (action) {
      case 'view':
        _viewTaskDetails(task);
        break;
      case 'cancel':
        _cancelTask(task);
        break;
      case 'pause':
        _pauseTask(task);
        break;
      case 'start':
        _startTask(task);
        break;
      case 'view_result':
        _viewTaskResult(task);
        break;
      case 'delete':
        _deleteTask(task);
        break;
    }
  }

  /// Task-Details anzeigen
  void _viewTaskDetails(TaskData task) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => TaskDetailScreen(task: task),
      ),
    );
  }

  /// Task abbrechen
  void _cancelTask(TaskData task) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Task abbrechen'),
        content: Text('Möchten Sie "${task.name}" wirklich abbrechen?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Nein'),
          ),
          ElevatedButton(
            onPressed: () {
              // Hier würde der Task tatsächlich abgebrochen werden
              setState(() {
                final index = _tasks.indexWhere((t) => t.id == task.id);
                if (index != -1) {
                  _tasks[index] = TaskData(
                    id: task.id,
                    name: task.name,
                    description: task.description,
                    status: TaskStatus.cancelled,
                    createdAt: task.createdAt,
                    startedAt: task.startedAt,
                    completedAt: DateTime.now(),
                    progress: task.progress,
                    parameters: task.parameters,
                    error: 'Vom Benutzer abgebrochen',
                  );
                  _applyFilters();
                }
              });
              Navigator.pop(context);
              _showInfo('Task wurde abgebrochen');
            },
            style: ElevatedButton.styleFrom(backgroundColor: Colors.orange),
            child: const Text('Ja, abbrechen'),
          ),
        ],
      ),
    );
  }

  /// Task pausieren
  void _pauseTask(TaskData task) {
    _showInfo('Pausieren-Funktion für "${task.name}" wird implementiert...');
  }

  /// Task starten
  void _startTask(TaskData task) {
    setState(() {
      final index = _tasks.indexWhere((t) => t.id == task.id);
      if (index != -1) {
        _tasks[index] = TaskData(
          id: task.id,
          name: task.name,
          description: task.description,
          status: TaskStatus.running,
          createdAt: task.createdAt,
          startedAt: DateTime.now(),
          progress: 0.1,
          parameters: task.parameters,
        );
        _applyFilters();
      }
    });
    _showInfo('Task "${task.name}" wurde gestartet');
  }

  /// Task-Ergebnis anzeigen
  void _viewTaskResult(TaskData task) {
    if (task.result == null) return;
    
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Ergebnis: ${task.name}'),
        content: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              for (final entry in task.result!.entries)
                Padding(
                  padding: const EdgeInsets.only(bottom: 8.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '${entry.key}:',
                        style: const TextStyle(fontWeight: FontWeight.bold),
                      ),
                      Text(
                        entry.value.toString(),
                        style: const TextStyle(color: Colors.grey[700]),
                      ),
                    ],
                  ),
                ),
            ],
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

  /// Task löschen
  void _deleteTask(TaskData task) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Task löschen'),
        content: Text('Möchten Sie "${task.name}" wirklich löschen?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Abbrechen'),
          ),
          ElevatedButton(
            onPressed: () {
              setState(() {
                _tasks.removeWhere((t) => t.id == task.id);
                _applyFilters();
              });
              Navigator.pop(context);
              _showInfo('Task wurde gelöscht');
            },
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            child: const Text('Löschen'),
          ),
        ],
      ),
    );
  }

  /// Neuen Task erstellen
  void _createNewTask() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Neuen Task erstellen'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              decoration: const InputDecoration(
                labelText: 'Task-Name',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              decoration: const InputDecoration(
                labelText: 'Beschreibung',
                border: OutlineInputBorder(),
              ),
              maxLines: 3,
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              decoration: const InputDecoration(
                labelText: 'Task-Typ',
                border: OutlineInputBorder(),
              ),
              items: const [
                DropdownMenuItem(value: 'lesson_plan', child: Text('Unterricht planen')),
                DropdownMenuItem(value: 'assessment', child: Text('Bewertungsraster erstellen')),
                DropdownMenuItem(value: 'curriculum', child: Text('Lehrplan einlesen')),
                DropdownMenuItem(value: 'correction', child: Text('Schülerarbeit bewerten')),
              ],
              onChanged: (value) {},
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
              // Hier würde der neue Task erstellt werden
              Navigator.pop(context);
              _showInfo('Neuer Task wurde erstellt');
            },
            child: const Text('Erstellen'),
          ),
        ],
      ),
    );
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
            DropdownButtonFormField<TaskStatus?>(
              value: _selectedStatus,
              decoration: const InputDecoration(
                labelText: 'Task-Status',
                border: OutlineInputBorder(),
              ),
              items: [
                const DropdownMenuItem(
                  value: null,
                  child: Text('Alle Status'),
                ),
                ...TaskStatus.values.map((status) => DropdownMenuItem(
                      value: status,
                      child: Row(
                        children: [
                          Icon(_getStatusIcon(status), color: _getStatusColor(status)),
                          const SizedBox(width: 8),
                          Text(_getStatusName(status)),
                        ],
                      ),
                    )),
              ],
              onChanged: (value) {
                setState(() {
                  _selectedStatus = value;
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
      _selectedStatus = null;
      _applyFilters();
    });
  }

  /// Statistik-Item erstellen
  Widget _buildStatItem(String label, String value, IconData icon, Color color) {
    return Column(
      children: [
        Icon(icon, color: color, size: 24),
        const SizedBox(height: 4),
        Text(
          value,
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
            color: color,
          ),
        ),
        Text(
          label,
          style: const TextStyle(fontSize: 12, color: Colors.grey),
        ),
      ],
    );
  }

  /// Hilfsmethoden
  String _formatTime(DateTime date) {
    final now = DateTime.now();
    final difference = now.difference(date);
    
    if (difference.inMinutes < 1) {
      return 'Gerade eben';
    } else if (difference.inHours < 1) {
      return 'Vor ${difference.inMinutes} min';
    } else if (difference.inDays < 1) {
      return 'Vor ${difference.inHours} h';
    } else {
      return '${date.day}.${date.month}.${date.year}';
    }
  }

  String _formatDuration(Duration duration) {
    if (duration.inMinutes < 1) {
      return '${duration.inSeconds} s';
    } else if (duration.inHours < 1) {
      return '${duration.inMinutes} min';
    } else {
      return '${duration.inHours} h ${duration.inMinutes.remainder(60)} min';
    }
  }

  String _getStatusName(TaskStatus status) {
    switch (status) {
      case TaskStatus.pending:
        return 'Ausstehend';
      case TaskStatus.running:
        return 'Läuft';
      case TaskStatus.completed:
        return 'Abgeschlossen';
      case TaskStatus.failed:
        return 'Fehlgeschlagen';
      case TaskStatus.cancelled:
        return 'Abgebrochen';
    }
  }

  IconData _getStatusIcon(TaskStatus status) {
    switch (status) {
      case TaskStatus.pending:
        return Icons.pending;
      case TaskStatus.running:
        return Icons.play_circle_filled;
      case TaskStatus.completed:
        return Icons.check_circle;
      case TaskStatus.failed:
        return Icons.error;
      case TaskStatus.cancelled:
        return Icons.cancel;
    }
  }

  Color _getStatusColor(TaskStatus status) {
    switch (status) {
      case TaskStatus.pending:
        return Colors.orange;
      case TaskStatus.running:
        return Colors.blue;
      case TaskStatus.completed:
        return Colors.green;
      case TaskStatus.failed:
        return Colors.red;
      case TaskStatus.cancelled:
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

/// Task-Detail-Screen
class TaskDetailScreen extends StatelessWidget {
  final TaskData task;

  const TaskDetailScreen({super.key, required this.task});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(task.name),
        actions: [
          if (task.status == TaskStatus.completed && task.result != null)
            IconButton(
              icon: const Icon(Icons.download),
              onPressed: () {
                // Hier würde das Ergebnis exportiert werden
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text('Ergebnis wird exportiert...'),
                  ),
                );
              },
              tooltip: 'Ergebnis exportieren',
            ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Row(
                  children: [
                    CircleAvatar(
                      backgroundColor: task.color.withOpacity(0.2),
                      radius: 30,
                      child: Icon(task.icon, color: task.color, size: 30),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            task.name,
                            style: const TextStyle(
                              fontSize: 20,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            task.description,
                            style: TextStyle(color: Colors.grey[600]),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
            
            const SizedBox(height: 16),
            
            // Status & Fortschritt
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Status & Fortschritt',
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                      ),
                    ),
                    const SizedBox(height: 12),
                    
                    Row(
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                _getStatusName(task.status),
                                style: TextStyle(
                                  fontSize: 18,
                                  color: task.color,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              const SizedBox(height: 8),
                              LinearProgressIndicator(
                                value: task.progress,
                                backgroundColor: Colors.grey[200],
                                color: task.color,
                                minHeight: 8,
                              ),
                              const SizedBox(height: 4),
                              Text(
                                '${(task.progress * 100).toStringAsFixed(0)}% abgeschlossen',
                                style: const TextStyle(fontSize: 12, color: Colors.grey),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(width: 16),
                        Column(
                          children: [
                            const Icon(Icons.schedule, color: Colors.grey),
                            const SizedBox(height: 4),
                            Text(
                              task.duration != null
                                  ? _formatDuration(task.duration!)
                                  : '-',
                              style: const TextStyle(fontSize: 12, color: Colors.grey),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            
            const SizedBox(height: 16),
            
            // Zeitstempel
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Zeitstempel',
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                      ),
                    ),
                    const SizedBox(height: 12),
                    
                    _buildTimeItem('Erstellt', task.createdAt),
                    if (task.startedAt != null)
                      _buildTimeItem('Gestartet', task.startedAt!),
                    if (task.completedAt != null)
                      _buildTimeItem('Abgeschlossen', task.completedAt!),
                  ],
                ),
              ),
            ),
            
            const SizedBox(height: 16),
            
            // Parameter
            if (task.parameters.isNotEmpty)
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Parameter',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 16,
                        ),
                      ),
                      const SizedBox(height: 12),
                      
                      Wrap(
                        spacing: 8.0,
                        runSpacing: 4.0,
                        children: task.parameters.entries.map((entry) {
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
            
            // Ergebnis
            if (task.result != null && task.result!.isNotEmpty)
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Ergebnis',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 16,
                        ),
                      ),
                      const SizedBox(height: 12),
                      
                      for (final entry in task.result!.entries)
                        Padding(
                          padding: const EdgeInsets.only(bottom: 8.0),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                '${entry.key}:',
                                style: const TextStyle(fontWeight: FontWeight.bold),
                              ),
                              Text(
                                entry.value.toString(),
                                style: const TextStyle(color: Colors.grey[700]),
                              ),
                            ],
                          ),
                        ),
                    ],
                  ),
                ),
              ),
            
            const SizedBox(height: 16),
            
            // Fehler
            if (task.error != null)
              Card(
                color: Colors.red[50],
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Row(
                        children: [
                          Icon(Icons.error, color: Colors.red),
                          SizedBox(width: 8),
                          Text(
                            'Fehler',
                            style: TextStyle(
                              fontWeight: FontWeight.bold,
                              fontSize: 16,
                              color: Colors.red,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Text(
                        task.error!,
                        style: const TextStyle(color: Colors.red),
                      ),
                    ],
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildTimeItem(String label, DateTime time) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8.0),
      child: Row(
        children: [
          Expanded(
            child: Text(
              label,
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
          ),
          Text(
            '${time.hour.toString().padLeft(2, '0')}:${time.minute.toString().padLeft(2, '0')} Uhr',
            style: const TextStyle(color: Colors.grey),
          ),
        ],
      ),
    );
  }

  String _formatDuration(Duration duration) {
    if (duration.inMinutes < 1) {
      return '${duration.inSeconds} s';
    } else if (duration.inHours < 1) {
      return '${duration.inMinutes} min';
    } else {
      return '${duration.inHours} h ${duration.inMinutes.remainder(60)} min';
    }
  }

  String _getStatusName(TaskStatus status) {
    switch (status) {
      case TaskStatus.pending:
        return 'Ausstehend';
      case TaskStatus.running:
        return 'Läuft';
      case TaskStatus.completed:
        return 'Abgeschlossen';
      case TaskStatus.failed:
        return 'Fehlgeschlagen';
      case TaskStatus.cancelled:
        return 'Abgebrochen';
    }
  }
}

