import XCTest
@testable import NEPPCore

final class NEPPPacketTests: XCTestCase {
    func testBootstrapRequestLayout() {
        let data = NEPPResponse.bootstrapRequest()
        XCTAssertEqual(data.count, 76)
        XCTAssertEqual(data[0], 0b1100_1011)
        XCTAssertEqual(data[1], 16)
        XCTAssertEqual(data[2], 6)
        XCTAssertEqual(data[3], 204)
    }

    func testDecodesPythonCompatibleResponse() throws {
        var data = Data(repeating: 0, count: 76)
        data[0] = 0b0000_1100
        data[1] = 1
        data.replaceSubrange(52..<56, with: [0, 0, 7, 234]) // 2026
        data.replaceSubrange(56..<64, with: [0x80, 0, 0, 0, 0, 0, 0, 0])
        data.replaceSubrange(72..<76, with: [0, 0, 0, 1])
        let response = try NEPPResponse.decode(data)
        XCTAssertEqual(response.transmit.year, 2026)
        XCTAssertEqual(response.transmit.value, 2026.5, accuracy: 1e-12)
        XCTAssertEqual(response.modelID, 1)
    }

    func testRejectsShortPacket() {
        XCTAssertThrowsError(try NEPPResponse.decode(Data(repeating: 0, count: 75)))
    }
}
