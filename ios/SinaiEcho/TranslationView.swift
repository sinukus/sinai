import SwiftUI
import Translation

@available(iOS 18.0, *)
struct LocalTranslationView: View {
    struct Entry: Decodable, Identifiable { let id: String; let english: String }
    struct Resources: Decodable { let language_entries: [Entry] }
    @State var source: String
    @State private var translated = ""
    @State private var status = "Prepare the English/Japanese models while online, then test in airplane mode."
    @State private var configuration: TranslationSession.Configuration?
    @State private var preparing = false
    @State private var busy = false
    @State private var selection = ""
    @Environment(\.dismiss) private var dismiss
    private let entries: [Entry] = {
        guard let url = Bundle.main.url(forResource: "travel-resources", withExtension: "json"), let data = try? Data(contentsOf: url), let resources = try? JSONDecoder().decode(Resources.self, from: data) else { return [] }
        return resources.language_entries
    }()
    private func run(prepare: Bool) {
        preparing = prepare; busy = true; translated = ""
        status = prepare ? "Preparing translation models…" : "Translating on device…"
        if configuration != nil { configuration?.invalidate() }
        else { configuration = TranslationSession.Configuration(source: Locale.Language(identifier: "en"), target: Locale.Language(identifier: "ja")) }
    }
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 18) {
                    Text(status)
                    TextEditor(text: $source).frame(height: 150).border(.secondary)
                    Picker("Template entry", selection: $selection) {
                        Text("Choose an entry").tag("")
                        ForEach(entries) { entry in Text(entry.id + " · " + entry.english).tag(entry.id) }
                    }.disabled(busy)
                    Button("Prepare models (online)") { run(prepare: true) }.disabled(busy)
                    Button("Translate locally") { run(prepare: false) }.disabled(busy || source.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                    Text(translated).font(.title2).textSelection(.enabled)
                    Text("Machine translation is unverified. Confirm critical allergy or medical wording with a person.").font(.footnote)
                }.padding()
            }.navigationTitle("English → Japanese")
             .toolbar { Button("Close") { dismiss() } }
             .onChange(of: selection) { _, id in if let entry = entries.first(where: { $0.id == id }) { source = entry.english; translated = "" } }
             .translationTask(configuration) { session in
                 do {
                     if preparing { try await session.prepareTranslation(); status = "Models prepared. Test in airplane mode to verify offline operation." }
                     else { let response = try await session.translate(source); translated = response.targetText; status = "Translated on device; output has not been reviewed." }
                 } catch { status = "Translation unavailable: \(error.localizedDescription)" }
                 busy = false
             }
        }
    }
}
