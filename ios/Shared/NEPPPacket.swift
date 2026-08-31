import Foundation
import Security

enum NEPPLocalization {
    static let bundle: Bundle = {
        #if SWIFT_PACKAGE
        return .module
        #else
        return .main
        #endif
    }()
    static func string(_ key: String, language: String? = nil) -> String {
        let selected: Bundle
        if let language, let path = bundle.path(forResource: language, ofType: "lproj"),
           let localized = Bundle(path: path) { selected = localized }
        else { selected = bundle }
        return selected.localizedString(forKey: key, value: key, table: nil)
    }
}

func L(_ key: String) -> String { NEPPLocalization.string(key) }
func LF(_ key: String, _ arguments: CVarArg...) -> String {
    String(format: L(key), locale: Locale.current, arguments: arguments)
}

enum NEPPDisplayPolicy {
    static func prefersCurrentLocation(defaults: UserDefaults = .standard) -> Bool {
        guard defaults.object(forKey: "useCurrentSolarLocation") != nil else { return true }
        return defaults.bool(forKey: "useCurrentSolarLocation")
    }
    static func retryDelay(failures: Int) -> Double {
        guard failures > 0 else { return 60 }
        return [2, 4, 8, 16, 30, 60][min(failures - 1, 5)]
    }
    static func locationLabel(age: Double, failed: Bool) -> String {
        age >= 300 || failed ? L("Last known location") : L("Current location")
    }
    static func status(age: Double, validity: UInt32, failures: Int, holdover: Bool) -> String {
        if validity != .max && age > Double(validity) { return L("Stale · estimated") }
        if failures > 0 { return L("Reconnecting · estimated") }
        if holdover { return L("Source holdover · estimated") }
        return L("Live · estimated")
    }
}

struct EarthDate: Equatable, Sendable {
    let year: Int32
    let fraction: UInt64
    var value: Double { Double(year) + Double(fraction) / 0x1p64 }
    var isZero: Bool { year == 0 && fraction == 0 }
    func difference(from other: EarthDate) -> Double {
        // Subtract fractions before converting: avoid losing sub-millisecond
        // differences by first adding the large year component in Double.
        let delta = fraction >= other.fraction
            ? Double(fraction - other.fraction) : -Double(other.fraction - fraction)
        return Double(Int64(year) - Int64(other.year)) + delta / 0x1p64
    }
}

struct NEPPQuality: Sendable {
    static let unknown = UInt32.max
    let state: UInt8
    let source: UInt8
    let flags: UInt8
    let stratum: UInt8
    let reference: UInt32
    let uncertainty: UInt32
    let validity: UInt32
    let dataAge: UInt32
    let updateAge: UInt32
    var evaluated: Bool { flags & 1 != 0 }
    var prediction: UInt8 { (flags >> 1) & 3 }

    init(_ data: Data, at i: Int, solar: Bool) throws {
        state = data[i]; source = data[i+1]; flags = data[i+2]; stratum = data[i+3]
        reference = data.u32(i+4); uncertainty = data.u32(i+8)
        validity = data.u32(i+12); dataAge = data.u32(i+16); updateAge = data.u32(i+20)
        if state == 0 {
            guard data[i..<i+24].allSatisfy({ $0 == 0 }) else { throw NEPPError.invalidQuality }
            return
        }
        guard state <= 3, flags & 0xf8 == 0, prediction != 3,
              stratum <= 15, solar || stratum > 0,
              validity == Self.unknown || validity <= 3600 else { throw NEPPError.invalidQuality }
        if evaluated {
            guard uncertainty != Self.unknown, validity != Self.unknown,
                  !solar || uncertainty < 0x80000000 else { throw NEPPError.invalidQuality }
        } else if uncertainty != Self.unknown { throw NEPPError.invalidQuality }
    }

    func freshness(age: Double) -> String {
        if validity == Self.unknown { return L("Validity unknown · local estimate") }
        if age > Double(validity) { return L("Stale · local prediction") }
        if state == 2 { return L("Source holdover") }
        if state == 3 { return L("Supply state unknown") }
        return L("Live estimate")
    }
}

struct NEPPResponse: Sendable {
    static let basePacketSize = 160
    let status: UInt8
    let stratum: UInt8
    let receive: EarthDate
    let transmit: EarthDate
    let rate: Double
    let edQuality: NEPPQuality
    let phase: Double?
    let phaseRate: Double
    let spQuality: NEPPQuality?
    let solarIssue: String?

    static func bootstrapRequest() throws -> Data {
        var token = [UInt8](repeating: 0, count: 16)
        repeat {
            guard SecRandomCopyBytes(kSecRandomDefault, token.count, &token) == errSecSuccess
            else { throw NEPPError.randomFailure }
        } while token.allSatisfy({ $0 == 0 })
        var data = Data(repeating: 0, count: basePacketSize)
        data[0] = 0xd3; data[1] = 16; data[2] = 6
        data.replaceSubrange(76..<92, with: token)
        return data
    }

    static func matches(_ data: Data, request: Data) -> Bool {
        data.count == 160 && request.count == 160 &&
        data[76..<92] == request[76..<92] && data[28..<40] == request[52..<64]
    }

    static func decode(_ data: Data, request: Data) throws -> Self {
        guard data.count == 160 else { throw NEPPError.shortPacket }
        let version = (data[0] >> 3) & 7
        guard version == 2 else { throw NEPPError.unsupportedVersion(version) }
        guard matches(data, request: request) else { throw NEPPError.correlation }
        let status = data[0] >> 6, mode = data[0] & 7
        guard mode == 4 else { throw NEPPError.invalidMode(mode) }
        guard status != 3, (1...15).contains(data[1]) else { throw NEPPError.unsynchronized }
        let ed = try NEPPQuality(data, at: 112, solar: false)
        guard ed.state != 0, ed.stratum == data[1], ed.reference == data.u32(12),
              (ed.state == 1 && status <= 1) || (ed.state == 2 && status == 2) ||
              (ed.state == 3 && status == 1),
              ed.evaluated || data.u32(8) == UInt32.max else { throw NEPPError.invalidQuality }
        let receive = data.earthDate(40), transmit = data.earthDate(52)
        let rate = Double(Int64(bitPattern: data.u64(64))) / 0x1p63
        guard data.u32(72) == 1, rate > 0, !receive.isZero, !transmit.isZero
        else { throw NEPPError.invalidCoordinate }
        var sp: NEPPQuality?, phase: Double?, q = 0.0, issue: String?
        do {
            let quality = try NEPPQuality(data, at: 136, solar: true)
            if quality.state == 0 {
                guard data[92..<112].allSatisfy({ $0 == 0 }) else { throw NEPPError.invalidQuality }
                issue = L("Solar phase unavailable")
            } else {
                q = Double(Int64(bitPattern: data.u64(100))) / 0x1p63
                guard data.u32(108) == 1, q > 0 else { throw NEPPError.invalidCoordinate }
                sp = quality
                phase = min(Double(data.u64(92)) / 0x1p64, Double(1).nextDown)
            }
        } catch { issue = L("Invalid or unsupported solar state"); q = 0 }
        return Self(status: status, stratum: data[1], receive: receive, transmit: transmit,
                    rate: rate, edQuality: ed, phase: phase, phaseRate: q,
                    spQuality: sp, solarIssue: issue)
    }
}

struct NEPPSample: Sendable {
    let response: NEPPResponse
    let receivedUptime: Double
    let oneWayEstimate: Double
    // A bounded display policy, NOT a guaranteed age or accuracy bound.
    static let maximumDisplayAge = 300.0
    init(response: NEPPResponse, sent: Double, received: Double) throws {
        let total = received - sent
        let processing = response.transmit.difference(from: response.receive) / response.rate
        let path = total - processing
        // No negative-delay clamping with unassessed timestamps.
        guard total.isFinite, processing.isFinite, total >= 0, total <= 3,
              processing >= 0, path >= 0 else { throw NEPPError.inconsistentTiming }
        self.response = response; receivedUptime = received; oneWayEstimate = path / 2
    }
    func age(at uptime: Double) -> Double { uptime - receivedUptime + oneWayEstimate }
    func usable(at uptime: Double) -> Bool {
        uptime >= receivedUptime && age(at: uptime) <= Self.maximumDisplayAge
    }
    func earthDate(at uptime: Double) -> Double {
        response.transmit.value + response.rate * age(at: uptime)
    }
    func solarPhase(at uptime: Double, longitude: Double) -> Double? {
        guard let phase = response.phase, longitude.isFinite, (-180...180).contains(longitude)
        else { return nil }
        let value = phase + response.phaseRate * age(at: uptime) + longitude / 360
        return value - floor(value)
    }
}

enum NEPPError: LocalizedError, Equatable {
    case shortPacket, unsupportedVersion(UInt8), invalidMode(UInt8), unsynchronized
    case invalidPort, timeout, network(String), invalidQuality, invalidCoordinate
    case correlation, randomFailure, inconsistentTiming
    var errorDescription: String? {
        switch self {
        case .shortPacket: return L("Expected a 160-byte draft-03 V2 packet.")
        case let .unsupportedVersion(v): return LF("Unsupported NEPP version %d; V2 is required.", Int(v))
        case let .invalidMode(v): return LF("Unexpected NEPP mode %d.", Int(v))
        case .unsynchronized: return L("ED is unavailable from this server.")
        case .invalidPort: return L("The server port is invalid.")
        case .timeout: return L("No V2 response. The server may still be V1.")
        case let .network(message): return message
        case .invalidQuality: return L("Invalid coordinate quality information.")
        case .invalidCoordinate: return L("Invalid or unsupported coordinate model.")
        case .correlation: return L("Response does not match this request.")
        case .randomFailure: return L("Could not generate a secure request token.")
        case .inconsistentTiming: return L("Inconsistent or excessive exchange delay.")
        }
    }
}

private extension Data {
    func u32(_ i: Int) -> UInt32 { self[i..<i+4].reduce(0) { ($0 << 8) | UInt32($1) } }
    func u64(_ i: Int) -> UInt64 { self[i..<i+8].reduce(0) { ($0 << 8) | UInt64($1) } }
    func earthDate(_ i: Int) -> EarthDate {
        EarthDate(year: Int32(bitPattern: u32(i)), fraction: u64(i+4))
    }
}
