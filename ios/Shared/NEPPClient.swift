import Foundation
import Network

struct NEPPClient: Sendable {
    func query(host: String, port: Int, timeout: Duration = .seconds(3)) async throws -> NEPPResponse {
        guard let rawPort = UInt16(exactly: port), rawPort > 0,
              let networkPort = NWEndpoint.Port(rawValue: rawPort)
        else { throw NEPPError.invalidPort }

        return try await withThrowingTaskGroup(of: NEPPResponse.self) { group in
            group.addTask {
                let data = try await UDPQuery(host: host, port: networkPort).run()
                return try NEPPResponse.decode(data)
            }
            group.addTask {
                try await Task.sleep(for: timeout)
                throw NEPPError.timeout
            }
            let result = try await group.next()!
            group.cancelAll()
            return result
        }
    }
}

private final class UDPQuery: @unchecked Sendable {
    private let connection: NWConnection
    private let lock = NSLock()
    private var finished = false

    init(host: String, port: NWEndpoint.Port) {
        connection = NWConnection(host: NWEndpoint.Host(host), port: port, using: .udp)
    }

    func run() async throws -> Data {
        try await withTaskCancellationHandler {
            try await withCheckedThrowingContinuation { continuation in
                connection.stateUpdateHandler = { [weak self] state in
                    guard let self else { return }
                    switch state {
                    case .ready:
                        self.connection.send(content: NEPPResponse.bootstrapRequest(),
                                             completion: .contentProcessed { error in
                            if let error { self.finish(.failure(.network(error.localizedDescription)), continuation) }
                        })
                        self.connection.receiveMessage { data, _, _, error in
                            if let data {
                                self.finish(.success(data), continuation)
                            } else {
                                self.finish(.failure(.network(error?.localizedDescription ?? "Empty UDP response.")), continuation)
                            }
                        }
                    case let .failed(error):
                        self.finish(.failure(.network(error.localizedDescription)), continuation)
                    case .cancelled:
                        self.finish(.failure(.timeout), continuation)
                    default:
                        break
                    }
                }
                connection.start(queue: DispatchQueue(label: "org.nepp.udp"))
            }
        } onCancel: {
            connection.cancel()
        }
    }

    private func finish(_ result: Result<Data, NEPPError>,
                        _ continuation: CheckedContinuation<Data, Error>) {
        lock.lock()
        guard !finished else { lock.unlock(); return }
        finished = true
        lock.unlock()
        connection.cancel()
        continuation.resume(with: result.mapError { $0 as Error })
    }
}
