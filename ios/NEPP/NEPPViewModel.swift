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
    @Published private(set) var status: Status = .idle
    @Published private(set) var isSynchronizing = false

    private let client = NEPPClient()
    private var pollingTask: Task<Void, Never>?
    private var displayTask: Task<Void, Never>?
    private var anchorEarthDate: Double?
    private var anchorTime: Date?
    private var rate = 0.0

    func start(host: String, port: Int) {
        stop()
        displayTask = Task { [weak self] in
            while !Task.isCancelled {
                self?.updateDisplay()
                try? await Task.sleep(for: .seconds(1))
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
            anchorTime = Date()
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
        guard let anchorEarthDate, let anchorTime else { return }
        let current = anchorEarthDate + rate * Date().timeIntervalSince(anchorTime)
        displayEarthDate = String(format: "%.4f", current)
    }
}
