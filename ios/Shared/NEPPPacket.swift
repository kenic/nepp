import Foundation

struct EarthDate: Equatable, Sendable {
    let year: Int32
    let fraction: UInt64

    var value: Double {
        Double(year) + Double(fraction) / 18_446_744_073_709_551_616.0
    }
}

struct NEPPResponse: Sendable {
    static let basePacketSize = 76

    let status: UInt8
    let version: UInt8
    let mode: UInt8
    let stratum: UInt8
    let transmit: EarthDate
    let rate: Double
    let modelID: UInt32

    static func bootstrapRequest() -> Data {
        var data = Data(repeating: 0, count: basePacketSize)
        data[0] = 0b1100_1011 // unsynchronized, Version 1, client
        data[1] = 16
        data[2] = 6
        data[3] = UInt8(bitPattern: -52)
        return data
    }

    static func decode(_ data: Data) throws -> NEPPResponse {
        guard data.count >= basePacketSize else { throw NEPPError.shortPacket }
        let flags = data[0]
        let status = flags >> 6
        let version = (flags >> 3) & 0x07
        let mode = flags & 0x07
        guard version == 1 else { throw NEPPError.unsupportedVersion(version) }
        guard mode == 4 else { throw NEPPError.invalidMode(mode) }
        guard status != 3, data[1] <= 15 else { throw NEPPError.unsynchronized }

        let year = Int32(bitPattern: data.readUInt32(at: 52))
        let fraction = data.readUInt64(at: 56)
        let rateBits = Int64(bitPattern: data.readUInt64(at: 64))
        return NEPPResponse(
            status: status,
            version: version,
            mode: mode,
            stratum: data[1],
            transmit: EarthDate(year: year, fraction: fraction),
            rate: Double(rateBits) / 9_223_372_036_854_775_808.0,
            modelID: data.readUInt32(at: 72)
        )
    }
}

enum NEPPError: LocalizedError, Equatable {
    case shortPacket
    case unsupportedVersion(UInt8)
    case invalidMode(UInt8)
    case unsynchronized
    case invalidPort
    case timeout
    case network(String)

    var errorDescription: String? {
        switch self {
        case .shortPacket: return "The server returned a short packet."
        case let .unsupportedVersion(value): return "Unsupported NEPP version \(value)."
        case let .invalidMode(value): return "Unexpected NEPP mode \(value)."
        case .unsynchronized: return "The NEPP server is not synchronized."
        case .invalidPort: return "The server port is invalid."
        case .timeout: return "The NEPP server did not respond."
        case let .network(message): return message
        }
    }
}

private extension Data {
    func readUInt32(at offset: Int) -> UInt32 {
        self[offset..<offset + 4].reduce(0) { ($0 << 8) | UInt32($1) }
    }

    func readUInt64(at offset: Int) -> UInt64 {
        self[offset..<offset + 8].reduce(0) { ($0 << 8) | UInt64($1) }
    }
}
