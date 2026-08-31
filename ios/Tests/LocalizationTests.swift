import XCTest
@testable import NEPPCore

final class LocalizationTests: XCTestCase {
    func testDefaultLocationAndExplicitOptOut() {
        let name = "NEPP-tests-" + UUID().uuidString
        let defaults = UserDefaults(suiteName: name)!
        defer { defaults.removePersistentDomain(forName: name) }
        XCTAssertTrue(NEPPDisplayPolicy.prefersCurrentLocation(defaults: defaults))
        defaults.set(false, forKey: "useCurrentSolarLocation")
        XCTAssertFalse(NEPPDisplayPolicy.prefersCurrentLocation(defaults: defaults))
        defaults.set(true, forKey: "useCurrentSolarLocation")
        XCTAssertTrue(NEPPDisplayPolicy.prefersCurrentLocation(defaults: defaults))
    }
    func testJapaneseAndEnglish() {
        XCTAssertEqual(NEPPLocalization.string("Settings", language: "ja"), "設定")
        XCTAssertEqual(NEPPLocalization.string("Settings", language: "en"), "Settings")
        XCTAssertEqual(NEPPLocalization.string("Current location", language: "ja"), "現在地")
        XCTAssertEqual(String(format: NEPPLocalization.string("Source: Stratum %d", language: "ja"), 1),
                       "接続先：Stratum 1")
    }
    func table(_ language: String, name: String = "Localizable") throws -> [String: String] {
        let path = try XCTUnwrap(NEPPLocalization.bundle.path(forResource: language, ofType: "lproj"))
        let data = try Data(contentsOf: URL(fileURLWithPath: path).appendingPathComponent(name + ".strings"))
        return try XCTUnwrap(PropertyListSerialization.propertyList(from: data, format: nil) as? [String: String])
    }
    func testTranslationKeysAndFormatArgumentsMatch() throws {
        let en = try table("en"), ja = try table("ja")
        XCTAssertEqual(Set(en.keys), Set(ja.keys))
        XCTAssertGreaterThan(en.count, 80)
        let format = try NSRegularExpression(pattern: "%([.][0-9]+)?[@duf]")
        func fields(_ s: String) -> [String] {
            format.matches(in: s, range: NSRange(s.startIndex..., in: s)).map {
                String(s[Range($0.range, in: s)!])
            }
        }
        for key in en.keys {
            XCTAssertFalse(ja[key]!.isEmpty, key)
            XCTAssertEqual(fields(en[key]!), fields(ja[key]!), key)
        }
        for language in ["en", "ja"] {
            let info = try table(language, name: "InfoPlist")
            XCTAssertNotNil(info["NSLocationWhenInUseUsageDescription"])
            XCTAssertNotNil(info["NSLocalNetworkUsageDescription"])
        }
    }
}
