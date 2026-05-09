// ConnectionService.swift
// Verwaltet die WebSocket-Verbindung zu OpenClaw über lokales WLAN oder Tailscale.
// Port 18789 ist die OpenClaw/Tailscale-WebSocket-Integration; der Desktop-Tool-Server nutzt separat 8789.
//
// Verwendung:
//   let service = ConnectionService(host: "192.168.1.42", port: 18789)
//   await service.connect()
//   try await service.sendImage(data: jpegData, context: context)

import Foundation
import Network

// MARK: - Nachrichtentypen

struct UploadMessage: Codable {
    let type: String          // "upload"
    let id: String            // UUID der Übertragung
    let skill: String         // z. B. "schuelerarbeit_bewerten"
    let image: ImagePayload
    let context: UploadContext
}

struct ImagePayload: Codable {
    let data: String          // Base64-kodiertes JPEG
    let format: String        // "jpeg"
    let widthPx: Int
    let heightPx: Int

    enum CodingKeys: String, CodingKey {
        case data, format
        case widthPx = "width_px"
        case heightPx = "height_px"
    }
}

struct UploadContext: Codable {
    let fach: String
    let klasse: String
    let aufgabe: String
}

struct ServerMessage: Codable {
    let type: String          // "progress", "result", "error"
    let id: String
    let step: String?         // bei "progress"
    let percent: Int?         // bei "progress" (0–100)
    let punkte: String?       // bei "result"
    let note: String?         // bei "result"
    let feedback: String?     // bei "result"
    let message: String?      // bei "error"
}

// MARK: - Verbindungsstatus

enum ConnectionState: Equatable {
    case disconnected
    case connecting
    case connected(host: String)
    case error(String)
}

// MARK: - ConnectionService

@MainActor
class ConnectionService: ObservableObject {

    // Konfiguration
    private let host: String
    private let port: UInt16
    private let path: String

    // State (Published für SwiftUI)
    @Published var state: ConnectionState = .disconnected
    @Published var lastError: String?

    // WebSocket Task
    private var webSocketTask: URLSessionWebSocketTask?
    private var urlSession: URLSession

    // Callback für eingehende Server-Nachrichten
    var onMessage: ((ServerMessage) -> Void)?

    // Reconnect
    private var reconnectAttempts = 0
    private let maxReconnectAttempts = 5

    init(host: String, port: UInt16 = 18789, path: String = "/ws") {
        self.host = host
        self.port = port
        self.path = path
        self.urlSession = URLSession(configuration: .default)
    }

    // MARK: - Verbinden

    func connect() async {
        guard state == .disconnected else { return }
        state = .connecting

        guard let url = buildURL() else {
            state = .error("Ungültige URL: \(host):\(port)")
            return
        }

        var request = URLRequest(url: url)
        request.timeoutInterval = 10

        webSocketTask = urlSession.webSocketTask(with: request)
        webSocketTask?.resume()

        // Verbindung prüfen mit Ping
        do {
            try await ping()
            state = .connected(host: host)
            reconnectAttempts = 0
            startReceiving()
        } catch {
            state = .error("Kein OpenClaw unter \(host):\(port) erreichbar.\nLäuft openclaw start auf dem Mac?")
            webSocketTask?.cancel()
            webSocketTask = nil
        }
    }

    func disconnect() {
        webSocketTask?.cancel(with: .goingAway, reason: nil)
        webSocketTask = nil
        state = .disconnected
    }

    // MARK: - Bild senden

    func sendImage(
        jpegData: Data,
        widthPx: Int,
        heightPx: Int,
        context: UploadContext
    ) async throws -> String {
        guard case .connected = state else {
            throw ConnectionError.notConnected
        }

        let uploadId = UUID().uuidString

        let base64String = jpegData.base64EncodedString()

        let message = UploadMessage(
            type: "upload",
            id: uploadId,
            skill: "schuelerarbeit_bewerten",
            image: ImagePayload(
                data: base64String,
                format: "jpeg",
                widthPx: widthPx,
                heightPx: heightPx
            ),
            context: context
        )

        let encoder = JSONEncoder()
        let jsonData = try encoder.encode(message)
        guard let jsonString = String(data: jsonData, encoding: .utf8) else {
            throw ConnectionError.encodingFailed
        }

        try await webSocketTask?.send(.string(jsonString))
        return uploadId
    }

    // MARK: - Nachrichten empfangen

    private func startReceiving() {
        webSocketTask?.receive { [weak self] result in
            guard let self = self else { return }

            switch result {
            case .success(let message):
                self.handleMessage(message)
                self.startReceiving() // rekursiv weiterhören

            case .failure(let error):
                Task { @MainActor in
                    if self.reconnectAttempts < self.maxReconnectAttempts {
                        self.reconnectAttempts += 1
                        self.state = .disconnected
                        try? await Task.sleep(nanoseconds: UInt64(self.reconnectDelay) * 1_000_000_000)
                        await self.connect()
                    } else {
                        self.state = .error("Verbindung verloren: \(error.localizedDescription)")
                    }
                }
            }
        }
    }

    private func handleMessage(_ message: URLSessionWebSocketTask.Message) {
        let jsonString: String
        switch message {
        case .string(let s):    jsonString = s
        case .data(let d):      jsonString = String(data: d, encoding: .utf8) ?? ""
        @unknown default:       return
        }

        guard let data = jsonString.data(using: .utf8),
              let serverMsg = try? JSONDecoder().decode(ServerMessage.self, from: data)
        else { return }

        Task { @MainActor in
            self.onMessage?(serverMsg)
        }
    }

    // MARK: - Hilfsmethoden

    private func ping() async throws {
        try await withCheckedThrowingContinuation { continuation in
            webSocketTask?.sendPing { error in
                if let error = error {
                    continuation.resume(throwing: error)
                } else {
                    continuation.resume()
                }
            }
        }
    }

    private func buildURL() -> URL? {
        var components = URLComponents()
        components.scheme = "ws"
        components.host = host
        components.port = Int(port)
        components.path = path
        return components.url
    }

    private var reconnectDelay: Double {
        // Exponential backoff: 1s, 2s, 4s, 8s, 16s
        return min(pow(2.0, Double(reconnectAttempts)), 16)
    }
}

// MARK: - Fehlertypen

enum ConnectionError: LocalizedError {
    case notConnected
    case encodingFailed
    case timeout

    var errorDescription: String? {
        switch self {
        case .notConnected:     return "Nicht mit OpenClaw verbunden"
        case .encodingFailed:   return "Nachricht konnte nicht kodiert werden"
        case .timeout:          return "Zeitüberschreitung"
        }
    }
}
