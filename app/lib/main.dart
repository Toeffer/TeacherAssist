import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'config/app_config.dart';
import 'services/openclaw_service.dart';
import 'services/notification_service.dart';
import 'services/tailscale_service.dart';
import 'screens/chat_screen.dart';
import 'screens/tasks_screen.dart';
import 'screens/results_screen.dart';
import 'screens/settings_screen.dart';

void main() {
  runApp(const TeacherAssistApp());
}

class TeacherAssistApp extends StatelessWidget {
  const TeacherAssistApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        // App-Konfiguration
        Provider<AppConfig>(
          create: (_) => AppConfig.fromEnvironment(),
        ),
        // OpenClaw Service
        ChangeNotifierProvider<OpenClawService>(
          create: (_) => OpenClawService(),
          lazy: false, // Sofort initialisieren
        ),
        // Notification Service
        ChangeNotifierProvider<NotificationService>(
          create: (_) => NotificationService(),
          lazy: false,
        ),
        // Tailscale Service
        ChangeNotifierProvider<TailscaleService>(
          create: (_) => TailscaleService(),
          lazy: false,
        ),
      ],
      child: MaterialApp(
        title: 'LehrerAssistent',
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(
            seedColor: Colors.indigo,
            brightness: Brightness.light,
          ),
          useMaterial3: true,
          fontFamily: 'Roboto',
        ),
        darkTheme: ThemeData(
          colorScheme: ColorScheme.fromSeed(
            seedColor: Colors.indigo,
            brightness: Brightness.dark,
          ),
          useMaterial3: true,
          fontFamily: 'Roboto',
        ),
        themeMode: ThemeMode.system,
        debugShowCheckedModeBanner: false,
        initialRoute: '/chat',
        routes: {
          '/chat': (context) => const ChatScreen(),
          '/tasks': (context) => const TasksScreen(),
          '/results': (context) => const ResultsScreen(),
          '/settings': (context) => const SettingsScreen(),
        },
        onGenerateRoute: (settings) {
          // Fallback für unbekannte Routen
          return MaterialPageRoute(
            builder: (context) => const ChatScreen(),
          );
        },
      ),
    );
  }
}
