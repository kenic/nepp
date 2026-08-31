import XCTest
@testable import NEPPCore

final class NEPPPacketTests: XCTestCase {
    func testRetryBackoffAndRecovery() {
        XCTAssertEqual((0...8).map { NEPPDisplayPolicy.retryDelay(failures: $0) },
                       [60, 2, 4, 8, 16, 30, 60, 60, 60])
        XCTAssertEqual(NEPPDisplayPolicy.status(age: 1, validity: 200, failures: 1, holdover: false),
                       L("Reconnecting · estimated"))
        XCTAssertEqual(NEPPDisplayPolicy.status(age: 1, validity: 200, failures: 0, holdover: false),
                       L("Live · estimated"))
    }
    func testStationaryLocationBecomesLastKnownNotGreenwich() {
        XCTAssertEqual(NEPPDisplayPolicy.locationLabel(age: 299, failed: false), L("Current location"))
        XCTAssertEqual(NEPPDisplayPolicy.locationLabel(age: 300, failed: false), L("Last known location"))
        XCTAssertEqual(NEPPDisplayPolicy.locationLabel(age: 3600, failed: false), L("Last known location"))
        XCTAssertEqual(NEPPDisplayPolicy.locationLabel(age: 10, failed: true), L("Last known location"))
    }
    func testStalenessIsNotHiddenByReconnecting() {
        XCTAssertEqual(NEPPDisplayPolicy.status(age: 201, validity: 200, failures: 2, holdover: false),
                       L("Stale · estimated"))
        XCTAssertEqual(NEPPDisplayPolicy.status(age: 201, validity: .max, failures: 2, holdover: false),
                       L("Reconnecting · estimated"))
    }
    // Python draft-03 build_response fixture: E2 at 101, E3 at 101.01,
    // source anchor 100, ED=2026.4, SP=.99999, token=16 ASCII x bytes.
    let hex = "140106d8ffffffffffffffff0000007b000007ea6666666666666666000000000000000000000000000007ea666666efd6c5a79c000007ea666666f1369da5b400000044b82fa09b000000017878787878787878787878787878787800001c59b309a534000061172283394500000001010100010000007bffffffff0000012affffffff00000002010100010000007bffffffff0000012affffffff00000002"
    func fixture() -> Data {
        let chars = Array(hex)
        return Data(stride(from: 0, to: chars.count, by: 2).map {
            UInt8(String(chars[$0..<$0+2]), radix: 16)!
        })
    }
    func request() throws -> Data {
        var data = try NEPPResponse.bootstrapRequest()
        data.replaceSubrange(76..<92, with: repeatElement(UInt8(120), count: 16))
        return data
    }
    func testBootstrapRequestLayoutAndFreshToken() throws {
        let data = try NEPPResponse.bootstrapRequest()
        XCTAssertEqual(data.count, 160)
        XCTAssertEqual(Array(data.prefix(4)), [0xd3, 16, 6, 0])
        XCTAssertTrue(data[4..<76].allSatisfy { $0 == 0 })
        XCTAssertTrue(data[92..<160].allSatisfy { $0 == 0 })
        XCTAssertTrue(data[76..<92].contains { $0 != 0 })
        XCTAssertNotEqual(data[76..<92], try NEPPResponse.bootstrapRequest()[76..<92])
    }
    func testPythonInteroperability() throws {
        let r = try NEPPResponse.decode(fixture(), request: request())
        XCTAssertEqual(r.transmit.value, 2026.40000003232, accuracy: 1e-12)
        XCTAssertEqual(r.transmit.difference(from: r.receive) / r.rate, 0.01, accuracy: 1e-8)
        XCTAssertNotNil(r.phase)
        XCTAssertFalse(r.edQuality.evaluated)
        XCTAssertEqual(r.edQuality.validity, 298)
        let s = try NEPPSample(response: r, sent: 10, received: 10.11)
        XCTAssertEqual(s.oneWayEstimate, 0.05, accuracy: 1e-8)
        XCTAssertEqual(s.earthDate(at: 11), r.transmit.value + r.rate * 0.94, accuracy: 1e-12)
        XCTAssertEqual(s.solarPhase(at: 10.11, longitude: 180)!,
                       s.solarPhase(at: 10.11, longitude: -180)!, accuracy: 1e-12)
        XCTAssertTrue((0..<1).contains(s.solarPhase(at: 11, longitude: -139)!))
        XCTAssertFalse(s.usable(at: 9))
        XCTAssertFalse(s.usable(at: 400))
    }
    func testRejectsWrongLengthsVersionsTokensOrigins() throws {
        for size in [0, 76, 128, 159, 161] {
            XCTAssertThrowsError(try NEPPResponse.decode(Data(repeating: 0, count: size), request: request()))
        }
        for offset in [0, 28, 76] {
            var data = fixture(); data[offset] ^= 8
            XCTAssertThrowsError(try NEPPResponse.decode(data, request: request()))
        }
    }
    func testRejectsInvalidEDQuality() throws {
        for offset in [1, 8, 72, 112, 114, 115, 116, 120, 124] {
            var data = fixture(); data[offset] ^= 128
            XCTAssertThrowsError(try NEPPResponse.decode(data, request: request()), "offset \(offset)")
        }
    }
    func testInvalidSPRetainsED() throws {
        var data = fixture(); data[138] = 128
        let r = try NEPPResponse.decode(data, request: request())
        XCTAssertNil(r.phase); XCTAssertNotNil(r.solarIssue)
        XCTAssertEqual(r.stratum, 1)
    }
    func testUnavailableSPAndMidnight() throws {
        var data = fixture()
        data.replaceSubrange(92..<112, with: repeatElement(UInt8(0), count: 20))
        data.replaceSubrange(136..<160, with: repeatElement(UInt8(0), count: 24))
        XCTAssertNil(try NEPPResponse.decode(data, request: request()).phase)
        data = fixture()
        data.replaceSubrange(92..<100, with: repeatElement(UInt8(0), count: 8))
        XCTAssertEqual(try NEPPResponse.decode(data, request: request()).phase, 0)
    }
    func testTimingPolicyAndExpiry() throws {
        let r = try NEPPResponse.decode(fixture(), request: request())
        XCTAssertThrowsError(try NEPPSample(response: r, sent: 1, received: 1.001))
        XCTAssertThrowsError(try NEPPSample(response: r, sent: 1, received: 5))
        XCTAssertEqual(r.edQuality.freshness(age: 299), L("Stale · local prediction"))
        var data = fixture()
        data.replaceSubrange(124..<128, with: [255, 255, 255, 255])
        XCTAssertEqual(try NEPPResponse.decode(data, request: request()).edQuality.freshness(age: 1), L("Validity unknown · local estimate"))
    }
    func testCancellationBeforeQueryDoesNotHang() async {
        let task = Task { try await NEPPClient().query(host: "127.0.0.1", port: 9) }
        task.cancel()
        do { _ = try await task.value; XCTFail("cancelled request completed") } catch { }
    }
    func testBoundedTimeout() async throws {
        guard let port = ProcessInfo.processInfo.environment["NEPP_SILENT_PORT"].flatMap(Int.init)
        else { throw XCTSkip("Run tests/run_swift_interop.py for silent-endpoint timeout") }
        do {
            _ = try await NEPPClient().query(host: "127.0.0.1", port: port, timeout: .milliseconds(100))
            XCTFail("silent server responded")
        } catch { XCTAssertEqual(error as? NEPPError, .timeout) }
    }
    func testEarthDateDifferenceAtYearBoundary() {
        let before = EarthDate(year: 2025, fraction: UInt64.max)
        let after = EarthDate(year: 2026, fraction: 0)
        // The wire has more precision than a Double across a whole-turn wrap;
        // the result must at least remain nonnegative, never a one-year jump.
        XCTAssertEqual(after.difference(from: before), 0, accuracy: 1e-15)
    }
    func testOptionalLocalPythonServer() async throws {
        guard let port = ProcessInfo.processInfo.environment["NEPP_TEST_PORT"].flatMap(Int.init)
        else { throw XCTSkip("Set NEPP_TEST_PORT for live Python V2 interop") }
        let sample = try await NEPPClient().query(host: "127.0.0.1", port: port)
        XCTAssertEqual(sample.response.stratum, 1)
        XCTAssertFalse(sample.response.edQuality.evaluated)
        XCTAssertNotNil(sample.response.phase)
        XCTAssertEqual(sample.response.transmit.value, 2020.25, accuracy: 0.002)
    }
}
