/// Notification Service für LehrerAgent
/// Implementiert Push-Benachrichtigungen für Android (FCM) und iOS (APNs)
library notification_service;

import 'dart:async';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:firebase_messaging/firebase_messaging.dart';

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
  late FirebaseMessaging _firebaseMessaging;
  bool _initialized = false;
  StreamController<NotificationData> _notificationStream = StreamController.broadcast();

  /// Stream für eingehende Benachrichtigungen
  Stream<NotificationData> get notifications => _notificationStream.stream;

  /// Initialisierung
  Future<void> initialize() async {
    if (_initialized) return;

    // Lokale Benachrichtigungen initialisieren
    _localNotifications = FlutterLocalNotificationsPlugin();
    
    const AndroidInitializationSettings androidSettings =
        AndroidInitializationSettings('@mipmap/ic_launcher');
    
    const DarwinInitializationSettings iosSettings = DarwinInitializationSettings(
      requestAlertPermission: true,
      requestBadgePermission: true,
      requestSoundPermission: true,
    );
    
    final InitializationSettings settings = InitializationSettings(
      android: androidSettings,
      iOS: iosSettings,
    );
    
    await _localNotifications.initialize(
      settings,
      onDidReceiveNotificationResponse: _onNotificationTapped,
    );

    // Firebase Messaging initialisieren (nur wenn verfügbar)
    try {
      _firebaseMessaging = FirebaseMessaging.instance;
      
      // Berechtigungen anfordern
      await _requestPermissions();
      
      // Token abrufen
      final token = await _firebaseMessaging.getToken();
      if (token != null) {
        debugPrint('FCM Token: $token');
      }
      
      // Hintergrund-Nachrichten konfigurieren
      FirebaseMessaging.onMessage.listen(_onFirebaseMessage);
      FirebaseMessaging.onMessageOpenedApp.listen(_onFirebaseMessageOpened);
    } catch (e) {
      debugPrint('Firebase Messaging nicht verfügbar: $e');
    }

    _initialized = true;
    debugPrint('Notification Service initialisiert');
  }

  /// Berechtigungen anfordern
  Future<void> _requestPermissions() async {
    if (defaultTargetPlatform == TargetPlatform.android) {
      await _firebaseMessaging.requestPermission(
        alert: true,
        announcement: false,
        badge: true,
        carPlay: false,
        criticalAlert: false,
        provisional: false,
        sound: true,
      );
    } else if (defaultTargetPlatform == TargetPlatform.iOS) {
      await _localNotifications
          .resolvePlatformSpecificImplementation<
              IOSFlutterLocalNotificationsPlugin>()
          ?.requestPermissions(
            alert: true,
            badge: true,
            sound: true,
          );
    }
  }

  /// Lokale Benachrichtigung anzeigen
  Future<void> showLocalNotification({
    required String title,
    required String body,
    required NotificationType type,
    Map<String, dynamic>? payload,
    String? channelId,
    String? channelName,
  }) async {
    if (!_initialized) await initialize();

    const androidPlatformChannelSpecifics = AndroidNotificationDetails(
      'lehreragent_channel', // Channel ID
      'LehrerAgent Benachrichtigungen', // Channel Name
      channelDescription: 'Benachrichtigungen für Agenten-Tasks und Systemmeldungen',
      importance: Importance.high,
      priority: Priority.high,
      ticker: 'ticker',
      enableVibration: true,
      vibrationPattern: Int64List.fromList([0, 250, 250, 250]),
      playSound: true,
    );

    const iosPlatformChannelSpecifics = DarwinNotificationDetails(
      presentAlert: true,
      presentBadge: true,
      presentSound: true,
    );

    final platformChannelSpecifics = NotificationDetails(
      android: androidPlatformChannelSpecifics,
      iOS: iosPlatformChannelSpecifics,
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
      platformChannelSpecifics,
      payload: jsonEncode(notification.toJson()),
    );

    // An Stream senden
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
        final data = jsonDecode(response.payload!);
        final notification = NotificationData.fromJson(data);
        _notificationStream.add(notification);
      }
    } catch (e) {
      debugPrint('Fehler beim Verarbeiten der Benachrichtigung: $e');
    }
  }

  /// Firebase Nachricht empfangen
  void _onFirebaseMessage(RemoteMessage message) {
    debugPrint('Firebase Message empfangen: ${message.notification?.title}');
    
    // Lokale Benachrichtigung anzeigen
    showLocalNotification(
      title: message.notification?.title ?? 'Neue Nachricht',
      body: message.notification?.body ?? '',
      type: NotificationType.system,
      payload: message.data,
    );
  }

  /// Firebase Nachricht geöffnet
  void _onFirebaseMessageOpened(RemoteMessage message) {
    debugPrint('Firebase Message geöffnet: ${message.data}');
    // Hier könnte Navigation zu spezifischem Screen erfolgen
  }

  /// Service beenden
  Future<void> dispose() async {
    await _notificationStream.close();
  }
}

/// Globale Notification Service Instanz
final notificationService = NotificationService();