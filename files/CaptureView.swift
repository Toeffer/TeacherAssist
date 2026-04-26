// CaptureView.swift
// Hauptscreen: Foto aufnehmen, Kontext eingeben, Auswertung starten.
//
// Layout:
//   ┌─────────────────────────┐
//   │  Vorschau / Kamera-     │
//   │  Button                 │
//   ├─────────────────────────┤
//   │  Fach | Klasse | Aufg.  │
//   ├─────────────────────────┤
//   │  [Auswerten] Button     │
//   └─────────────────────────┘

import SwiftUI

struct CaptureView: View {

    @ObservedObject var viewModel: UploadViewModel
    @ObservedObject var connection: ConnectionService

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 20) {

                    // Verbindungsstatus-Banner
                    ConnectionBanner(state: connection.state)

                    // Bildbereich
                    ImagePreviewArea(
                        image: viewModel.capturedImage,
                        onCameraTap: { viewModel.showCameraPicker = true },
                        onGalleryTap: { viewModel.showGalleryPicker = true }
                    )

                    // Kontext-Eingabe
                    ContextForm(
                        fach: $viewModel.fach,
                        klasse: $viewModel.klasse,
                        aufgabe: $viewModel.aufgabe
                    )

                    // Auswertung starten
                    AuswertungButton(
                        state: viewModel.uploadState,
                        canUpload: canUpload
                    ) {
                        Task { await viewModel.startUpload() }
                    }

                    // Fortschritt / Ergebnis
                    ResultArea(state: viewModel.uploadState) {
                        viewModel.reset()
                    }
                }
                .padding()
            }
            .navigationTitle("Schülerarbeit bewerten")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    ConnectionIndicator(state: connection.state)
                }
            }
        }
        .sheet(isPresented: $viewModel.showCameraPicker) {
            CameraPicker(capturedImage: $viewModel.capturedImage)
                .ignoresSafeArea()
        }
        .sheet(isPresented: $viewModel.showGalleryPicker) {
            GalleryPicker(capturedImage: $viewModel.capturedImage)
        }
    }

    private var canUpload: Bool {
        viewModel.capturedImage != nil &&
        !viewModel.fach.isEmpty &&
        !viewModel.klasse.isEmpty &&
        connection.state == .connected(host: connection.state.host ?? "")
    }
}

// MARK: - Subviews

struct ConnectionBanner: View {
    let state: ConnectionState

    var body: some View {
        if case .error = state {
            HStack {
                Image(systemName: "wifi.exclamationmark")
                Text("Nicht verbunden – gehe zum Tab 'Verbinden'")
                    .font(.caption)
            }
            .padding(10)
            .frame(maxWidth: .infinity)
            .background(.orange.opacity(0.15), in: RoundedRectangle(cornerRadius: 8))
            .foregroundStyle(.orange)
        }
    }
}

struct ImagePreviewArea: View {
    let image: UIImage?
    let onCameraTap: () -> Void
    let onGalleryTap: () -> Void

    var body: some View {
        ZStack {
            RoundedRectangle(cornerRadius: 16)
                .fill(Color(.secondarySystemBackground))
                .frame(height: 260)

            if let image {
                Image(uiImage: image)
                    .resizable()
                    .scaledToFit()
                    .frame(height: 260)
                    .clipShape(RoundedRectangle(cornerRadius: 16))
            } else {
                VStack(spacing: 16) {
                    Image(systemName: "doc.text.viewfinder")
                        .font(.system(size: 50))
                        .foregroundStyle(.tertiary)
                    Text("Schülerarbeit fotografieren")
                        .font(.callout)
                        .foregroundStyle(.secondary)

                    HStack(spacing: 12) {
                        Button(action: onCameraTap) {
                            Label("Kamera", systemImage: "camera")
                                .font(.callout.weight(.medium))
                                .padding(.horizontal, 16)
                                .padding(.vertical, 8)
                                .background(.blue, in: Capsule())
                                .foregroundStyle(.white)
                        }
                        Button(action: onGalleryTap) {
                            Label("Galerie", systemImage: "photo.on.rectangle")
                                .font(.callout.weight(.medium))
                                .padding(.horizontal, 16)
                                .padding(.vertical, 8)
                                .background(Color(.tertiarySystemBackground), in: Capsule())
                                .foregroundStyle(.primary)
                        }
                    }
                }
            }

            // Bild ersetzen (wenn bereits ein Bild vorhanden)
            if image != nil {
                VStack {
                    HStack {
                        Spacer()
                        Button(action: onCameraTap) {
                            Image(systemName: "arrow.counterclockwise.circle.fill")
                                .font(.title2)
                                .foregroundStyle(.white)
                                .background(Circle().fill(.black.opacity(0.4)))
                        }
                        .padding(8)
                    }
                    Spacer()
                }
            }
        }
    }
}

struct ContextForm: View {
    @Binding var fach: String
    @Binding var klasse: String
    @Binding var aufgabe: String

    var body: some View {
        VStack(spacing: 12) {
            HStack(spacing: 12) {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Fach *").font(.caption).foregroundStyle(.secondary)
                    TextField("z. B. Mathematik", text: $fach)
                        .textFieldStyle(.roundedBorder)
                }

                VStack(alignment: .leading, spacing: 4) {
                    Text("Klasse *").font(.caption).foregroundStyle(.secondary)
                    TextField("z. B. 7a", text: $klasse)
                        .textFieldStyle(.roundedBorder)
                        .frame(maxWidth: 80)
                }
            }

            VStack(alignment: .leading, spacing: 4) {
                Text("Aufgabe / Prüfungsname (optional)")
                    .font(.caption).foregroundStyle(.secondary)
                TextField("z. B. Bruchrechnung Test 3", text: $aufgabe)
                    .textFieldStyle(.roundedBorder)
            }
        }
        .padding()
        .background(Color(.secondarySystemBackground), in: RoundedRectangle(cornerRadius: 12))
    }
}

struct AuswertungButton: View {
    let state: UploadState
    let canUpload: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack {
                if isLoading {
                    ProgressView().tint(.white)
                } else {
                    Image(systemName: "wand.and.stars")
                }
                Text(buttonTitle)
                    .fontWeight(.semibold)
            }
            .frame(maxWidth: .infinity)
            .padding()
            .background(
                canUpload && !isLoading ? .blue : .gray,
                in: RoundedRectangle(cornerRadius: 14)
            )
            .foregroundStyle(.white)
        }
        .disabled(!canUpload || isLoading)
    }

    private var isLoading: Bool {
        switch state {
        case .optimizing, .uploading, .processing: return true
        default: return false
        }
    }

    private var buttonTitle: String {
        switch state {
        case .optimizing:           return "Bild wird optimiert..."
        case .uploading:            return "Wird übertragen..."
        case .processing(let s, _): return s
        default:                    return "Jetzt auswerten"
        }
    }
}

struct ResultArea: View {
    let state: UploadState
    let onReset: () -> Void

    var body: some View {
        switch state {
        case .processing(let step, let percent):
            ProgressCard(step: step, percent: percent)

        case .done(let result):
            ResultCard(result: result, onReset: onReset)

        case .failed(let msg):
            ErrorCard(message: msg, onReset: onReset)

        default:
            EmptyView()
        }
    }
}

struct ProgressCard: View {
    let step: String
    let percent: Int

    var body: some View {
        VStack(spacing: 12) {
            ProgressView(value: Double(percent), total: 100)
                .tint(.blue)
            Text(step)
                .font(.callout)
                .foregroundStyle(.secondary)
        }
        .padding()
        .background(Color(.secondarySystemBackground), in: RoundedRectangle(cornerRadius: 12))
    }
}

struct ResultCard: View {
    let result: EvaluationResult
    let onReset: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                VStack(alignment: .leading) {
                    Text("Ergebnis").font(.headline)
                    Text(result.timestamp.formatted(date: .omitted, time: .shortened))
                        .font(.caption).foregroundStyle(.secondary)
                }
                Spacer()
                // Note groß anzeigen
                VStack {
                    Text(result.note)
                        .font(.system(size: 36, weight: .bold))
                        .foregroundStyle(.blue)
                    Text(result.punkte + " Pkt.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }

            Divider()

            Text("Feedback")
                .font(.subheadline.weight(.medium))

            Text(result.feedback)
                .font(.callout)
                .foregroundStyle(.secondary)

            // Hinweis: Vorschlag
            HStack(spacing: 6) {
                Image(systemName: "info.circle")
                    .font(.caption)
                Text("Dies ist ein Vorschlag. Die endgültige Note liegt bei dir.")
                    .font(.caption)
            }
            .foregroundStyle(.orange)
            .padding(8)
            .background(.orange.opacity(0.1), in: RoundedRectangle(cornerRadius: 8))

            Button("Nächste Arbeit") {
                onReset()
            }
            .frame(maxWidth: .infinity)
            .padding()
            .background(.blue, in: RoundedRectangle(cornerRadius: 12))
            .foregroundStyle(.white)
            .fontWeight(.semibold)
        }
        .padding()
        .background(Color(.secondarySystemBackground), in: RoundedRectangle(cornerRadius: 12))
    }
}

struct ErrorCard: View {
    let message: String
    let onReset: () -> Void

    var body: some View {
        VStack(spacing: 12) {
            Image(systemName: "exclamationmark.triangle.fill")
                .font(.title).foregroundStyle(.orange)
            Text(message)
                .font(.callout).multilineTextAlignment(.center)
            Button("Erneut versuchen", action: onReset)
                .buttonStyle(.bordered)
        }
        .padding()
        .frame(maxWidth: .infinity)
        .background(Color(.secondarySystemBackground), in: RoundedRectangle(cornerRadius: 12))
    }
}

struct ConnectionIndicator: View {
    let state: ConnectionState

    var body: some View {
        switch state {
        case .connected:
            Image(systemName: "wifi").foregroundStyle(.green)
        case .connecting:
            ProgressView().scaleEffect(0.8)
        default:
            Image(systemName: "wifi.slash").foregroundStyle(.red)
        }
    }
}

// MARK: - ConnectionState Helper

extension ConnectionState {
    var host: String? {
        if case .connected(let h) = self { return h }
        return nil
    }
}
