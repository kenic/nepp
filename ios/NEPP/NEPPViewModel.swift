import Foundation

@MainActor
final class NEPPViewModel: ObservableObject {
    enum Status {
        case idle
        case connecting
        case synchronized(stratum: UInt8, at: Date)
        case failed(String)
    }

    @Published private(set) var displayEarthDate = "—"
    @Published private(set) var displayEarthDateMajor = "—"
    @Published private(set) var displayEarthDateMinor = ""
    @Published private(set) var displayLocalTime = "—"
    @Published private(set) var status: Status = .idle
    @Published private(set) var isSynchronizing = false

    private let client = NEPPClient()
    private var pollingTask: Task<Void, Never>?
    private var displayTask: Task<Void, Never>?
    private var anchorEarthDate: Double?
    private var anchorUptime: TimeInterval?
    private var rate = 0.0

    func start(host: String, port: Int) {
        stop()
        displayTask = Task { [weak self] in
            while !Task.isCancelled {
                self?.updateDisplay()
                try? await Task.sleep(for: .milliseconds(10))
            }
        }
        pollingTask = Task { [weak self] in
            guard let self else { return }
            while !Task.isCancelled {
                await self.synchronizeOnce(host: host, port: port)
                try? await Task.sleep(for: .seconds(60))
            }
        }
    }

    func stop() {
        pollingTask?.cancel()
        displayTask?.cancel()
        pollingTask = nil
        displayTask = nil
        isSynchronizing = false
    }

    func synchronize(host: String, port: Int) {
        Task { await synchronizeOnce(host: host, port: port) }
    }

    private func synchronizeOnce(host: String, port: Int) async {
        guard !isSynchronizing else { return }
        isSynchronizing = true
        status = .connecting
        defer { isSynchronizing = false }
        do {
            let response = try await client.query(host: host, port: port)
            anchorEarthDate = response.transmit.value
            anchorUptime = ProcessInfo.processInfo.systemUptime
            rate = response.rate
            updateDisplay()
            status = .synchronized(stratum: response.stratum, at: Date())
        } catch is CancellationError {
            return
        } catch {
            status = .failed(error.localizedDescription)
        }
    }

    private func updateDisplay() {
        guard let anchorEarthDate, let anchorUptime else { return }
        let elapsed = ProcessInfo.processInfo.systemUptime - anchorUptime
        let current = anchorEarthDate + rate * elapsed
        let formatted = String(format: "%.10f", current)
        displayEarthDate = formatted
        displayEarthDateMajor = String(formatted.dropLast(6))
        displayEarthDateMinor = String(formatted.suffix(6))
        displayLocalTime = Date().formatted(date: .abbreviated, time: .standard)
    }
}
