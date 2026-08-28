import SwiftUI

struct ContentView: View {
    @Environment(\.scenePhase) private var scenePhase
    @StateObject private var model = NEPPViewModel()
    @AppStorage("serverHost") private var serverHost = "127.0.0.1"
    @AppStorage("serverPort") private var serverPort = 56377

    var body: some View {
        NavigationStack {
            VStack(spacing: 28) {
                Spacer()

                VStack(spacing: 4) {
                    Text("today:")
                        .font(.title3)
                        .foregroundStyle(.secondary)
                    Text(model.displayEarthDate)
                        .font(.system(size: 52, weight: .light, design: .rounded))
                        .monospacedDigit()
                        .contentTransition(.numericText())
                        .accessibilityLabel("Earth Date \(model.displayEarthDate)")
                }

                status
                Spacer()

                Form {
                    Section("NEPP server") {
                        TextField("Host", text: $serverHost)
                            .textInputAutocapitalization(.never)
                            .autocorrectionDisabled()
                        TextField("Port", value: $serverPort,
                                  format: .number.grouping(.never))
                            .keyboardType(.numberPad)
                    }
                }
                .frame(maxHeight: 190)
                .scrollContentBackground(.hidden)
            }
            .padding(.horizontal)
            .navigationTitle("NEPP")
            .toolbar {
                Button {
                    model.synchronize(host: serverHost, port: serverPort)
                } label: {
                    Image(systemName: "arrow.clockwise")
                }
                .disabled(model.isSynchronizing)
                .accessibilityLabel("Synchronize now")
            }
        }
        .onAppear { model.start(host: serverHost, port: serverPort) }
        .onDisappear { model.stop() }
        .onChange(of: scenePhase) { phase in
            if phase == .active {
                model.start(host: serverHost, port: serverPort)
            } else {
                model.stop()
            }
        }
        .onChange(of: serverHost) { _ in model.start(host: serverHost, port: serverPort) }
        .onChange(of: serverPort) { _ in model.start(host: serverHost, port: serverPort) }
    }

    @ViewBuilder
    private var status: some View {
        switch model.status {
        case .idle:
            Label("Not synchronized", systemImage: "circle.dashed")
                .foregroundStyle(.secondary)
        case .connecting:
            HStack { ProgressView(); Text("Synchronizing…") }
                .foregroundStyle(.secondary)
        case let .synchronized(stratum, date):
            VStack(spacing: 4) {
                Label("Stratum \(stratum)", systemImage: "checkmark.circle.fill")
                    .foregroundStyle(.green)
                Text("Updated \(date.formatted(date: .omitted, time: .standard))")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        case let .failed(message):
            Label(message, systemImage: "exclamationmark.triangle.fill")
                .font(.footnote)
                .foregroundStyle(.orange)
                .multilineTextAlignment(.center)
        }
    }
}
