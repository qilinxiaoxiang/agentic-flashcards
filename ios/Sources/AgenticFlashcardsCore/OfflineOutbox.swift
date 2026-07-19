import Foundation

public actor OfflineOutbox {
    public typealias Sender = @Sendable (PendingOperation) async throws -> Void
    private var operations: [PendingOperation]
    private let fileURL: URL

    public init(fileURL: URL) throws {
        self.fileURL = fileURL
        if FileManager.default.fileExists(atPath: fileURL.path) {
            operations = try JSONDecoder().decode([PendingOperation].self, from: Data(contentsOf: fileURL))
        } else {
            operations = []
        }
    }

    public func enqueue(_ operation: PendingOperation) throws {
        guard !operations.contains(where: { $0.id == operation.id }) else { return }
        operations.append(operation)
        try persist()
    }

    public func pending() -> [PendingOperation] { operations }

    public func flush(send: Sender) async throws {
        while let first = operations.first {
            try await send(first)
            operations.removeFirst()
            try persist()
        }
    }

    private func persist() throws {
        try FileManager.default.createDirectory(
            at: fileURL.deletingLastPathComponent(), withIntermediateDirectories: true
        )
        try JSONEncoder().encode(operations).write(to: fileURL, options: .atomic)
    }
}
