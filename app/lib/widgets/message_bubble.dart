/// Message Bubble Widget für LehrerAgent
/// Zeigt Chat-Nachrichten in einer Blasen-Form an
library message_bubble;

import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

/// Nachrichten-Typ
enum MessageType {
  /// Nachricht vom Benutzer (Lehrer)
  user,

  /// Nachricht vom Agenten (KI)
  agent,

  /// System-Nachricht (Info, Fehler, Status)
  system,

  /// Datei-Upload-Nachricht
  file,

  /// Tool-Aufruf-Nachricht
  tool,
}

/// Message Bubble Widget
class MessageBubble extends StatelessWidget {
  /// Nachrichteninhalt
  final String message;

  /// Nachrichtentyp
  final MessageType type;

  /// Zeitstempel
  final DateTime timestamp;

  /// Sender-Name
  final String? senderName;

  /// Soll Zeitstempel angezeigt werden?
  final bool showTimestamp;

  /// Soll Avatar angezeigt werden?
  final bool showAvatar;

  /// Ist Nachricht geladen? (für Lade-Animation)
  final bool isLoading;

  /// Hat Nachricht einen Fehler?
  final bool hasError;

  /// Fehlermeldung (falls vorhanden)
  final String? errorMessage;

  /// Callback bei Fehler-Klick
  final VoidCallback? onErrorTap;

  /// Callback bei Nachrichten-Klick
  final VoidCallback? onTap;

  /// Maximale Breite (für Desktop)
  final double? maxWidth;

  /// Konstruktor
  const MessageBubble({
    Key? key,
    required this.message,
    required this.type,
    required this.timestamp,
    this.senderName,
    this.showTimestamp = true,
    this.showAvatar = true,
    this.isLoading = false,
    this.hasError = false,
    this.errorMessage,
    this.onErrorTap,
    this.onTap,
    this.maxWidth,
  }) : super(key: key);

  /// Farbe basierend auf Nachrichtentyp
  Color _getBubbleColor(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    switch (type) {
      case MessageType.user:
        return isDark
            ? Colors.blue.shade800
            : Colors.blue.shade600;
      case MessageType.agent:
        return isDark
            ? Colors.grey.shade800
            : Colors.grey.shade200;
      case MessageType.system:
        return isDark
            ? Colors.orange.shade900.withOpacity(0.3)
            : Colors.orange.shade100;
      case MessageType.file:
        return isDark
            ? Colors.green.shade900.withOpacity(0.3)
            : Colors.green.shade100;
      case MessageType.tool:
        return isDark
            ? Colors.purple.shade900.withOpacity(0.3)
            : Colors.purple.shade100;
    }
  }

  /// Textfarbe basierend auf Nachrichtentyp
  Color _getTextColor(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    switch (type) {
      case MessageType.user:
        return Colors.white;
      case MessageType.agent:
        return isDark ? Colors.white : Colors.black;
      case MessageType.system:
        return isDark ? Colors.orange.shade200 : Colors.orange.shade900;
      case MessageType.file:
        return isDark ? Colors.green.shade200 : Colors.green.shade900;
      case MessageType.tool:
        return isDark ? Colors.purple.shade200 : Colors.purple.shade900;
    }
  }

  /// Avatar-Icon basierend auf Nachrichtentyp
  Widget? _getAvatar(BuildContext context) {
    if (!showAvatar) return null;

    final icon = switch (type) {
      MessageType.user => Icons.person,
      MessageType.agent => Icons.smart_toy,
      MessageType.system => Icons.info,
      MessageType.file => Icons.attach_file,
      MessageType.tool => Icons.build,
    };

    final color = switch (type) {
      MessageType.user => Colors.blue,
      MessageType.agent => Colors.grey,
      MessageType.system => Colors.orange,
      MessageType.file => Colors.green,
      MessageType.tool => Colors.purple,
    };

    return CircleAvatar(
      radius: 16,
      backgroundColor: color.withOpacity(0.2),
      child: Icon(
        icon,
        size: 18,
        color: color,
      ),
    );
  }

  /// Sender-Name basierend auf Nachrichtentyp
  String _getSenderName() {
    if (senderName != null && senderName!.isNotEmpty) {
      return senderName!;
    }

    return switch (type) {
      MessageType.user => 'Du',
      MessageType.agent => 'LehrerAgent',
      MessageType.system => 'System',
      MessageType.file => 'Datei',
      MessageType.tool => 'Tool',
    };
  }

  /// Zeitstempel formatieren
  String _formatTimestamp() {
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final messageDate = DateTime(timestamp.year, timestamp.month, timestamp.day);

    if (messageDate == today) {
      // Heute: nur Uhrzeit
      return DateFormat('HH:mm').format(timestamp);
    } else if (messageDate == today.subtract(const Duration(days: 1))) {
      // Gestern
      return 'Gestern ${DateFormat('HH:mm').format(timestamp)}';
    } else {
      // Älter: Datum + Uhrzeit
      return DateFormat('dd.MM. HH:mm').format(timestamp);
    }
  }

  /// Nachrichteninhalt formatieren (Markdown-Support)
  Widget _buildMessageContent(BuildContext context) {
    final textColor = _getTextColor(context);
    final textStyle = TextStyle(
      color: textColor,
      fontSize: 16,
      height: 1.4,
    );

    // Einfache Markdown-Erkennung
    final lines = message.split('\n');
    final children = <Widget>[];

    for (final line in lines) {
      if (line.startsWith('# ')) {
        // Überschrift
        children.add(
          Text(
            line.substring(2),
            style: textStyle.copyWith(
              fontWeight: FontWeight.bold,
              fontSize: 18,
            ),
          ),
        );
      } else if (line.startsWith('## ')) {
        // Unterüberschrift
        children.add(
          Text(
            line.substring(3),
            style: textStyle.copyWith(
              fontWeight: FontWeight.bold,
              fontSize: 16,
            ),
          ),
        );
      } else if (line.startsWith('- ') || line.startsWith('• ')) {
        // Listenpunkt
        children.add(
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('• ', style: TextStyle(fontSize: 16)),
              Expanded(
                child: Text(
                  line.substring(2),
                  style: textStyle,
                ),
              ),
            ],
          ),
        );
      } else if (line.trim().isEmpty) {
        // Leerzeile
        children.add(const SizedBox(height: 8));
      } else {
        // Normaler Text
        children.add(Text(line, style: textStyle));
      }
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: children,
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isUserMessage = type == MessageType.user;
    final bubbleColor = _getBubbleColor(context);
    final avatar = _getAvatar(context);
    final formattedTime = _formatTimestamp();

    return ConstrainedBox(
      constraints: BoxConstraints(
        maxWidth: maxWidth ?? 600,
      ),
      child: GestureDetector(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 4, horizontal: 8),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisAlignment: isUserMessage
                ? MainAxisAlignment.end
                : MainAxisAlignment.start,
            children: [
              // Avatar (links, außer bei User-Nachrichten)
              if (!isUserMessage && avatar != null)
                Padding(
                  padding: const EdgeInsets.only(right: 8, top: 4),
                  child: avatar,
                ),

              // Nachrichteninhalt
              Expanded(
                child: Column(
                  crossAxisAlignment: isUserMessage
                      ? CrossAxisAlignment.end
                      : CrossAxisAlignment.start,
                  children: [
                    // Sender-Name und Zeitstempel
                    if (showTimestamp || senderName != null)
                      Padding(
                        padding: const EdgeInsets.only(bottom: 4),
                        child: Row(
                          mainAxisAlignment: isUserMessage
                              ? MainAxisAlignment.end
                              : MainAxisAlignment.start,
                          children: [
                            if (senderName != null && !isUserMessage)
                              Text(
                                _getSenderName(),
                                style: TextStyle(
                                  fontSize: 12,
                                  fontWeight: FontWeight.bold,
                                  color: theme.hintColor,
                                ),
                              ),
                            if (senderName != null && showTimestamp)
                              const SizedBox(width: 8),
                            if (showTimestamp)
                              Text(
                                formattedTime,
                                style: TextStyle(
                                  fontSize: 11,
                                  color: theme.hintColor,
                                ),
                              ),
                          ],
                        ),
                      ),

                    // Nachrichten-Bubble
                    Material(
                      borderRadius: BorderRadius.only(
                        topLeft: isUserMessage
                            ? const Radius.circular(16)
                            : const Radius.circular(4),
                        topRight: isUserMessage
                            ? const Radius.circular(4)
                            : const Radius.circular(16),
                        bottomLeft: const Radius.circular(16),
                        bottomRight: const Radius.circular(16),
                      ),
                      elevation: 1,
                      color: bubbleColor,
                      child: Container(
                        padding: const EdgeInsets.all(12),
                        child: isLoading
                            ? _buildLoadingIndicator()
                            : _buildMessageContent(context),
                      ),
                    ),

                    // Fehler-Anzeige
                    if (hasError && errorMessage != null)
                      GestureDetector(
                        onTap: onErrorTap,
                        child: Padding(
                          padding: const EdgeInsets.only(top: 4),
                          child: Row(
                            mainAxisAlignment: isUserMessage
                                ? MainAxisAlignment.end
                                : MainAxisAlignment.start,
                            children: [
                              Icon(
                                Icons.error_outline,
                                size: 14,
                                color: Colors.red.shade600,
                              ),
                              const SizedBox(width: 4),
                              Text(
                                errorMessage!,
                                style: TextStyle(
                                  fontSize: 12,
                                  color: Colors.red.shade600,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                  ],
                ),
              ),

              // Avatar (rechts, nur bei User-Nachrichten)
              if (isUserMessage && avatar != null)
                Padding(
                  padding: const EdgeInsets.only(left: 8, top: 4),
                  child: avatar,
                ),
            ],
          ),
        ),
      ),
    );
  }

  /// Lade-Indikator
  Widget _buildLoadingIndicator() {
    return const SizedBox(
      height: 24,
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          SizedBox(
            width: 24,
            height: 24,
            child: CircularProgressIndicator(strokeWidth: 2),
          ),
        ],
      ),
    );
  }
}

/// Spezialisierte Message Bubble für Datei-Uploads
class FileMessageBubble extends StatelessWidget {
  final String fileName;
  final String fileType;
  final int fileSize;
  final DateTime timestamp;
  final bool isUploading;
  final double uploadProgress;
  final bool hasError;
  final String? errorMessage;
  final VoidCallback? onRetry;
  final VoidCallback? onTap;

  const FileMessageBubble({
    Key? key,
    required this.fileName,
    required this.fileType,
    required this.fileSize,
    required this.timestamp,
    this.isUploading = false,
    this.uploadProgress = 0.0,
    this.hasError = false,
    this.errorMessage,
    this.onRetry,
    this.onTap,
  }) : super(key: key);

  /// Dateigröße formatieren
  String _formatFileSize(int bytes) {
    if (bytes >= 1024 * 1024) {
      return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
    } else if (bytes >= 1024) {
      return '${(bytes / 1024).toStringAsFixed(1)} KB';
    } else {
      return '$bytes Bytes';
    }
  }

  /// Datei-Icon basierend auf Typ
  IconData _getFileIcon() {
    return switch (fileType.toLowerCase()) {
      'pdf' => Icons.picture_as_pdf,
      'jpg' || 'jpeg' || 'png' || 'gif' || 'bmp' || 'webp' => Icons.image,
      'doc' || 'docx' => Icons.description,
      'xls' || 'xlsx' => Icons.table_chart,
      'txt' => Icons.text_fields,
      _ => Icons.insert_drive_file,
    };
  }

  @override
  Widget build(BuildContext context) {
    return MessageBubble(
      message: '📎 $fileName\n📏 ${_formatFileSize(fileSize)}',
      type: MessageType.file,
      timestamp: timestamp,
      showAvatar: true,
      isLoading: isUploading,
      hasError: hasError,
      errorMessage: errorMessage,
      onErrorTap: onRetry,
      onTap: onTap,
      maxWidth: 400,
    );
  }
}

/// Spezialisierte Message Bubble für Tool-Aufrufe
class ToolMessageBubble extends StatelessWidget {
  final String toolName;
  final Map<String, dynamic> parameters;
  final DateTime timestamp;
  final bool isExecuting;
  final bool hasError;
  final String? errorMessage;
  final Map<String, dynamic>? result;

  const ToolMessageBubble({
    Key? key,
    required this.toolName,
    required this.parameters,
    required this.timestamp,
    this.isExecuting = false,
    this.hasError = false,
    this.errorMessage,
    this.result,
  }) : super(key: key);

  /// Tool-Name in lesbares Format bringen
  String _formatToolName() {
    return toolName.replaceAll('_', ' ').replaceAll('.py', '');
  }

  /// Kurze Parameter-Zusammenfassung
  String _getParametersSummary() {
    if (parameters.isEmpty) return 'Keine Parameter';
    
    final entries = parameters.entries.take(2).toList();
    final summary = entries.map((e) => '${e.key}: ${e.value}').join(', ');
    
    if (parameters.length > 2) {
      return '$summary, +${parameters.length - 2} weitere';
    }
    
    return summary;
  }

  @override
  Widget build(BuildContext context) {
    final message = StringBuffer();
    message.write('🛠️ ${_formatToolName()}\n');
    message.write('⚙️ ${_getParametersSummary()}');

    if (result != null && result!['success'] == true) {
      message.write('\n✅ Erfolgreich ausgeführt');
    }

    return MessageBubble(
      message: message.toString(),
      type: MessageType.tool,
      timestamp: timestamp,
      showAvatar: true,
      isLoading: isExecuting,
      hasError: hasError,
      errorMessage: errorMessage,
    );
  }
}