import Foundation
import Testing
@testable import AgenticFlashcardsCore

@Test func outboxPersistsAndReplaysInOrder() async throws {
    let file = FileManager.default.temporaryDirectory.appending(path: UUID().uuidString)
    let outbox = try OfflineOutbox(fileURL: file)
    let one = PendingOperation(id: "one", cardID: "card", expectedVersion: 1, kind: "review", payload: Data())
    let two = PendingOperation(id: "two", cardID: "card", expectedVersion: 2, kind: "edit", payload: Data())
    try await outbox.enqueue(one)
    try await outbox.enqueue(two)
    let recorder = Recorder()
    try await outbox.flush { operation in await recorder.append(operation.id) }
    #expect(await recorder.values == ["one", "two"])
    #expect(await outbox.pending().isEmpty)
}

actor Recorder {
    var values: [String] = []
    func append(_ value: String) { values.append(value) }
}
