// UploadViewModel.swift
// Steuert den kompletten Ablauf:
// Bild aufnehmen → optimieren → senden → Fortschritt → Ergebnis anzeigen.

import SwiftUI
import Combine

// MARK: - Upload-Status

enum UploadState: Equatable {
    case idle
    case optimizing                    // Bild wird komprimiert
    case uploading(progress: Double)   // Übertragung läuft (0.0–1.0)
    case processing(step: String, percent: Int) // Agent arbeitet
    case done(result: EvaluationResult)
    case failed(message: String)
}

// MARK: - Bewertungsergebnis

struct EvaluationResult: Equatable {
    let uploadId: String
    let punkte: String          // z. B. "34/50"
    let note: String            // z. B. "3"
    let feedback: String        // Ausführliches Feedback vom Agenten
    let timestamp: Date
}

// MARK: - ViewModel

@MainActor
class UploadViewModel: ObservableObject {

    // State
    @Published var uploadState: UploadState = .idle
    @Published var capturedImage: UIImage?
    @Published var showCameraPicker = false
    @Published var showGalleryPicker = false

    // Formular: Kontext für den Agenten
    @Published var fach: String = ""
    @Published var klasse: String = ""
    @Published var aufgabe: String = ""

    // Verbindungsservice (wird von außen injiziert)
    private let connection: ConnectionService

    // Laufende Upload-ID (für Fortschritts-Tracking)
    private var currentUploadId: String?

    init(connection: ConnectionService) {
        self.connection = connection

        // Server-Nachrichten abhören
        connection.onMessage = { [weak self] message in
            Task { @MainActor in
                self?.handleServerMessage(message)
            }
        }
    }

    // MARK: - Upload starten

    func startUpload() async {
        guard let image = capturedImage else { return }
        guard !fach.isEmpty && !klasse.isEmpty else {
            uploadState = .failed(message: "Bitte Fach und Klasse eingeben")
            return
        }

        // 1. Perspektivkorrektur versuchen
        uploadState = .optimizing
        let corrected = ImageService.perspectiveCorrect(image)

        // 2. Bild optimieren
        guard let optimized = ImageService.optimize(corrected) else {
            uploadState = .failed(message: "Bild konnte nicht optimiert werden")
            return
        }

        // 3. Größeninfo loggen (Debugging)
        debugPrint("Bildgröße: \(optimized.originalSizeKB) KB → \(optimized.optimizedSizeKB) KB")
        debugPrint("Auflösung: \(optimized.widthPx) × \(optimized.heightPx) px")

        // 4. Verbindung prüfen
        guard case .connected = connection.state else {
            uploadState = .failed(message: "Nicht verbunden mit OpenClaw.\nBitte erst verbinden.")
            return
        }

        // 5. Senden
        uploadState = .uploading(progress: 0.1)

        let context = UploadContext(
            fach: fach,
            klasse: klasse,
            aufgabe: aufgabe.isEmpty ? "Allgemeine Bewertung" : aufgabe
        )

        do {
            let uploadId = try await connection.sendImage(
                jpegData: optimized.jpegData,
                widthPx: optimized.widthPx,
                heightPx: optimized.heightPx,
                context: context
            )
            currentUploadId = uploadId
            uploadState = .uploading(progress: 1.0)

        } catch {
            uploadState = .failed(message: "Senden fehlgeschlagen: \(error.localizedDescription)")
        }
    }

    // MARK: - Server-Antworten verarbeiten

    private func handleServerMessage(_ message: ServerMessage) {
        // Nur Nachrichten für den aktuellen Upload verarbeiten
        guard message.id == currentUploadId else { return }

        switch message.type {

        case "progress":
            let step = message.step ?? "Verarbeitung läuft..."
            let percent = message.percent ?? 0
            uploadState = .processing(step: step, percent: percent)

        case "result":
            let result = EvaluationResult(
                uploadId: message.id,
                punkte: message.punkte ?? "–",
                note: message.note ?? "–",
                feedback: message.feedback ?? "Kein Feedback erhalten",
                timestamp: Date()
            )
            uploadState = .done(result: result)
            currentUploadId = nil

        case "error":
            uploadState = .failed(message: message.message ?? "Unbekannter Fehler")
            currentUploadId = nil

        default:
            break
        }
    }

    // MARK: - Zurücksetzen

    func reset() {
        uploadState = .idle
        capturedImage = nil
        currentUploadId = nil
        // Fach/Klasse/Aufgabe bleiben erhalten (für nächste Arbeit)
    }
}
