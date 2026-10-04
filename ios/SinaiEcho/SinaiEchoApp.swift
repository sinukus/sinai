import SwiftUI
import Speech
import AVFoundation

@main
struct SinaiEchoApp: App {
    var body: some Scene { WindowGroup { EchoView() } }
}

@MainActor
final class EchoController: ObservableObject {
    @Published var transcript = ""
    @Published var status = "English (US). Enable airplane mode for the offline test."
    @Published var listening = false
    private let engine = AVAudioEngine()
    private let speaker = AVSpeechSynthesizer()
    private let recognizer = SFSpeechRecognizer(locale: Locale(identifier: "en-US"))
    private var request: SFSpeechAudioBufferRecognitionRequest?
    private var task: SFSpeechRecognitionTask?
    private var tapped = false
    private var generation = 0

    func start() async {
        guard !listening else { return }
        let authorized = await withCheckedContinuation { continuation in
            SFSpeechRecognizer.requestAuthorization { continuation.resume(returning: $0 == .authorized) }
        }
        let microphone = await withCheckedContinuation { continuation in
            AVAudioSession.sharedInstance().requestRecordPermission { continuation.resume(returning: $0) }
        }
        guard authorized && microphone else { status = "Microphone and speech permissions are required."; return }
        guard let recognizer, recognizer.supportsOnDeviceRecognition else {
            status = "On-device English recognition is unavailable. No cloud fallback is used."; return
        }
        cancel()
        generation += 1
        let current = generation
        speaker.stopSpeaking(at: .immediate)
        do {
            let session = AVAudioSession.sharedInstance()
            try session.setCategory(.playAndRecord, mode: .default, options: [.defaultToSpeaker])
            try session.setActive(true)
            let input = engine.inputNode
            let format = input.outputFormat(forBus: 0)
            guard format.sampleRate > 0, format.channelCount > 0 else { status = "Microphone format unavailable."; return }
            let buffer = SFSpeechAudioBufferRecognitionRequest()
            buffer.requiresOnDeviceRecognition = true
            buffer.shouldReportPartialResults = true
            request = buffer
            input.installTap(onBus: 0, bufferSize: 1024, format: format) { audio, _ in buffer.append(audio) }
            tapped = true
            task = recognizer.recognitionTask(with: buffer) { [weak self] result, error in
                Task { @MainActor in
                    guard let self, self.generation == current else { return }
                    if let result { self.transcript = result.bestTranscription.formattedString }
                    if error != nil || result?.isFinal == true {
                        self.finish()
                        self.status = error == nil ? "Transcript ready. Tap Read aloud." : "Local recognition ended with an error: \(error!.localizedDescription)"
                        self.task = nil
                    }
                }
            }
            engine.prepare()
            try engine.start()
            listening = true
            status = "Listening locally…"
        } catch { cancel(); status = error.localizedDescription }
    }
    func finish() {
        engine.stop()
        if tapped { engine.inputNode.removeTap(onBus: 0); tapped = false }
        request?.endAudio(); request = nil
        listening = false
    }
    func cancel() { generation += 1; finish(); task?.cancel(); task = nil; speaker.stopSpeaking(at: .immediate) }
    func speak() {
        guard !listening, !transcript.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return }
        guard let voice = AVSpeechSynthesisVoice(language: "en-US") else { status = "Install an English system voice first."; return }
        do {
            try AVAudioSession.sharedInstance().setCategory(.playback, mode: .default)
            try AVAudioSession.sharedInstance().setActive(true)
            let utterance = AVSpeechUtterance(string: transcript); utterance.voice = voice
            speaker.speak(utterance)
        } catch { status = error.localizedDescription }
    }
    func stopAudio() { speaker.stopSpeaking(at: .immediate) }
}

struct EchoView: View {
    @StateObject private var echo = EchoController()
    @State private var starting = false
    @State private var showingResources = false
    @Environment(\.scenePhase) private var phase
    var body: some View {
        VStack(alignment: .leading, spacing: 18) {
            Text("Sin.AI · Offline echo").font(.title)
            Text(echo.status)
            TextEditor(text: $echo.transcript).frame(minHeight: 180).border(.secondary)
            Button("Record") { starting = true; Task { await echo.start(); starting = false } }.disabled(starting || echo.listening)
            Button("Finish recording") { echo.finish() }.disabled(!echo.listening)
            Button("Read aloud") { echo.speak() }.disabled(echo.listening)
            Button("Stop audio") { echo.stopAudio() }
            Button("Travel and language resources") { showingResources = true }
            Spacer()
        }.padding()
        .sheet(isPresented: $showingResources) { ResourceView() }
        .onChange(of: phase) { _, state in if state != .active { echo.cancel() } }
    }
}

struct TravelResources: Decodable {
    struct Pack: Decodable, Identifiable {
        let code: String
        let country: String
        let locales: [String]
        var id: String { code }
    }
    let language_template: String
    let travel_template: String
    let packs: [Pack]
}
struct ResourceView: View {
    @AppStorage("destination") private var destination = ""
    @Environment(\.dismiss) private var dismiss
    private let resources: TravelResources? = {
        guard let url = Bundle.main.url(forResource: "travel-resources", withExtension: "json"),
              let data = try? Data(contentsOf: url) else { return nil }
        return try? JSONDecoder().decode(TravelResources.self, from: data)
    }()
    var body: some View {
        NavigationStack {
            List {
                if let resources {
                    Section("Destination · saved on device") {
                        ForEach(resources.packs) { pack in
                            Button(pack.country + (destination == pack.code ? " ✓" : "")) { destination = pack.code }
                        }
                        Text("Translation and target-language speech assets are not connected yet.")
                    }
                    NavigationLink("Travel template") { ScrollView { Text(resources.travel_template).textSelection(.enabled).padding() } }
                    NavigationLink("Language template · 180 English entries") { ScrollView { Text(resources.language_template).textSelection(.enabled).padding() } }
                } else { Text("Bundled resources could not be loaded.") }
            }.navigationTitle("Offline resources")
             .toolbar { Button("Close") { dismiss() } }
        }
    }
}
