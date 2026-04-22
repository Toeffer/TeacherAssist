/// Datei-Upload-Button für LehrerAgent
/// Ermöglicht das Hochladen von PDFs und Bildern für OCR und Lehrplan-Import
library file_upload_button;

import 'dart:io';
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import '../config/app_config.dart';

/// Callback-Typ für erfolgreiche Uploads
typedef FileUploadCallback = void Function(File file, String fileType);

/// Callback-Typ für Upload-Fehler
typedef UploadErrorCallback = void Function(String errorMessage);

/// Datei-Upload-Button Widget
class FileUploadButton extends StatefulWidget {
  /// Erlaubte Dateitypen
  final List<String> allowedExtensions;

  /// Maximale Dateigröße in Bytes
  final int? maxFileSize;

  /// Callback bei erfolgreichem Upload
  final FileUploadCallback onFileSelected;

  /// Callback bei Upload-Fehler
  final UploadErrorCallback? onError;

  /// Button-Text
  final String buttonText;

  /// Button-Icon
  final IconData? icon;

  /// Button-Farbe
  final Color? backgroundColor;

  /// Text-Farbe
  final Color? textColor;

  /// Soll Multiple Selection erlaubt sein?
  final bool allowMultiple;

  /// Konstruktor
  const FileUploadButton({
    Key? key,
    this.allowedExtensions = const ['pdf', 'jpg', 'jpeg', 'png', 'webp'],
    this.maxFileSize,
    required this.onFileSelected,
    this.onError,
    this.buttonText = 'Datei hochladen',
    this.icon = Icons.upload_file,
    this.backgroundColor,
    this.textColor,
    this.allowMultiple = false,
  }) : super(key: key);

  @override
  State<FileUploadButton> createState() => _FileUploadButtonState();
}

class _FileUploadButtonState extends State<FileUploadButton> {
  /// Upload läuft
  bool _isUploading = false;

  /// Letzter Upload-Fehler
  String? _lastError;

  /// Dateityp-Description für Benutzer
  String get _fileTypeDescription {
    final types = widget.allowedExtensions;
    if (types.contains('pdf') && types.contains('jpg')) {
      return 'PDF oder Bild (JPG, PNG, WEBP)';
    } else if (types.contains('pdf')) {
      return 'PDF-Dateien';
    } else {
      return 'Bilddateien (${types.join(', ')})';
    }
  }

  /// Maximale Dateigröße mit Fallback
  int get _effectiveMaxFileSize {
    return widget.maxFileSize ?? appConfig.maxFileSizeBytes;
  }

  /// Dateigröße in lesbarem Format
  String get _maxFileSizeFormatted {
    final bytes = _effectiveMaxFileSize;
    if (bytes >= 1024 * 1024) {
      return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
    } else if (bytes >= 1024) {
      return '${(bytes / 1024).toStringAsFixed(1)} KB';
    } else {
      return '$bytes Bytes';
    }
  }

  /// Datei auswählen und validieren
  Future<void> _pickFile() async {
    if (_isUploading) return;

    setState(() {
      _isUploading = true;
      _lastError = null;
    });

    try {
      final result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: widget.allowedExtensions,
        allowMultiple: widget.allowMultiple,
        withData: false,
        withReadStream: false,
      );

      if (result == null || result.files.isEmpty) {
        // Benutzer hat abgebrochen
        setState(() {
          _isUploading = false;
        });
        return;
      }

      // Nur erste Datei verarbeiten (bei Multiple=false)
      final platformFile = result.files.first;
      final file = File(platformFile.path!);

      // Datei validieren
      await _validateFile(file, platformFile);

      // Dateityp bestimmen
      final fileType = _determineFileType(platformFile.extension);

      // Callback aufrufen
      widget.onFileSelected(file, fileType);

      // Erfolgs-Snackbar anzeigen
      _showSuccessSnackbar(platformFile.name, fileType);
    } catch (e) {
      final errorMessage = e.toString();
      setState(() {
        _lastError = errorMessage;
      });

      // Error-Callback aufrufen
      widget.onError?.call(errorMessage);

      // Fehler-Snackbar anzeigen
      _showErrorSnackbar(errorMessage);
    } finally {
      setState(() {
        _isUploading = false;
      });
    }
  }

  /// Datei validieren
  Future<void> _validateFile(File file, PlatformFile platformFile) async {
    // Dateigröße prüfen
    final fileSize = await file.length();
    if (fileSize > _effectiveMaxFileSize) {
      throw Exception(
          'Datei zu groß: ${_formatFileSize(fileSize)} (max. $_maxFileSizeFormatted)');
    }

    // Dateityp prüfen
    final extension = platformFile.extension?.toLowerCase() ?? '';
    if (!widget.allowedExtensions.any((ext) => extension == ext.toLowerCase())) {
      throw Exception('Dateityp nicht erlaubt: .$extension');
    }

    // Datei existiert und ist lesbar
    if (!await file.exists()) {
      throw Exception('Datei konnte nicht gefunden werden');
    }
  }

  /// Dateityp bestimmen
  String _determineFileType(String? extension) {
    final ext = extension?.toLowerCase() ?? '';
    if (ext == 'pdf') {
      return 'pdf';
    } else if (['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'tiff'].contains(ext)) {
      return 'image';
    } else {
      return 'unknown';
    }
  }

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

  /// Erfolgs-Snackbar anzeigen
  void _showSuccessSnackbar(String fileName, String fileType) {
    final message = fileType == 'pdf'
        ? 'PDF "$fileName" wurde ausgewählt'
        : 'Bild "$fileName" wurde ausgewählt';

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.green,
        duration: const Duration(seconds: 2),
      ),
    );
  }

  /// Fehler-Snackbar anzeigen
  void _showErrorSnackbar(String error) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Fehler: $error'),
        backgroundColor: Colors.red,
        duration: const Duration(seconds: 3),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Upload-Button
        ElevatedButton(
          onPressed: _isUploading ? null : _pickFile,
          style: ElevatedButton.styleFrom(
            backgroundColor: widget.backgroundColor ??
                (isDark ? Colors.blue.shade800 : Colors.blue.shade600),
            foregroundColor: widget.textColor ?? Colors.white,
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(8),
            ),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              if (widget.icon != null)
                Icon(
                  widget.icon,
                  size: 20,
                ),
              const SizedBox(width: 8),
              Text(
                _isUploading ? 'Wird geladen...' : widget.buttonText,
                style: const TextStyle(fontSize: 16),
              ),
            ],
          ),
        ),

        const SizedBox(height: 8),

        // Info-Text
        Text(
          'Unterstützt: $_fileTypeDescription (max. $_maxFileSizeFormatted)',
          style: TextStyle(
            fontSize: 12,
            color: theme.hintColor,
          ),
        ),

        // Fehler-Anzeige
        if (_lastError != null) ...[
          const SizedBox(height: 8),
          Text(
            _lastError!,
            style: TextStyle(
              fontSize: 12,
              color: Colors.red.shade700,
            ),
          ),
        ],

        // Upload-Status
        if (_isUploading) ...[
          const SizedBox(height: 8),
          const LinearProgressIndicator(),
        ],
      ],
    );
  }
}

/// Spezialisierter PDF-Upload-Button
class PdfUploadButton extends StatelessWidget {
  final FileUploadCallback onPdfSelected;
  final UploadErrorCallback? onError;
  final String buttonText;

  const PdfUploadButton({
    Key? key,
    required this.onPdfSelected,
    this.onError,
    this.buttonText = 'PDF hochladen',
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return FileUploadButton(
      allowedExtensions: const ['pdf'],
      onFileSelected: (file, fileType) => onPdfSelected(file, fileType),
      onError: onError,
      buttonText: buttonText,
      icon: Icons.picture_as_pdf,
      backgroundColor: Colors.red.shade600,
    );
  }
}

/// Spezialisierter Bild-Upload-Button
class ImageUploadButton extends StatelessWidget {
  final FileUploadCallback onImageSelected;
  final UploadErrorCallback? onError;
  final String buttonText;

  const ImageUploadButton({
    Key? key,
    required this.onImageSelected,
    this.onError,
    this.buttonText = 'Bild hochladen',
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return FileUploadButton(
      allowedExtensions: const ['jpg', 'jpeg', 'png', 'webp'],
      onFileSelected: (file, fileType) => onImageSelected(file, fileType),
      onError: onError,
      buttonText: buttonText,
      icon: Icons.image,
      backgroundColor: Colors.green.shade600,
    );
  }
}