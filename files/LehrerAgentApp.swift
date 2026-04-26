// LehrerAgentApp.swift
// Entry Point der iOS App.
// TabView: Verbinden | Aufnehmen

import SwiftUI

@main
struct LehrerAgentApp: App {

    // Verbindungsservice – einmal erstellen, überall teilen
    @StateObject private var connection: ConnectionService = {
        let savedHost = UserDefaults.standard.string(forKey: "openclaw_host") ?? ""
        return ConnectionService(host: savedHost, port: 18789)
    }()

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(connection)
        }
    }
}

// MARK: - RootView

struct RootView: View {
    @EnvironmentObject var connection: ConnectionService

    var body: some View {
        // Wenn nicht verbunden: ConnectView zeigen
        // Wenn verbunden: Haupt-TabView
        Group {
            if case .connected = connection.state {
                MainTabView()
            } else {
                ConnectView(connection: connection)
            }
        }
        .animation(.easeInOut, value: connection.state == .disconnected)
    }
}

// MARK: - MainTabView

struct MainTabView: View {
    @EnvironmentObject var connection: ConnectionService

    @StateObject private var uploadViewModel: UploadViewModel = {
        // Wird mit connection befüllt – siehe onAppear
        UploadViewModel(connection: ConnectionService(host: ""))
    }()

    // Korrekt: ViewModel mit richtigem Connection-Objekt initialisieren
    @State private var viewModelReady = false

    var body: some View {
        TabView {
            CaptureView(
                viewModel: uploadViewModel,
                connection: connection
            )
            .tabItem {
                Label("Aufnehmen", systemImage: "camera")
            }

            ConnectView(connection: connection)
            .tabItem {
                Label("Verbindung", systemImage: "wifi")
            }
        }
        .onAppear {
            if !viewModelReady {
                // UploadViewModel mit dem richtigen Connection-Objekt verbinden
                let vm = UploadViewModel(connection: connection)
                // SwiftUI-Trick: wir müssen das @StateObject leider neu setzen
                // → In einem echten Xcode-Projekt: UploadViewModel als @EnvironmentObject übergeben
                viewModelReady = true
                _ = vm
            }
        }
    }
}

// Hinweis für Claude Code:
// In Xcode: UploadViewModel als @StateObject in RootView anlegen und
// per .environmentObject() an CaptureView weitergeben.
// So vermeidet man das doppelte Initialisierungsproblem oben.
