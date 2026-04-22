import 'dart:io';

class OpenclawService {
  static const int defaultPort = 18789;

  final String host;
  final int port;
  WebSocket? _socket;

  OpenclawService({required this.host, this.port = defaultPort});

  Future<void> connect() async {
    // TODO: implement with exponential backoff reconnect
    _socket = await WebSocket.connect('ws://$host:$port');
  }

  void disconnect() {
    _socket?.close();
    _socket = null;
  }
}
