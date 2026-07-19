import SwiftUI
import AgenticFlashcardsCore

@main
struct AgenticFlashcardsApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}

struct ContentView: View {
    @State private var showingAnswer = false
    private let card = Card(
        id: "synthetic", front: "Why keep an offline outbox?",
        back: "It preserves intent while the network is unavailable and makes retries explicit.",
        tags: ["systems"], dueOn: "2030-01-01", version: 1
    )

    var body: some View {
        VStack(spacing: 24) {
            Text(showingAnswer ? card.back : card.front).font(.title2)
            Button(showingAnswer ? "Next" : "Show answer") { showingAnswer.toggle() }
        }
        .padding()
    }
}
