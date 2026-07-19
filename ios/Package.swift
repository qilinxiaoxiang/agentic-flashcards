// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "AgenticFlashcardsCore",
    platforms: [.iOS(.v17), .macOS(.v14)],
    products: [.library(name: "AgenticFlashcardsCore", targets: ["AgenticFlashcardsCore"])],
    targets: [
        .target(name: "AgenticFlashcardsCore"),
        .testTarget(name: "AgenticFlashcardsCoreTests", dependencies: ["AgenticFlashcardsCore"]),
    ]
)
