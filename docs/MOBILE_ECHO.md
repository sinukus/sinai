# Sin.AI native offline echo test

Standalone English (US) speech → editable transcript → system-voice playback.
No desktop server, Ollama, AI model, translation, or voice cloning is involved.
Android uses the on-device recognizer exclusively and an installed non-network TTS voice; no INTERNET permission is declared. iOS requires on-device recognition support before starting. Install needed system language/voice assets while online before testing in airplane mode.

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
