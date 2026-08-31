// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "NEPPCore",
    defaultLocalization: "en",
    platforms: [.iOS(.v17), .macOS(.v13)],
    products: [.library(name: "NEPPCore", targets: ["NEPPCore"])],
    targets: [
        .target(name: "NEPPCore", path: ".",
                exclude: ["NEPP", "NEPP.xcodeproj", "Tests", "README.md"],
                sources: ["Shared"], resources: [.process("Resources")]),
        .testTarget(name: "NEPPCoreTests", dependencies: ["NEPPCore"], path: "Tests")
    ]
)
