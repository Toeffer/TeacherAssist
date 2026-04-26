// ConnectView.swift
// Erster Screen der App: IP-Adresse des Macs eingeben und verbinden.
//
// Der Lehrer gibt einmalig die lokale IP seines Macs ein
// (z. B. 192.168.1.42 – zu finden unter Mac → Systemeinstellungen → WLAN).
// Die IP wird in UserDefaults gespeichert und beim nächsten Start vorausgefüllt.

import SwiftUI

struct ConnectView: View {

    @ObservedObject var connection: ConnectionService
    @State private var hostInput: String = ""
    @State private var portInput: String = "18789"
    @State private var isConnecting = false

    // IP in UserDefaults merken
    private let hostKey = "openclaw_host"

    var body: some View {
        NavigationStack {
            VStack(spacing: 32) {

                // Logo / Header
                VStack(spacing: 8) {
                    Image(systemName: "graduationcap.fill")
                        .font(.system(size: 60))
                        .foregroundStyle(.blue)
                    Text("LehrerAgent")
                        .font(.largeTitle.bold())
                    Text("Verbinde dich mit deinem Mac im WLAN")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                        .multilineTextAlignment(.center)
                }
                .padding(.top, 40)

                // Eingabefelder
                VStack(spacing: 16) {
                    VStack(alignment: .leading, spacing: 6) {
                        Label("IP-Adresse deines Macs", systemImage: "desktopcomputer")
                            .font(.caption)
                            .foregroundStyle(.secondary)

                        TextField("z. B. 192.168.1.42", text: $hostInput)
                            .textFieldStyle(.roundedBorder)
                            .keyboardType(.numbersAndPunctuation)
                            .autocorrectionDisabled()
                            .textInputAutocapitalization(.never)
                    }

                    VStack(alignment: .leading, spacing: 6) {
                        Label("Port (Standard: 18789)", systemImage: "network")
                            .font(.caption)
                            .foregroundStyle(.secondary)

                        TextField("18789", text: $portInput)
                            .textFieldStyle(.roundedBorder)
                            .keyboardType(.numberPad)
                    }
                }
                .padding(.horizontal)

                // Hilfetipp
                HStack(alignment: .top, spacing: 8) {
                    Image(systemName: "info.circle")
                        .foregroundStyle(.blue)
                    Text("Die IP deines Macs findest du unter:\nSystemeinstellungen → WLAN → Details")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                .padding()
                .background(.blue.opacity(0.08), in: RoundedRectangle(cornerRadius: 10))
                .padding(.horizontal)

                // Verbinden-Button
                Button {
                    Task { await connect() }
                } label: {
                    HStack {
                        if isConnecting {
                            ProgressView().tint(.white)
                        }
                        Text(isConnecting ? "Verbinde..." : "Verbinden")
                            .fontWeight(.semibold)
                    }
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(canConnect ? .blue : .gray, in: RoundedRectangle(cornerRadius: 12))
                    .foregroundStyle(.white)
                }
                .disabled(!canConnect || isConnecting)
                .padding(.horizontal)

                // Fehlermeldung
                if case .error(let msg) = connection.state {
                    HStack(alignment: .top, spacing: 8) {
                        Image(systemName: "exclamationmark.triangle.fill")
                            .foregroundStyle(.orange)
                        Text(msg)
                            .font(.caption)
                    }
                    .padding()
                    .background(.orange.opacity(0.1), in: RoundedRectangle(cornerRadius: 10))
                    .padding(.horizontal)
                }

                Spacer()
            }
            .navigationTitle("")
            .navigationBarHidden(true)
            .onAppear {
                // Gespeicherte IP laden
                hostInput = UserDefaults.standard.string(forKey: hostKey) ?? ""
            }
        }
    }

    // MARK: - Computed

    private var canConnect: Bool {
        !hostInput.trimmingCharacters(in: .whitespaces).isEmpty &&
        !portInput.trimmingCharacters(in: .whitespaces).isEmpty
    }

    // MARK: - Verbinden

    private func connect() async {
        isConnecting = true

        // IP speichern
        UserDefaults.standard.set(hostInput.trimmingCharacters(in: .whitespaces), forKey: hostKey)

        await connection.connect()
        isConnecting = false
    }
}

// MARK: - Preview

#Preview {
    ConnectView(connection: ConnectionService(host: "192.168.1.42"))
}
