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
            GeometryReader { geometry in
                ScrollView {
                    VStack(spacing: 42) {
                        Spacer(minLength: 12)
                        Button { showingDetails = true } label: {
                            VStack(spacing: 8) {
                                Text("now:").font(.title3).foregroundStyle(.secondary)
                                HStack(alignment: .firstTextBaseline, spacing: 1) {
                                    Text(model.displayEarthDateMajor)
                                        .font(.system(size: 48, weight: .light, design: .rounded))
                                    Text(model.displayEarthDateMinor)
                                        .font(.system(size: 24, weight: .light, design: .rounded))
                                        .foregroundStyle(.secondary)
                                }
                                .monospacedDigit().lineLimit(1).minimumScaleFactor(0.6)
                            }
                            .frame(maxWidth: .infinity).contentShape(Rectangle())
                        }
                        .buttonStyle(.plain)
                        .accessibilityLabel(LF("Earth Date %@. Show details", model.displayEarthDate))
                        Button { showingDetails = true } label: {
                            VStack(spacing: 8) {
                                Text("solar phase:").font(.callout).foregroundStyle(.secondary)
                                Text(model.displaySolarPhase)
                                    .font(.system(size: 36, weight: .light, design: .rounded).monospacedDigit())
                                Text(model.locationText).font(.caption).foregroundStyle(.secondary)
                                if !model.solarNotice.isEmpty {
                                    Text(model.solarNotice).font(.caption).foregroundStyle(.orange)
                                }
                                SolarPhaseBar(phase: Double(model.displaySolarPhase))
                                    .padding(.top, 12)
                            }
                            .frame(maxWidth: .infinity).contentShape(Rectangle())
                        }
                        .buttonStyle(.plain)
                        .accessibilityLabel(LF("Solar phase %@. %@. Show details", model.displaySolarPhase, model.locationText))
                        .accessibilityHint("0.5 = solar noon at the selected longitude.")
                        VStack(spacing: 10) {
                            Text(model.compactStatus).font(.caption).foregroundStyle(.secondary)
                            Button("Details", systemImage: "info.circle") { showingDetails = true }
                                .font(.caption)
                        }
                        Spacer(minLength: 12)
                    }
                    .padding(.horizontal)
                    .frame(minHeight: geometry.size.height)
                }
            }
            .navigationTitle("NEPP")
            .toolbar {
                Button { model.synchronize(host: serverHost, port: serverPort) } label: {
                    Image(systemName: "arrow.clockwise")
                }
                .disabled(model.isSynchronizing)
                .accessibilityLabel("Refresh")
                Button { showingSettings = true } label: { Image(systemName: "gearshape") }
                    .accessibilityLabel("Settings")
            }
        }
        .sheet(isPresented: $showingSettings) {
            SettingsView(host: $serverHost, port: $serverPort, model: model)
        }
        .sheet(isPresented: $showingDetails) {
            DetailsView(model: model, host: serverHost, port: serverPort)
        }
        .onAppear { if scenePhase == .active { model.start(host: serverHost, port: serverPort) } }
        .onDisappear { model.stop() }
        .onChange(of: scenePhase) { _, phase in
            if phase == .active { model.start(host: serverHost, port: serverPort) }
            else { model.stop() }
        }
        .onChange(of: serverHost) { if scenePhase == .active { model.start(host: serverHost, port: serverPort) } }
        .onChange(of: serverPort) { if scenePhase == .active { model.start(host: serverHost, port: serverPort) } }
    }
}

private struct SolarPhaseBar: View {
    let phase: Double?

    var body: some View {
        VStack(spacing: 8) {
            GeometryReader { geometry in
                let inset: CGFloat = 5
                let width = max(0, geometry.size.width - 2 * inset)
                ZStack(alignment: .leading) {
                    Capsule()
                        .fill(.secondary.opacity(0.3))
                        .frame(height: 1)
                        .padding(.horizontal, inset)
                    Rectangle()
                        .fill(.secondary.opacity(0.6))
                        .frame(width: 1, height: 7)
                        .offset(x: geometry.size.width / 2 - 0.5)
                    if let phase, phase.isFinite, phase >= 0, phase < 1 {
                        Circle()
                            .fill(Color.accentColor)
                            .frame(width: 10, height: 10)
                            .shadow(color: .accentColor.opacity(0.35), radius: 5)
                            .offset(x: width * CGFloat(phase))
                    }
                }
                .frame(height: 12)
            }
            .frame(height: 12)
            HStack(alignment: .top, spacing: 4) {
                Text("0 · Solar midnight")
                    .frame(maxWidth: .infinity, alignment: .leading)
                Text("0.5 · Solar noon")
                    .frame(maxWidth: .infinity)
                    .multilineTextAlignment(.center)
                Text("1")
                    .frame(maxWidth: .infinity, alignment: .trailing)
            }
            .font(.caption2)
            .foregroundStyle(.secondary)
        }
        .frame(maxWidth: 380)
        // The surrounding button announces the phase and opens Details.
        .accessibilityHidden(true)
    }
}

private struct DetailsView: View {
    @Environment(\.dismiss) private var dismiss
    @ObservedObject var model: NEPPViewModel
    let host: String
    let port: Int
    var body: some View {
        NavigationStack {
            List {
                Section("Connection") {
                    LabeledContent("Server", value: "\(host):\(port)")
                    Text(model.sourceText)
                    LabeledContent("Last response", value: model.lastUpdateText)
                    Text(model.compactStatus)
                    if !model.retryText.isEmpty { Text(model.retryText) }
                    if !model.lastError.isEmpty {
                        Text(model.lastError).foregroundStyle(.orange)
                    }
                }
                Section("Earth Date") {
                    Text(model.displayEarthDate).monospacedDigit()
                    Text(model.edQualityText)
                    Text(model.edMetadata).font(.caption)
                }
                Section("Solar phase") {
                    Text(model.displaySolarPhase).monospacedDigit()
                    Text(model.locationText)
                    Text("0.5 = solar noon at the selected longitude.")
                    Text(model.solarQualityText)
                    Text(model.solarMetadata).font(.caption)
                    Text(model.locationMessage).font(.caption)
                }
                Section("About these values") {
                    Text("Experimental. Display accuracy is unassessed. Network delay is estimated assuming a symmetric path.")
                    Text("A source stratum describes the source path, not a guarantee of precision.")
                    Text(model.displayLocalTime).font(.caption)
                }
            }
            .textSelection(.enabled)
            .navigationTitle("Details")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) { Button("Done") { dismiss() } }
            }
        }
    }
}

private struct SettingsView: View {
    @Environment(\.dismiss) private var dismiss
    @Binding var host: String
    @Binding var port: Int
    @ObservedObject var model: NEPPViewModel
    @FocusState private var focusedField: Field?

    private enum Field { case host, port, longitude }

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

                Section("Solar reference") {
                    Toggle("Use current location", isOn: Binding(
                        get: { model.wantsLocation },
                        set: { enabled in
                            if enabled { model.useCurrentLocation() }
                            else { model.disableLocation() }
                        }
                    ))
                    Text(model.locationMessage).font(.caption)
                    Toggle("Manual longitude", isOn: Binding(
                        get: { model.useManualLongitude },
                        set: { enabled in
                            if enabled { model.disableLocation() }
                            model.useManualLongitude = enabled
                        }
                    ))
                    if model.useManualLongitude {
                        TextField("Longitude (east positive)", text: $model.manualLongitude)
                            .keyboardType(.numbersAndPunctuation)
                            .focused($focusedField, equals: .longitude)
                        Text("−180 to 180 degrees. Manual locations are reference points, not GPS fixes.")
                            .font(.caption)
                    }
                }

                Section("About") {
                    Text("Experimental V2 · accuracy unassessed. No V1 fallback.").font(.caption)
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
