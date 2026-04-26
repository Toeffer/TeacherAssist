/// Chat Screen für LehrerAgent
/// Haupt-Chat-Interface für die Kommunikation mit dem Agenten
library chat_screen;

import 'dart:async';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../services/openclaw_service.dart';
import '../services/connection_manager.dart';
import '../widgets/message_bubble.dart';
import '../widgets/file_upload_button.dart';
import '../widgets/quick_actions.dart';
import '../widgets/connection_indicator.dart';

/// Chat-Nachricht
class ChatMessage {
  final String id;
  final String content;
  final DateTime timestamp;
  final bool isUser;
  final MessageType type;
  final Map<String, dynamic>? metadata;

  ChatMessage({
    required this.id,
    required this.content,
    required this.timestamp,
    required this.isUser,
    this.type = MessageType.text,
    this.metadata,
  });

  factory ChatMessage.fromJson(Map<String, dynamic> json) {
    return ChatMessage(
      id: json['id'],
      content: json['content'],
      timestamp: DateTime.parse(json['timestamp']),
      isUser: json['isUser'],
      type: MessageType.values.firstWhere(
        (e) => e.toString() == json['type'],
        orElse: () => MessageType.text,
      ),
      metadata: json['metadata'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'content': content,
      'timestamp': timestamp.toIso8601String(),
      'isUser': isUser,
      'type': type.toString(),
      'metadata': metadata,
    };
  }
}

/// Chat Screen State
class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final List<ChatMessage> _messages = [];
  final TextEditingController _textController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final FocusNode _focusNode = FocusNode();
  bool _isLoading = false;
  bool _showQuickActions = true;
  StreamSubscription? _openClawSubscription;
  final _openClawService = openClawService;
  final _connectionManager = connectionManager;

  @override
  void initState() {
    super.initState();
    _loadInitialMessages();
    _setupOpenClawListener();
  }

  @override
  void dispose() {
    _openClawSubscription?.cancel();
    _textController.dispose();
    _scrollController.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  /// Initiale Nachrichten laden
  void _loadInitialMessages() {
    // Willkommensnachricht
    _addMessage(
      ChatMessage(
        id: 'welcome',
        content: 'Hallo! Ich bin Ihr LehrerAgent-Assistent. '
            'Wie kann ich Ihnen heute helfen?\n\n'
            'Ich kann Ihnen bei folgenden Aufgaben helfen:\n'
            '• Unterricht planen – Stundenentwürfe mit Lehrplanbezug\n'
            '• Arbeitsblatt oder Prüfung erstellen – druckfertig mit AFB-Verteilung\n'
            '• Bewertungsraster & Erwartungshorizonte erstellen\n'
            '• Schülerarbeiten bewerten – per Foto oder PDF\n'
            '• Elternbriefe schreiben – für jeden Anlass\n'
            '• Zeugnisformulierungen generieren – 3 Varianten je SuS\n'
            '• Förderpläne erstellen – mit SMART-Zielen\n'
            '• Klassenstatistik auswerten – Notenspiegel & Aufgabenanalyse\n'
            '• Lehrpläne einlesen und semantisch durchsuchen',
        timestamp: DateTime.now().subtract(const Duration(seconds: 1)),
        isUser: false,
        type: MessageType.system,
      ),
    );
  }

  /// OpenClaw Listener einrichten
  void _setupOpenClawListener() {
    _openClawSubscription = _openClawService.messageStream.listen((message) {
      if (message.type == OpenClawMessageType.skillResponse) {
        _handleSkillResponse(message);
      } else if (message.type == OpenClawMessageType.toolResponse) {
        _handleToolResponse(message);
      } else if (message.type == OpenClawMessageType.error) {
        _handleError(message);
      }
    });
  }

  /// Skill-Antwort verarbeiten
  void _handleSkillResponse(OpenClawMessage message) {
    final data = message.data;
    final skillName = data['skill'] ?? 'Unbekannter Skill';
    final result = data['result'] ?? {};
    
    setState(() {
      _isLoading = false;
    });
    
    _addMessage(
      ChatMessage(
        id: 'skill_${DateTime.now().millisecondsSinceEpoch}',
        content: _formatSkillResponse(skillName, result),
        timestamp: DateTime.now(),
        isUser: false,
        type: MessageType.result,
        metadata: {
          'skill': skillName,
          'result': result,
        },
      ),
    );
  }

  /// Tool-Antwort verarbeiten
  void _handleToolResponse(OpenClawMessage message) {
    final data = message.data;
    final toolName = data['tool'] ?? 'Unbekanntes Tool';
    final success = data['success'] ?? false;
    
    if (!success) {
      final error = data['error'] ?? 'Unbekannter Fehler';
      _addMessage(
        ChatMessage(
          id: 'tool_error_${DateTime.now().millisecondsSinceEpoch}',
          content: 'Tool-Fehler ($toolName): $error',
          timestamp: DateTime.now(),
          isUser: false,
          type: MessageType.error,
        ),
      );
    }
  }

  /// Fehler verarbeiten
  void _handleError(OpenClawMessage message) {
    final error = message.data['error'] ?? 'Unbekannter Fehler';
    
    setState(() {
      _isLoading = false;
    });
    
    _addMessage(
      ChatMessage(
        id: 'error_${DateTime.now().millisecondsSinceEpoch}',
        content: 'Fehler: $error',
        timestamp: DateTime.now(),
        isUser: false,
        type: MessageType.error,
      ),
    );
  }

  /// Skill-Antwort formatieren
  String _formatSkillResponse(String skillName, Map<String, dynamic> result) {
    switch (skillName) {
      case 'unterricht_planen':
        return _formatLessonPlanResponse(result);
      case 'bewertung_erstellen':
        return _formatAssessmentResponse(result);
      case 'lehrplan_einlesen':
        return _formatCurriculumResponse(result);
      case 'schuelerarbeit_bewerten':
        return _formatCorrectionResponse(result);
      case 'onboarding':
        return _formatOnboardingResponse(result);
      case 'arbeitsblatt_erstellen':
        return '📄 **Arbeitsblatt erstellt**\n\n'
            'Fach: ${result['fach'] ?? '—'} | Klasse: ${result['klasse'] ?? '—'}\n'
            'Thema: ${result['thema'] ?? '—'}\n\n'
            'Das Arbeitsblatt ist druckfertig. '
            'Klicke auf den Export-Button, um es als PDF zu speichern.';
      case 'pruefung_erstellen':
        return '📝 **Prüfung erstellt**\n\n'
            'Art: ${result['art'] ?? 'Klassenarbeit'} | '
            'Fach: ${result['fach'] ?? '—'} | Klasse: ${result['klasse'] ?? '—'}\n'
            'Gesamtpunkte: ${result['gesamtpunkte'] ?? '—'}\n\n'
            'Schülerversion und Erwartungshorizont sind druckfertig.';
      case 'elternbrief_schreiben':
        return '✉️ **Elternbrief erstellt**\n\n'
            'Anlass: ${result['anlass'] ?? '—'} | Klasse: ${result['klasse'] ?? '—'}\n\n'
            'Der Brief ist druckfertig. '
            'Klicke auf den Export-Button, um ihn auszudrucken.';
      case 'zeugnis_formulieren':
        return '🎓 **Zeugnisformulierungen erstellt**\n\n'
            'Fach: ${result['fach'] ?? '—'} | Note: ${result['note'] ?? '—'}\n\n'
            '3 Varianten wurden generiert (kompakt / ausführlich / entwicklungsorientiert). '
            'Bitte Pronomen manuell anpassen.';
      case 'foerderplan_erstellen':
        return '📋 **Förderplan erstellt**\n\n'
            'Bereich: ${result['foerderbereich'] ?? '—'} | Klasse: ${result['klasse'] ?? '—'}\n\n'
            'Der Plan enthält SMART-Ziele, Maßnahmentabelle und Evaluationsplan. '
            'Bitte Schüler-Kürzel (SuS-XX) manuell ergänzen.';
      case 'klassenstatistik':
        return '📊 **Klassenauswertung erstellt**\n\n'
            'Klasse: ${result['klasse'] ?? '—'} | '
            'Durchschnitt: ${result['durchschnitt'] ?? '—'}\n\n'
            'Notenspiegel und Empfehlungen wurden generiert.';
      default:
        return 'Skill "$skillName" wurde ausgeführt.\n'
            'Ergebnis: ${result.toString()}';
    }
  }

  /// Stundenentwurf-Antwort formatieren
  String _formatLessonPlanResponse(Map<String, dynamic> result) {
    final subject = result['fach'] ?? 'Unbekanntes Fach';
    final grade = result['klasse'] ?? 'Unbekannte Klasse';
    final topic = result['thema'] ?? 'Unbekanntes Thema';
    final duration = result['dauer'] ?? '45 Minuten';
    final materials = (result['materialien'] as List<dynamic>?)?.join(', ') ?? 'Keine';
    
    return '''
✅ **Stundenentwurf erstellt**

**Fach:** $subject
**Klasse:** $grade
**Thema:** $topic
**Dauer:** $duration
**Materialien:** $materials

**Ablauf:**
1. Einstieg (5 min): ${result['einstieg'] ?? 'Aktivierung des Vorwissens'}
2. Erarbeitung (25 min): ${result['erarbeitung'] ?? 'Neue Inhalte einführen'}
3. Sicherung (10 min): ${result['sicherung'] ?? 'Ergebnisse festhalten'}
4. Hausaufgabe (5 min): ${result['hausaufgabe'] ?? 'Vertiefende Aufgabe'}

**Kompetenzen:** ${result['kompetenzen'] ?? 'Fachliche und methodische Kompetenzen'}
**AFB-Verteilung:** ${result['afb_verteilung'] ?? 'I: 30%, II: 40%, III: 30%'}
''';
  }

  /// Bewertungsraster-Antwort formatieren
  String _formatAssessmentResponse(Map<String, dynamic> result) {
    final subject = result['fach'] ?? 'Unbekanntes Fach';
    final grade = result['klasse'] ?? 'Unbekannte Klasse';
    final topic = result['thema'] ?? 'Unbekanntes Thema';
    final criteriaCount = result['kriterien_anzahl'] ?? 5;
    final maxPoints = result['max_punkte'] ?? 15;
    
    return '''
📋 **Bewertungsraster erstellt**

**Fach:** $subject
**Klasse:** $grade
**Thema:** $topic
**Kriterien:** $criteriaCount
**Maximale Punkte:** $maxPoints

**Notenschlüssel:**
• 100-90%: Sehr gut (1)
• 89-80%: Gut (2)
• 79-65%: Befriedigend (3)
• 64-50%: Ausreichend (4)
• 49-25%: Mangelhaft (5)
• 24-0%: Ungenügend (6)

**Kriterien:**
${_formatCriteriaList(result['kriterien'])}
''';
  }

  /// Kriterienliste formatieren
  String _formatCriteriaList(dynamic criteria) {
    if (criteria is! List) return '• Keine Kriterien definiert';
    
    final buffer = StringBuffer();
    for (var i = 0; i < criteria.length; i++) {
      final criterion = criteria[i];
      buffer.writeln('${i + 1}. ${criterion['name']}: ${criterion['punkte']} Punkte');
      if (criterion['beschreibung'] != null) {
        buffer.writeln('   ${criterion['beschreibung']}');
      }
    }
    return buffer.toString();
  }

  /// Lehrplan-Antwort formatieren
  String _formatCurriculumResponse(Map<String, dynamic> result) {
    final state = result['bundesland'] ?? 'Unbekanntes Bundesland';
    final subject = result['fach'] ?? 'Unbekanntes Fach';
    final grade = result['klasse'] ?? 'Unbekannte Klasse';
    final chunks = result['chunks_indexed'] ?? 0;
    final source = result['quelle'] ?? 'Unbekannte Quelle';
    
    return '''
📚 **Lehrplan eingelesen**

**Bundesland:** $state
**Fach:** $subject
**Klasse:** $grade
**Quelle:** $source
**Textabschnitte:** $chunks

Der Lehrplan wurde erfolgreich in die semantische Datenbank eingelesen und ist jetzt durchsuchbar.

**Verwendung:**
• Unterrichtsplanung: "Planen Sie eine Stunde zu [Thema]"
• Kompetenzsuche: "Welche Kompetenzen werden in Klasse $grade erwartet?"
• Materialempfehlung: "Empfehlen Sie Materialien zu [Thema]"
''';
  }

  /// Korrektur-Antwort formatieren
  String _formatCorrectionResponse(Map<String, dynamic> result) {
    final studentCount = result['anzahl_schueler'] ?? 0;
    final avgGrade = result['durchschnittsnote'] ?? 'n/a';
    final commonErrors = (result['haeufige_fehler'] as List<dynamic>?)?.join(', ') ?? 'Keine';
    
    return '''
✏️ **Korrekturprotokoll erstellt**

**Anzahl Schüler:** $studentCount
**Durchschnittsnote:** $avgGrade
**Häufige Fehler:** $commonErrors

**Empfehlungen:**
1. **Nachbereitung:** Besprechen Sie die häufigsten Fehler in der nächsten Stunde
2. **Förderung:** Bieten Sie individuelles Feedback für Schüler mit besonderen Schwierigkeiten
3. **Dokumentation:** Das Protokoll wurde in Ihrer Memory-Datei gespeichert

**Hinweis:** Alle Schülerdaten wurden anonymisiert gemäß DSGVO.
''';
  }

  /// Onboarding-Antwort formatieren
  String _formatOnboardingResponse(Map<String, dynamic> result) {
    final completed = result['completed'] ?? false;
    
    if (completed) {
      return '''
🎉 **Onboarding abgeschlossen!**

Ihr Lehrerprofil wurde erfolgreich erstellt und alle Grundeinstellungen sind konfiguriert.

**Nächste Schritte:**
1. **Lehrpläne einlesen:** Laden Sie Ihre Lehrplandokumente hoch
2. **Erste Unterrichtsplanung:** Testen Sie die Planungsfunktion
3. **Bewertungsraster:** Erstellen Sie Ihr erstes Bewertungsraster

**Tipp:** Verwenden Sie die Quick-Actions für häufig genutzte Funktionen.
''';
    } else {
      return '''
⚠️ **Onboarding nicht abgeschlossen**

Bitte vervollständigen Sie Ihr Lehrerprofil, um alle Funktionen nutzen zu können.

**Fehlende Informationen:**
${result['missing_fields']?.join('\n') ?? 'Unbekannt'}
''';
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDesktop = MediaQuery.of(context).size.width > 600;
    
    return Scaffold(
      appBar: AppBar(
        title: const Text('LehrerAgent Chat'),
        actions: [
          const ConnectionIndicator(),
          IconButton(
            icon: const Icon(Icons.help_outline),
            onPressed: _showHelp,
            tooltip: 'Hilfe',
          ),
          IconButton(
            icon: const Icon(Icons.history),
            onPressed: _showHistory,
            tooltip: 'Chat-Verlauf',
          ),
        ],
      ),
      body: Column(
        children: [
          // Chat-Nachrichten
          Expanded(
            child: _buildChatList(isDesktop),
          ),
          
          // Quick-Actions (nur auf Mobile oder wenn aktiviert)
          if (_showQuickActions && !isDesktop)
            QuickActionsBar(
              actions: LehrerAgentQuickActions.frequentActions(
                callbacks: {
                  'unterricht_planen': () => _handleQuickAction('plan_lesson'),
                  'bewertung_erstellen': () => _handleQuickAction('create_assessment'),
                  'pruefung_erstellen': () => _handleQuickAction('create_exam'),
                  'arbeitsblatt_erstellen': () => _handleQuickAction('create_worksheet'),
                  'elternbrief_schreiben': () => _handleQuickAction('write_letter'),
                  'schuelerarbeit_bewerten': () => _handleQuickAction('correct_work'),
                  'pdf_upload': () => _handleQuickAction('pdf_upload'),
                },
              ),
            ),
          
          // Eingabebereich
          _buildInputArea(isDesktop),
        ],
      ),
    );
  }

  /// Chat-Liste erstellen
  Widget _buildChatList(bool isDesktop) {
    return Container(
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.background,
      ),
      child: ListView.builder(
        controller: _scrollController,
        padding: EdgeInsets.only(
          top: 8,
          bottom: 8,
          left: isDesktop ? 24 : 8,
          right: isDesktop ? 24 : 8,
        ),
        itemCount: _messages.length + (_isLoading ? 1 : 0),
        itemBuilder: (context, index) {
          if (index < _messages.length) {
            final message = _messages[index];
            return MessageBubble(
              message: message.content,
              type: message.isUser ? MessageType.user : message.type,
              timestamp: message.timestamp,
              isDesktop: isDesktop,
              onCopy: () => _copyToClipboard(message.content),
              onShare: () => _shareMessage(message),
              onSave: () => _saveMessage(message),
            );
          } else {
            // Lade-Indikator
            return Padding(
              padding: const EdgeInsets.all(16.0),
              child: Row(
                children: [
                  const CircleAvatar(
                    backgroundColor: Colors.blue,
                    child: Icon(Icons.auto_awesome, color: Colors.white, size: 20),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'LehrerAgent denkt nach...',
                          style: TextStyle(
                            fontWeight: FontWeight.bold,
                            color: Theme.of(context).colorScheme.primary,
                          ),
                        ),
                        const SizedBox(height: 4),
                        const LinearProgressIndicator(),
                      ],
                    ),
                  ),
                ],
              ),
            );
          }
        },
      ),
    );
  }

  /// Eingabebereich erstellen
  Widget _buildInputArea(bool isDesktop) {
    return Container(
      padding: EdgeInsets.symmetric(
        horizontal: isDesktop ? 24 : 8,
        vertical: 8,
      ),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surface,
        border: Border(top: BorderSide(color: Theme.of(context).dividerColor)),
      ),
      child: Column(
        children: [
          // Datei-Upload
          Row(
            children: [
              Expanded(
                child: FileUploadButton(
                  onFileSelected: (File file, String fileType) =>
                      _handleFileUpload(file, fileType),
                  maxFileSize: 10 * 1024 * 1024, // 10 MB
                  allowedExtensions: const ['pdf', 'jpg', 'jpeg', 'png', 'txt'],
                ),
              ),
              if (isDesktop)
                IconButton(
                  icon: const Icon(Icons.more_vert),
                  onPressed: _toggleQuickActions,
                  tooltip: 'Mehr Optionen',
                ),
            ],
          ),
          
          const SizedBox(height: 8),
          
          // Texteingabe
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _textController,
                  focusNode: _focusNode,
                  decoration: InputDecoration(
                    hintText: 'Nachricht eingeben...',
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(24),
                    ),
                    contentPadding: const EdgeInsets.symmetric(
                      horizontal: 16,
                      vertical: 12,
                    ),
                    suffixIcon: IconButton(
                      icon: const Icon(Icons.send),
                      onPressed: _sendMessage,
                      tooltip: 'Senden',
                    ),
                  ),
                  maxLines: 3,
                  minLines: 1,
                  textInputAction: TextInputAction.send,
                  onSubmitted: (_) => _sendMessage(),
                ),
              ),
              
              if (!isDesktop)
                IconButton(
                  icon: Icon(_showQuickActions ? Icons.keyboard_arrow_up : Icons.keyboard_arrow_down),
                  onPressed: _toggleQuickActions,
                  tooltip: 'Quick-Actions',
                ),
            ],
          ),
        ],
      ),
    );
  }

  /// Nachricht senden
  void _sendMessage() {
    final text = _textController.text.trim();
    if (text.isEmpty) return;
    
    // Benutzernachricht hinzufügen
    _addMessage(
      ChatMessage(
        id: 'user_${DateTime.now().millisecondsSinceEpoch}',
        content: text,
        timestamp: DateTime.now(),
        isUser: true,
      ),
    );
    
    // Texteingabe leeren
    _textController.clear();
    
    // Skill basierend auf Nachricht erkennen
    final skill = _detectSkill(text);
    
    setState(() {
      _isLoading = true;
    });
    
    // Skill ausführen
    _executeSkill(skill, text);
  }

  /// Skill basierend auf Nachricht erkennen
  String _detectSkill(String text) {
    final lowerText = text.toLowerCase();
    
    if (lowerText.contains('prüfung') ||
        lowerText.contains('klassenarbeit') ||
        lowerText.contains('klausur') ||
        lowerText.contains('kurztest')) {
      return 'pruefung_erstellen';
    } else if (lowerText.contains('arbeitsblatt') ||
               lowerText.contains('aufgabenblatt') ||
               lowerText.contains('übungsblatt')) {
      return 'arbeitsblatt_erstellen';
    } else if (lowerText.contains('elternbrief') ||
               lowerText.contains('brief an eltern') ||
               lowerText.contains('elternschreiben')) {
      return 'elternbrief_schreiben';
    } else if (lowerText.contains('zeugnis') ||
               lowerText.contains('zeugnistext') ||
               lowerText.contains('zeugnisformulierung')) {
      return 'zeugnis_formulieren';
    } else if (lowerText.contains('förderplan') ||
               lowerText.contains('individuelle förderung') ||
               lowerText.contains('fördermaßnahmen')) {
      return 'foerderplan_erstellen';
    } else if (lowerText.contains('klassenstatistik') ||
               lowerText.contains('notenverteilung') ||
               lowerText.contains('notenspiegel') ||
               lowerText.contains('auswertung')) {
      return 'klassenstatistik';
    } else if (lowerText.contains('unterricht') ||
               lowerText.contains('stunde') ||
               lowerText.contains('plan')) {
      return 'unterricht_planen';
    } else if (lowerText.contains('bewertung') ||
               lowerText.contains('raster') ||
               lowerText.contains('erwartungshorizont')) {
      return 'bewertung_erstellen';
    } else if (lowerText.contains('lehrplan') ||
               lowerText.contains('curriculum') ||
               lowerText.contains('vorgabe')) {
      return 'lehrplan_einlesen';
    } else if (lowerText.contains('korrektur') ||
               lowerText.contains('schülerarbeit') ||
               lowerText.contains('bewerte diese')) {
      return 'schuelerarbeit_bewerten';
    } else if (lowerText.contains('hilfe') ||
               lowerText.contains('was kann') ||
               lowerText.contains('funktion')) {
      return 'help';
    } else {
      return 'general';
    }
  }

  /// Skill ausführen
  Future<void> _executeSkill(String skill, String text) async {
    try {
      if (!_connectionManager.isConnected) {
        throw Exception('Nicht mit OpenClaw verbunden (Status: ${_connectionManager.currentStatus})');
      }
      
      final parameters = _extractParameters(skill, text);
      
      await _openClawService.executeSkill(
        skillName: skill,
        parameters: parameters,
      );
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
      _addMessage(
        ChatMessage(
          id: 'error_${DateTime.now().millisecondsSinceEpoch}',
          content: 'Fehler: $e',
          timestamp: DateTime.now(),
          isUser: false,
          type: MessageType.error,
        ),
      );
    }
  }

  /// Parameter aus Text extrahieren
  Map<String, dynamic> _extractParameters(String skill, String text) {
    final parameters = <String, dynamic>{};
    final lowerText = text.toLowerCase();
    
    switch (skill) {
      case 'unterricht_planen':
        if (lowerText.contains('mathe')) parameters['fach'] = 'Mathematik';
        if (lowerText.contains('deutsch')) parameters['fach'] = 'Deutsch';
        if (lowerText.contains('englisch')) parameters['fach'] = 'Englisch';
        
        final gradeMatch = RegExp(r'klasse\s*(\d+)').firstMatch(lowerText);
        if (gradeMatch != null) parameters['klasse'] = gradeMatch.group(1);
        
        // Thema extrahieren
        final topicKeywords = ['über', 'zu', 'thema', 'über'];
        for (var keyword in topicKeywords) {
          final index = lowerText.indexOf(keyword);
          if (index != -1) {
            parameters['thema'] = text.substring(index + keyword.length).trim();
            break;
          }
        }
        break;
        
      case 'bewertung_erstellen':
        if (lowerText.contains('gedicht')) parameters['thema'] = 'Gedichtanalyse';
        if (lowerText.contains('aufsatz')) parameters['thema'] = 'Aufsatz';
        if (lowerText.contains('präsentation')) parameters['thema'] = 'Präsentation';
        break;
    }
    
    return parameters;
  }

  /// Datei-Upload verarbeiten
  void _handleFileUpload(File file, String fileType) {
    final fileName = file.path.split('/').last.split('\\').last;
    _addMessage(
      ChatMessage(
        id: 'file_${DateTime.now().millisecondsSinceEpoch}',
        content: 'Datei hochgeladen: $fileName',
        timestamp: DateTime.now(),
        isUser: true,
        type: MessageType.file,
        metadata: {'file_path': file.path, 'file_type': fileType},
      ),
    );

    if (fileType == 'pdf') {
      _addMessage(
        ChatMessage(
          id: 'auto_${DateTime.now().millisecondsSinceEpoch}',
          content: 'Erkenne PDF-Datei. Möchten Sie diese als Lehrplan einlesen?',
          timestamp: DateTime.now(),
          isUser: false,
          type: MessageType.system,
        ),
      );
    }
  }

  /// Quick-Action verarbeiten
  void _handleQuickAction(String action) {
    String message;
    
    switch (action) {
      case 'plan_lesson':
        message = 'Plane eine Unterrichtsstunde für mich.';
        break;
      case 'create_assessment':
        message = 'Erstelle ein Bewertungsraster.';
        break;
      case 'create_exam':
        message = 'Erstelle eine Klassenarbeit.';
        break;
      case 'create_worksheet':
        message = 'Erstelle ein Arbeitsblatt.';
        break;
      case 'write_letter':
        message = 'Schreibe einen Elternbrief.';
        break;
      case 'read_curriculum':
        message = 'Lese einen Lehrplan ein.';
        break;
      case 'correct_work':
        message = 'Bewerte eine Schülerarbeit.';
        break;
      case 'show_profile':
        message = 'Zeige mein Lehrerprofil an.';
        break;
      default:
        message = action;
    }
    
    _textController.text = message;
    _sendMessage();
  }

  /// Nachricht hinzufügen
  void _addMessage(ChatMessage message) {
    setState(() {
      _messages.add(message);
    });
    
    // Automatisch nach unten scrollen
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  /// In Zwischenablage kopieren
  void _copyToClipboard(String text) {
    Clipboard.setData(ClipboardData(text: text));
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('In Zwischenablage kopiert'),
        duration: Duration(seconds: 2),
      ),
    );
  }

  /// Nachricht teilen
  void _shareMessage(ChatMessage message) {
    // Hier würde die Sharing-Funktionalität implementiert werden
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Teilen: ${message.content.substring(0, 50)}...'),
        duration: const Duration(seconds: 2),
      ),
    );
  }

  /// Nachricht speichern
  void _saveMessage(ChatMessage message) {
    // Hier würde die Speicherfunktionalität implementiert werden
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Gespeichert: ${message.id}'),
        duration: const Duration(seconds: 2),
      ),
    );
  }

  /// Hilfe anzeigen
  void _showHelp() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Hilfe - LehrerAgent Chat'),
        content: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text(
                'So verwenden Sie den Chat:',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              _buildHelpItem('📅', 'Unterricht planen', '"Plane eine Mathestunde zu Bruchrechnung für Klasse 7"'),
              _buildHelpItem('📄', 'Arbeitsblatt erstellen', '"Erstelle ein Arbeitsblatt zu Photosynthese für Klasse 9"'),
              _buildHelpItem('📝', 'Prüfung erstellen', '"Erstelle eine Klassenarbeit Deutsch Klasse 8 zum Thema Kurzgeschichte"'),
              _buildHelpItem('📋', 'Bewertungsraster', '"Erstelle einen Erwartungshorizont für Gedichtanalyse Klasse 8"'),
              _buildHelpItem('✏️', 'Schülerarbeit bewerten', '"Bewerte diese Schülerarbeit" (+ Foto/PDF hochladen)'),
              _buildHelpItem('✉️', 'Elternbrief schreiben', '"Schreibe einen Elternbrief für den Elternabend am 15. Mai"'),
              _buildHelpItem('🎓', 'Zeugnisformulierung', '"Formuliere einen Zeugnistext für Deutsch Note 3"'),
              _buildHelpItem('🤝', 'Förderplan erstellen', '"Erstelle einen Förderplan für LRS"'),
              _buildHelpItem('📊', 'Klassenstatistik', '"Werte diese Ergebnisse aus: 38, 42, 17, 29, 45, 31"'),
              _buildHelpItem('📚', 'Lehrplan einlesen', '"Lese den Bayern-Lehrplan Mathematik Klasse 7 ein"'),
              const SizedBox(height: 16),
              const Text(
                'Datei-Upload:',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 4),
              const Text('• PDF: Lehrpläne, Arbeitsblätter\n• Bilder: Schülerarbeiten, Tafelbilder\n• Text: Notizen, Protokolle'),
              const SizedBox(height: 16),
              const Text(
                'Tipps:',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 4),
              const Text('• Seien Sie spezifisch in Ihren Anfragen\n• Nutzen Sie die Quick-Actions auf Mobilgeräten\n• Alle Daten bleiben lokal auf Ihrem Gerät'),
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

  Widget _buildHelpItem(String emoji, String title, String example) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('$emoji $title'),
          Text(
            example,
            style: const TextStyle(fontSize: 12, color: Colors.grey),
          ),
        ],
      ),
    );
  }

  /// Chat-Verlauf anzeigen
  void _showHistory() {
    // Hier würde der Chat-Verlauf angezeigt werden
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Chat-Verlauf wird geladen...'),
        duration: Duration(seconds: 2),
      ),
    );
  }

  /// Quick-Actions umschalten
  void _toggleQuickActions() {
    setState(() {
      _showQuickActions = !_showQuickActions;
    });
  }
}