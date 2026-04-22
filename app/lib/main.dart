import 'package:flutter/material.dart';
import 'screens/chat_screen.dart';

void main() {
  runApp(const TeacherAssistApp());
}

class TeacherAssistApp extends StatelessWidget {
  const TeacherAssistApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'LehrerAssistent',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.indigo),
        useMaterial3: true,
      ),
      home: const ChatScreen(),
    );
  }
}
