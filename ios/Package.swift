// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "NEPPCore",
    platforms: [.iOS(.v17), .macOS(.v13)],
    products: [.library(name: "NEPPCore", targets: ["NEPPCore"])],
    targets: [
        .target(name: "NEPPCore", path: "Shared"),
        .testTarget(name: "NEPPCoreTests", dependencies: ["NEPPCore"], path: "Tests")
    ]
)
