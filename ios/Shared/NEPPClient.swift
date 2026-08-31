import Foundation
import Network

struct NEPPClient: Sendable {
    func query(host: String, port: Int, timeout: Duration = .seconds(3)) async throws -> NEPPSample {
        guard let rawPort = UInt16(exactly: port), rawPort > 0,
              let networkPort = NWEndpoint.Port(rawValue: rawPort) else { throw NEPPError.invalidPort }
        return try await withThrowingTaskGroup(of: NEPPSample.self) { group in
            defer { group.cancelAll() }
            group.addTask { try await UDPQuery(host: host, port: networkPort).run() }
            group.addTask {
                try await Task.sleep(for: timeout)
                throw NEPPError.timeout
            }
            return try await group.next()!
        }
    }
}

// All mutable state is confined to queue. Cancellation works even before run's
// continuation is installed; one connected UDP endpoint and one consumed token.
private final class UDPQuery: @unchecked Sendable {
    private let connection: NWConnection
    private let queue = DispatchQueue(label: "jp.kenic.nepp.udp")
    private var continuation: CheckedContinuation<NEPPSample, Error>?
    private var cancelled = false
    private var finished = false
    private var sent = false
    private var request = Data()
    private var sentUptime = 0.0

    init(host: String, port: NWEndpoint.Port) {
        connection = NWConnection(host: NWEndpoint.Host(host), port: port, using: .udp)
    }
    func run() async throws -> NEPPSample {
        try await withTaskCancellationHandler {
            try await withCheckedThrowingContinuation { continuation in
                queue.async {
                    self.continuation = continuation
                    if self.cancelled { self.finish(.failure(CancellationError())); return }
                    self.connection.stateUpdateHandler = { state in
                        switch state {
                        case .ready: self.send()
                        case let .failed(error): self.finish(.failure(error))
                        case .cancelled: self.finish(.failure(CancellationError()))
                        default: break
                        }
                    }
                    self.connection.start(queue: self.queue)
                }
            }
        } onCancel: {
            self.queue.async {
                self.cancelled = true
                if self.continuation != nil { self.finish(.failure(CancellationError())) }
            }
        }
    }
    private func send() {
        guard !sent, !finished else { return }
        sent = true
        do { request = try NEPPResponse.bootstrapRequest() }
        catch { finish(.failure(error)); return }
        sentUptime = ProcessInfo.processInfo.systemUptime
        connection.send(content: request, completion: .contentProcessed { error in
            if let error { self.finish(.failure(error)) }
        })
        receive()
    }
    private func receive() {
        connection.receiveMessage { data, _, _, error in
            let received = ProcessInfo.processInfo.systemUptime
            guard !self.finished else { return }
            if let error { self.finish(.failure(error)); return }
            guard let data, NEPPResponse.matches(data, request: self.request) else {
                self.receive(); return // unrelated/malformed packets do not consume the request
            }
            do {
                let response = try NEPPResponse.decode(data, request: self.request)
                self.finish(.success(try NEPPSample(response: response,
                                                   sent: self.sentUptime, received: received)))
            } catch { self.finish(.failure(error)) }
        }
    }
    private func finish(_ result: Result<NEPPSample, Error>) {
        guard !finished, let continuation else { return }
        finished = true
        self.continuation = nil
        connection.stateUpdateHandler = nil
        connection.cancel()
        continuation.resume(with: result)
    }
}
