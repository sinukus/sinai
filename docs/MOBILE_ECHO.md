# Sin.AI native offline echo test

Standalone English (US) speech → editable transcript → system-voice playback.
No desktop server, Ollama, conversational AI model, or voice cloning is involved.
Android uses the on-device recognizer exclusively and an installed non-network TTS voice; network permission is included for explicit translation-model preparation. iOS requires on-device recognition support before starting. Install needed system language/voice assets while online before testing in airplane mode.

## Android APK

Open repository Actions → Mobile echo builds → latest successful run on `travel-local-first` → artifact `sinai-echo-android-apk`. Download/unzip and open `app-debug.apk` on Pixel. Allow installation from that download app when prompted. Grant microphone permission. Switch to airplane mode with Wi-Fi off. Record a short English sentence, Finish recording, edit if needed, Read aloud.

Local build with JDK 17, Android SDK 35 and Gradle 8.9: `gradle -p android assembleDebug lintDebug`.
Output: `android/app/build/outputs/apk/debug/app-debug.apk`.
Debug APK is for private testing. CI debug signing keys may change between runs, so later builds may require uninstalling the prior test app.

## iPad / iOS

The iOS CI job compiles for the simulator; it does NOT produce an installable iPad IPA. Download `sinai-echo-ios-source` or clone this branch, then on a Mac with Xcode and XcodeGen run `cd ios && xcodegen generate`. Open `SinaiEcho.xcodeproj`, select your Apple development team under Signing & Capabilities, choose the connected iPad, and Run.

For installation directly on iPad through TestFlight, an Apple Developer membership, App Store Connect app entry, and signed distribution build uploaded to TestFlight are required. No TestFlight build or invitation exists yet. Unsigned simulator output cannot be installed on iPad.

## Acceptance

Both apps must transcribe and play back a short sentence with airplane mode enabled and Wi-Fi disabled. Denied microphone permissions, absent offline recognition, absent voice data, Stop audio, leaving the app, and a second recording must behave clearly. Native compilation, installation and actual device offline behavior are separate validation stages. Do not treat source inspection or passing backend tests as proof of mobile operation.

## Native template integration

Both apps now bundle the existing travel template, the full 180-entry English language template, and JP/VN destination metadata. Open Travel and language resources to read templates offline and select a destination; the destination selection is saved locally. Bundles are identical on both platforms. These are source-language entries, not translated language packs. Model routing, AI Court, conversation memory, translation engines, and target-language speech selection remain unconnected.

## On-device translation

Translate transcript / template opens English-to-Japanese translation and allows selecting any of the 180 template entries. Android uses ML Kit 17.0.3, with explicit Wi-Fi model preparation and installed-model checks before translating. iOS 18+ uses Apple Translation with system-managed model preparation/download consent. Models must be prepared online before airplane-mode testing. Translation output is machine-generated and not a reviewed language pack. No API key or developer account is required for these translation engines. AI Court/model routing remains unconnected.

## Pronunciation and mnemonics — all target languages

The learning entry contract is `mobile/learning-entry.schema.json`: native-script text, standard romanization where applicable, IPA, English-friendly phonetic respelling, tone/stress/vowel-length notes, and a mnemonic. This applies to every target language, not only Japanese. Keep regional pronunciation distinctions. Romanization alone is not sufficient pronunciation guidance. Mnemonics are memory aids, not factual etymologies.

Translation engine output does not populate these fields reliably. Store unavailable fields as missing rather than inventing pronunciation. Reviewed offline learning packs or a separately validated generation pipeline are still needed. This commit defines the contract; it does not claim the pronunciation/mnemonic pipeline is implemented.

Target selection: Android lists ML Kit's supported target languages; iOS offers a selection of common travel languages, with actual availability determined by Apple on the device. Input remains English in this iteration. Pronunciation helper words are optional and deferred; readable phonetics remain planned.
