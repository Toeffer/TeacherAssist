/// Notification Service für LehrerAgent
/// Lokale Push-Benachrichtigungen (kein Firebase – DSGVO-konform)
library notification_service;

import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';

/// Benachrichtigungstypen
enum NotificationType {
  taskCompleted,    // Agenten-Task abgeschlossen
  connectionChange, // Verbindungsstatus geändert
  reminder,         // Erinnerung (z.B. Korrekturfrist)
  system            // Systembenachrichtigung
}

/// Benachrichtigungsdaten
class NotificationData {
  final String id;
  final String title;
  final String body;
  final NotificationType type;
  final DateTime timestamp;
  final Map<String, dynamic>? payload;

  NotificationData({
    required this.id,
    required this.title,
    required this.body,
    required this.type,
    required this.timestamp,
    this.payload,
  });

  factory NotificationData.fromJson(Map<String, dynamic> json) {
    return NotificationData(
      id: json['id'],
      title: json['title'],
      body: json['body'],
      type: NotificationType.values.firstWhere(
        (e) => e.toString() == json['type'],
        orElse: () => NotificationType.system,
      ),
      timestamp: DateTime.parse(json['timestamp']),
      payload: json['payload'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'body': body,
      'type': type.toString(),
      'timestamp': timestamp.toIso8601String(),
      'payload': payload,
    };
  }
}

/// Haupt-Notification-Service
class NotificationService {
  static final NotificationService _instance = NotificationService._internal();
  factory NotificationService() => _instance;
  NotificationService._internal();

  late FlutterLocalNotificationsPlugin _localNotifications;
  bool _initialized = false;
  final StreamController<NotificationData> _notificationStream =
      StreamController.broadcast();

  /// Stream für eingehende Benachrichtigungen
  Stream<NotificationData> get notifications => _notificationStream.stream;

  /// Initialisierung
  Future<void> initialize() async {
    if (_initialized) return;

    _localNotifications = FlutterLocalNotificationsPlugin();

    const androidSettings =
        AndroidInitializationSettings('@mipmap/ic_launcher');

    const darwinSettings = DarwinInitializationSettings(
      requestAlertPermission: true,
      requestBadgePermission: true,
      requestSoundPermission: true,
    );

    const settings = InitializationSettings(
      android: androidSettings,
      iOS: darwinSettings,
      macOS: darwinSettings,
    );

    await _localNotifications.initialize(
      settings,
      onDidReceiveNotificationResponse: _onNotificationTapped,
    );

    // iOS-Berechtigungen anfordern
    await _localNotifications
        .resolvePlatformSpecificImplementation<
            IOSFlutterLocalNotificationsPlugin>()
        ?.requestPermissions(alert: true, badge: true, sound: true);

    _initialized = true;
    debugPrint('Notification Service initialisiert');
  }

  /// Lokale Benachrichtigung anzeigen
  Future<void> showLocalNotification({
    required String title,
    required String body,
    required NotificationType type,
    Map<String, dynamic>? payload,
  }) async {
    if (!_initialized) await initialize();

    final androidDetails = AndroidNotificationDetails(
      'lehreragent_channel',
      'LehrerAgent Benachrichtigungen',
      channelDescription:
          'Benachrichtigungen für Agenten-Tasks und Systemmeldungen',
      importance: Importance.high,
      priority: Priority.high,
      enableVibration: true,
      vibrationPattern: Int64List.fromList([0, 250, 250, 250]),
      playSound: true,
    );

    const darwinDetails = DarwinNotificationDetails(
      presentAlert: true,
      presentBadge: true,
      presentSound: true,
    );

    final details = NotificationDetails(
      android: androidDetails,
      iOS: darwinDetails,
      macOS: darwinDetails,
    );

    final notification = NotificationData(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      title: title,
      body: body,
      type: type,
      timestamp: DateTime.now(),
      payload: payload,
    );

    await _localNotifications.show(
      notification.id.hashCode,
      title,
      body,
      details,
      payload: jsonEncode(notification.toJson()),
    );

    _notificationStream.add(notification);
  }

  /// Benachrichtigung für abgeschlossenen Task
  Future<void> notifyTaskCompleted({
    required String taskName,
    required String resultSummary,
    Map<String, dynamic>? taskData,
  }) async {
    await showLocalNotification(
      title: 'Task abgeschlossen: $taskName',
      body: resultSummary,
      type: NotificationType.taskCompleted,
      payload: {
        'task_name': taskName,
        'result_summary': resultSummary,
        'task_data': taskData,
        'action': 'view_result',
      },
    );
  }

  /// Verbindungsänderung benachrichtigen
  Future<void> notifyConnectionChange({
    required String fromStatus,
    required String toStatus,
    bool isOnline = false,
  }) async {
    await showLocalNotification(
      title: 'Verbindungsstatus geändert',
      body: 'Von $fromStatus zu $toStatus',
      type: NotificationType.connectionChange,
      payload: {
        'from_status': fromStatus,
        'to_status': toStatus,
        'is_online': isOnline,
        'action': 'check_connection',
      },
    );
  }

  /// Erinnerungsbenachrichtigung
  Future<void> notifyReminder({
    required String reminderTitle,
    required String reminderText,
    DateTime? dueDate,
  }) async {
    final dueText = dueDate != null
        ? 'Fällig: ${dueDate.toLocal().toString().substring(0, 16)}'
        : '';

    await showLocalNotification(
      title: reminderTitle,
      body: '$reminderText\n$dueText',
      type: NotificationType.reminder,
      payload: {
        'reminder_title': reminderTitle,
        'reminder_text': reminderText,
        'due_date': dueDate?.toIso8601String(),
        'action': 'view_reminder',
      },
    );
  }

  /// Alle Benachrichtigungen löschen
  Future<void> clearAllNotifications() async {
    await _localNotifications.cancelAll();
  }

  /// Bei Tipp auf Benachrichtigung
  void _onNotificationTapped(NotificationResponse response) {
    try {
      if (response.payload != null) {
        final data = jsonDecode(response.payload!) as Map<String, dynamic>;
        final notification = NotificationData.fromJson(data);
        _notificationStream.add(notification);
      }
    } catch (e) {
      debugPrint('Fehler beim Verarbeiten der Benachrichtigung: $e');
    }
  }

  /// Service beenden
  Future<void> dispose() async {
    await _notificationStream.close();
  }
}

/// Globale Notification Service Instanz
final notificationService = NotificationService();
