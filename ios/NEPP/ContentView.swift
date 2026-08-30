import SwiftUI

struct ContentView: View {
    @Environment(\.scenePhase) private var scenePhase
    @StateObject private var model = NEPPViewModel()
    @AppStorage("serverHost") private var serverHost = "nepp.kenic.jp"
    @AppStorage("serverPort") private var serverPort = 56377
    @State private var showingDetails = false
    @State private var showingSettings = false

    var body: some View {
        NavigationStack {
            VStack(spacing: 28) {
                Spacer()

                VStack(spacing: 4) {
                    Text("now:")
                        .font(.title3)
                        .foregroundStyle(.secondary)
                    HStack(alignment: .firstTextBaseline, spacing: 1) {
                        Text(model.displayEarthDateMajor)
                            .font(.system(size: 48, weight: .light, design: .rounded))
                        Text(model.displayEarthDateMinor)
                            .font(.system(size: 24, weight: .light, design: .rounded))
                            .foregroundStyle(.secondary)
                    }
                    .monospacedDigit()
                    .lineLimit(1)
                    .minimumScaleFactor(0.65)
                    .contentTransition(.numericText())
                    .accessibilityElement(children: .ignore)
                    .accessibilityLabel("Earth Date \(model.displayEarthDate)")
                }
                .contentShape(Rectangle())
                .onTapGesture { withAnimation { showingDetails.toggle() } }

                status
                if showingDetails {
                    Text(model.displayLocalTime)
                        .font(.callout.monospacedDigit())
                        .foregroundStyle(.secondary)
                        .transition(.opacity.combined(with: .move(edge: .top)))
                }
                Spacer()
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

                Button {
                    showingSettings = true
                } label: {
                    Image(systemName: "gearshape")
                }
                .accessibilityLabel("Settings")
            }
        }
        .sheet(isPresented: $showingSettings) {
            SettingsView(host: $serverHost, port: $serverPort)
        }
        .onAppear { model.start(host: serverHost, port: serverPort) }
        .onDisappear { model.stop() }
        .onChange(of: scenePhase) { _, phase in
            if phase == .active {
                model.start(host: serverHost, port: serverPort)
            } else {
                model.stop()
            }
        }
        .onChange(of: serverHost) { model.start(host: serverHost, port: serverPort) }
        .onChange(of: serverPort) { model.start(host: serverHost, port: serverPort) }
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

private struct SettingsView: View {
    @Environment(\.dismiss) private var dismiss
    @Binding var host: String
    @Binding var port: Int
    @FocusState private var focusedField: Field?

    private enum Field { case host, port }

    var body: some View {
        NavigationStack {
            Form {
                Section("NEPP server") {
                    TextField("Host", text: $host)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                        .focused($focusedField, equals: .host)
                    TextField("Port", value: $port, format: .number.grouping(.never))
                        .keyboardType(.numberPad)
                        .focused($focusedField, equals: .port)
                }

                Section("About") {
                    Link(destination: URL(string: "https://nepp.kenic.jp/en/")!) {
                        Label("NEPP Website", systemImage: "safari")
                    }
                    LabeledContent("Version", value: appVersion)
                    LabeledContent("Build", value: appBuild)
                }
            }
            .scrollDismissesKeyboard(.interactively)
            .navigationTitle("Settings")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Done") { dismiss() }
                }
                ToolbarItemGroup(placement: .keyboard) {
                    Spacer()
                    Button("Done") { focusedField = nil }
                }
            }
        }
    }

    private var appVersion: String {
        Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "—"
    }

    private var appBuild: String {
        Bundle.main.object(forInfoDictionaryKey: "CFBundleVersion") as? String ?? "—"
    }
}
