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
            Spacer()
        }.padding()
        .onChange(of: phase) { _, state in if state != .active { echo.cancel() } }
    }
}
