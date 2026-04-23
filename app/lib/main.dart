import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'config/app_config.dart';
import 'services/openclaw_service.dart';
import 'services/notification_service.dart';
import 'services/tailscale_service.dart';
import 'services/connection_manager.dart';
import 'screens/chat_screen.dart';
import 'screens/tasks_screen.dart';
import 'screens/results_screen.dart';
import 'screens/settings_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();

  // Globalen ConnectionManager initialisieren (setzt _globalConnectionManager
  // synchron bevor runApp() läuft — der erste await liegt innerhalb von initialize())
  initializeConnectionManager(appConfig);

  // Services starten (fire-and-forget, Fehler werden intern behandelt)
  openClawService.initialize(appConfig);
  tailscaleService.initialize();
  notificationService.initialize();

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
        // OpenClaw Service (Singleton, kein ChangeNotifier — nutzt Streams)
        Provider<OpenClawService>(
          create: (_) => openClawService,
          lazy: false,
        ),
        // Notification Service
        Provider<NotificationService>(
          create: (_) => notificationService,
          lazy: false,
        ),
        // Tailscale Service
        Provider<TailscaleService>(
          create: (_) => tailscaleService,
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
          return MaterialPageRoute(
            builder: (context) => const ChatScreen(),
          );
        },
      ),
    );
  }
}
