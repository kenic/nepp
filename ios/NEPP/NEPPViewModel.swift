import Foundation
import CoreLocation

@MainActor
final class NEPPViewModel: NSObject, ObservableObject, CLLocationManagerDelegate {
    enum Status {
        case idle, connecting, synchronized(stratum: UInt8, at: Date), failed(String)
    }
    @Published private(set) var displayEarthDate = "—"
    @Published private(set) var displayEarthDateMajor = "—"
    @Published private(set) var displayEarthDateMinor = ""
    @Published private(set) var displayLocalTime = "—"
    @Published private(set) var displaySolarPhase = "—"
    @Published private(set) var edQualityText = L("No sample")
    @Published private(set) var solarQualityText = L("No sample")
    @Published private(set) var locationText = L("Location unavailable")
    @Published private(set) var locationMessage = L("Location stays on this device.")
    @Published private(set) var status: Status = .idle
    @Published private(set) var isSynchronizing = false
    @Published private(set) var compactStatus = L("Connecting…")
    @Published private(set) var solarNotice = ""
    @Published private(set) var sourceText = "—"
    @Published private(set) var lastUpdateText = "—"
    @Published private(set) var lastError = ""
    @Published private(set) var retryText = ""
    @Published private(set) var edMetadata = "—"
    @Published private(set) var solarMetadata = "—"
    @Published var manualLongitude = "0" { didSet { updateDisplay() } }
    @Published var useManualLongitude = false { didSet { updateDisplay() } }
    private let client = NEPPClient()
    private let locationManager = CLLocationManager()
    private var location: CLLocation?
    @Published private(set) var wantsLocation = NEPPDisplayPolicy.prefersCurrentLocation() {
        didSet { UserDefaults.standard.set(wantsLocation, forKey: "useCurrentSolarLocation") }
    }
    private var active = false
    private var generation = UUID()
    private var pollingTask: Task<Void, Never>?
    private var displayTask: Task<Void, Never>?
    private var locationTask: Task<Void, Never>?
    private var locationPending = false
    private var permissionRequested = false
    private var locationRequestTime = Date.distantPast
    private var locationFailedRecently = false
    private var failures = 0
    private var sample: NEPPSample?

    override init() {
        super.init()
        locationManager.delegate = self
        locationManager.desiredAccuracy = kCLLocationAccuracyKilometer
        locationManager.distanceFilter = 1000
    }
    func start(host: String, port: Int) {
        stop()
        active = true
        let id = generation
        resumeLocation()
        locationTask = Task { [weak self] in
            while !Task.isCancelled {
                try? await Task.sleep(for: .seconds(60))
                guard !Task.isCancelled else { return }
                self?.resumeLocation()
            }
        }
        displayTask = Task { [weak self] in
            while !Task.isCancelled {
                self?.updateDisplay()
                try? await Task.sleep(for: .milliseconds(33))
            }
        }
        beginPolling(host: host, port: port, id: id)
    }
    private func beginPolling(host: String, port: Int, id: UUID) {
        pollingTask = Task { [weak self] in
            guard let self else { return }
            while !Task.isCancelled, id == self.generation {
                await self.synchronizeOnce(host: host, port: port, id: id)
                guard !Task.isCancelled, id == self.generation else { return }
                let delay = NEPPDisplayPolicy.retryDelay(failures: self.failures)
                self.retryText = self.failures == 0 ? "" : LF("Retry interval: %d seconds", Int(delay))
                try? await Task.sleep(for: .seconds(delay))
            }
        }
    }
    func stop() {
        active = false
        generation = UUID()
        pollingTask?.cancel(); displayTask?.cancel()
        locationTask?.cancel(); locationTask = nil
        pollingTask = nil; displayTask = nil
        locationManager.stopUpdatingLocation()
        locationPending = false
        sample = nil
        isSynchronizing = false
        status = .idle
        failures = 0; lastError = ""; retryText = ""; sourceText = "—"; lastUpdateText = "—"
        clearDisplay()
    }
    func synchronize(host: String, port: Int) {
        guard active else { return }
        // A manual retry must not erase a usable sample or the location.
        generation = UUID()
        pollingTask?.cancel()
        isSynchronizing = false
        beginPolling(host: host, port: port, id: generation)
    }
    private func synchronizeOnce(host: String, port: Int, id: UUID) async {
        guard active, id == generation else { return }
        isSynchronizing = true; status = .connecting
        defer { if id == generation { isSynchronizing = false } }
        do {
            let result = try await client.query(host: host.trimmingCharacters(in: .whitespacesAndNewlines), port: port)
            guard !Task.isCancelled, active, id == generation else { return }
            sample = result
            failures = 0; lastError = ""; retryText = ""
            sourceText = LF("Source: Stratum %d", Int(result.response.stratum))
            lastUpdateText = Date().formatted(date: .omitted, time: .standard)
            status = .synchronized(stratum: result.response.stratum, at: Date())
            updateDisplay()
        } catch {
            guard !Task.isCancelled, active, id == generation else { return }
            // Retain a recent sample only as explicitly labelled local prediction.
            status = .failed(error.localizedDescription)
            failures = min(failures + 1, 6)
            lastError = error.localizedDescription
            updateDisplay()
        }
    }
    private func clearDisplay() {
        displayEarthDate = "—"; displayEarthDateMajor = "—"; displayEarthDateMinor = ""
        displaySolarPhase = "—"; edQualityText = L("No current sample"); solarQualityText = L("No current sample")
        compactStatus = failures > 0 ? L("Reconnecting · no current value") : L("Connecting…")
        solarNotice = L("Unavailable")
        edMetadata = "—"; solarMetadata = "—"
    }
    private func qualityText(_ q: NEPPQuality, age: Double) -> String {
        let freshness: String
        if failures > 0 { freshness = L("Reconnecting · local estimate · ") + q.freshness(age: age) }
        else { freshness = q.freshness(age: age) }
        let quality = q.evaluated ? L("Server bound provided; total accuracy unassessed") : L("Accuracy unassessed")
        return "\(freshness) · \(quality)"
    }
    private func updateDisplay() {
        let now = ProcessInfo.processInfo.systemUptime
        guard let sample else { clearDisplay(); return }
        guard sample.usable(at: now) else {
            clearDisplay()
            compactStatus = L("Value expired · reconnecting")
            return
        }
        let age = sample.age(at: now)
        compactStatus = NEPPDisplayPolicy.status(age: age, validity: sample.response.edQuality.validity,
                                                 failures: failures, holdover: sample.response.edQuality.state == 2)
        edMetadata = metadata(sample.response.edQuality, age: age)
        let formatted = String(format: "%.10f", sample.earthDate(at: now))
        displayEarthDate = formatted
        displayEarthDateMajor = String(formatted.dropLast(6))
        displayEarthDateMinor = String(formatted.suffix(6))
        displayLocalTime = L("Device clock: ") + Date().formatted(date: .abbreviated, time: .standard)
        edQualityText = qualityText(sample.response.edQuality, age: sample.age(at: now))
        let longitude: Double
        if useManualLongitude {
            guard let value = Double(manualLongitude), value.isFinite, (-180...180).contains(value) else {
                displaySolarPhase = "—"; locationText = L("Invalid manual longitude")
                solarQualityText = L("Enter −180 to 180 degrees (east positive).")
                solarNotice = L("Invalid longitude"); solarMetadata = "—"; return
            }
            longitude = value
            locationText = String(format: L("Manual reference · %.3f°"), value)
        } else if let location,
                  abs(location.coordinate.latitude) < 89.9 {
            longitude = location.coordinate.longitude
            let label = NEPPDisplayPolicy.locationLabel(age: max(0, -location.timestamp.timeIntervalSinceNow),
                                                       failed: locationFailedRecently)
            locationText = String(format: "\(label) · %.3f°", longitude)
        } else if wantsLocation {
            displaySolarPhase = "—"; locationText = L("Location unavailable")
            solarNotice = L("Location needed")
            solarMetadata = "—"
            solarQualityText = L("Choose a manual longitude or stop location use for Greenwich.")
            return
        } else {
            longitude = 0
            locationText = L("Greenwich reference · 0° (not current location)")
        }
        if let phase = sample.solarPhase(at: now, longitude: longitude), let q = sample.response.spQuality {
            displaySolarPhase = String(format: "%.6f", floor(phase * 1_000_000) / 1_000_000)
            solarQualityText = qualityText(q, age: sample.age(at: now))
            solarMetadata = metadata(q, age: age)
            solarNotice = q.validity != .max && age > Double(q.validity) ? L("Stale · estimated") : ""
        } else {
            displaySolarPhase = "—"
            solarQualityText = sample.response.solarIssue ?? L("Solar phase unavailable")
            solarNotice = L("Unavailable"); solarMetadata = "—"
        }
    }
    private func metadata(_ q: NEPPQuality, age: Double) -> String {
        let validity = q.validity == .max ? L("Unknown") : LF("%u s from transmission", q.validity)
        let uncertainty = q.evaluated ? String(format: "%.9g", Double(q.uncertainty) / 0x1p32) : L("Unassessed")
        let dataAge = q.dataAge == .max ? L("Unknown") : LF("%u s at transmission", q.dataAge)
        let updateAge = q.updateAge == .max ? L("Unknown") : LF("%u s at transmission", q.updateAge)
        let prediction = [L("Unknown"), L("No"), L("Yes")][Int(q.prediction)]
        return LF("Source kind: %u · stratum: %u\nUncertainty: %@\nValidity: %@\nEstimated age: %d s\nInput age: %@\nSource update age: %@\nPrediction used: %@",
                  UInt32(q.source), UInt32(q.stratum), uncertainty, validity, Int(max(0, age)), dataAge, updateAge, prediction)
    }
    func useCurrentLocation() {
        wantsLocation = true
        useManualLongitude = false
        if locationManager.authorizationStatus == .notDetermined {
            permissionRequested = true
            locationManager.requestWhenInUseAuthorization()
        } else { resumeLocation() }
        updateDisplay()
    }
    func disableLocation() {
        wantsLocation = false; location = nil
        locationPending = false; locationFailedRecently = false
        locationManager.stopUpdatingLocation()
        locationMessage = L("Location off. Greenwich or manual reference is used.")
        updateDisplay()
    }
    private func resumeLocation() {
        guard active, wantsLocation, !useManualLongitude else { return }
        if locationPending && Date().timeIntervalSince(locationRequestTime) < 45 { return }
        locationPending = false
        switch locationManager.authorizationStatus {
        case .authorizedAlways, .authorizedWhenInUse:
            locationMessage = L("Finding location… (never sent to server)")
            locationPending = true
            locationRequestTime = Date()
            // Periodic one-shot fixes also refresh stationary users. No distance
            // filter gates freshness, and requests never overlap indefinitely.
            locationManager.requestLocation()
        case .denied, .restricted:
            locationMessage = L("Location unavailable. ED still works; use Greenwich or manual longitude.")
        case .notDetermined:
            if !permissionRequested {
                permissionRequested = true
                locationManager.requestWhenInUseAuthorization()
            }
        default: break
        }
    }
    nonisolated func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
        Task { @MainActor [weak self] in self?.authorizationChanged() }
    }
    private func authorizationChanged() {
        if locationManager.authorizationStatus == .denied || locationManager.authorizationStatus == .restricted {
            location = nil
        }
        resumeLocation(); updateDisplay()
    }
    nonisolated func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        Task { @MainActor [weak self] in self?.receivedLocations(locations) }
    }
    private func receivedLocations(_ locations: [CLLocation]) {
        locationPending = false
        guard active, wantsLocation,
              [.authorizedAlways, .authorizedWhenInUse].contains(locationManager.authorizationStatus),
              let fix = locations.last, fix.horizontalAccuracy >= 0,
              CLLocationCoordinate2DIsValid(fix.coordinate), abs(fix.timestamp.timeIntervalSinceNow) < 300 else { return }
        location = fix
        locationFailedRecently = false
        locationMessage = abs(fix.coordinate.latitude) >= 89.9
            ? L("Near a pole: use a manual reference longitude.")
            : L("Location used only on this device; precision is not guaranteed.")
        updateDisplay()
    }
    nonisolated func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
        Task { @MainActor [weak self] in self?.locationFailed() }
    }
    private func locationFailed() {
        guard active, wantsLocation else { return }
        locationPending = false; locationFailedRecently = true
        locationMessage = L("Location refresh failed. Keeping the last known location; will retry.")
        updateDisplay()
    }
}
