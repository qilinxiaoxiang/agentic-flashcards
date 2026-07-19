import Foundation

public struct Card: Codable, Equatable, Identifiable, Sendable {
    public let id: String
    public var front: String
    public var back: String
    public var tags: [String]
    public var dueOn: String
    public var version: Int

    public init(id: String, front: String, back: String, tags: [String], dueOn: String, version: Int) {
        self.id = id
        self.front = front
        self.back = back
        self.tags = tags
        self.dueOn = dueOn
        self.version = version
    }
}

public struct PendingOperation: Codable, Equatable, Identifiable, Sendable {
    public let id: String
    public let cardID: String
    public let expectedVersion: Int
    public let kind: String
    public let payload: Data

    public init(id: String, cardID: String, expectedVersion: Int, kind: String, payload: Data) {
        self.id = id
        self.cardID = cardID
        self.expectedVersion = expectedVersion
        self.kind = kind
        self.payload = payload
    }
}

public struct CardConflict: Codable, Equatable, Sendable {
    public let operation: PendingOperation
    public let serverCard: Card

    public init(operation: PendingOperation, serverCard: Card) {
        self.operation = operation
        self.serverCard = serverCard
    }
}
