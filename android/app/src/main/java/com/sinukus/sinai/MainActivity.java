package com.sinukus.sinai;

import android.Manifest;
import android.app.Activity;
import android.app.AlertDialog;
import org.json.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.speech.*;
import android.speech.tts.*;
import android.view.View;
import android.widget.*;
import java.util.*;

public class MainActivity extends Activity implements RecognitionListener {
 private SpeechRecognizer recognizer;
 private TextToSpeech tts;
 private EditText transcript;
 private TextView status;
 private Button record;
 private boolean ready, listening;
 private final Locale language = Locale.US;
 @Override public void onCreate(Bundle state) {
  super.onCreate(state);
  LinearLayout layout = new LinearLayout(this); layout.setOrientation(LinearLayout.VERTICAL); layout.setPadding(32,48,32,32);
  TextView title = new TextView(this); title.setText("Sin.AI · Offline echo · English (US)"); title.setTextSize(22); layout.addView(title);
  status = new TextView(this); status.setText("Initializing local speech…"); layout.addView(status);
  transcript = new EditText(this); transcript.setHint("Your words appear here. You can edit them."); transcript.setMinLines(4); layout.addView(transcript);
  record = button(layout,"Record", v -> start());
  button(layout,"Finish recording",v -> { if(recognizer != null && listening) recognizer.stopListening(); });
  button(layout,"Read aloud",v -> speak());
  button(layout,"Stop audio",v -> { if(tts != null) tts.stop(); });
  button(layout,"Travel and language resources", v -> resources());
  setContentView(layout);
  if(state != null) transcript.setText(state.getString("transcript", ""));
  tts = new TextToSpeech(this, code -> {
   if(code != TextToSpeech.SUCCESS) { status.setText("Local speech playback initialization failed."); return; }
   Set<Voice> voices = tts.getVoices();
   if(voices != null) for(Voice voice: voices) {
    if(!voice.isNetworkConnectionRequired() && voice.getLocale().getLanguage().equals(language.getLanguage()) && !voice.getFeatures().contains(TextToSpeech.Engine.KEY_FEATURE_NOT_INSTALLED)) {
     if(tts.setVoice(voice) == TextToSpeech.SUCCESS) { ready = true; break; }
    }
   }
   status.setText(ready ? "Ready. Use airplane mode to verify offline operation." : "No installed offline English voice. Install a voice in Android text-to-speech settings first.");
  });
 }
 private void resources() {
  try (InputStream stream = getAssets().open("travel-resources.json")) {
   ByteArrayOutputStream bytes = new ByteArrayOutputStream(); byte[] buffer = new byte[4096]; int n;
   while((n=stream.read(buffer))!=-1) bytes.write(buffer,0,n);
   JSONObject data = new JSONObject(new String(bytes.toByteArray(), StandardCharsets.UTF_8));
   JSONArray packs=data.getJSONArray("packs");
   String[] choices=new String[packs.length()+2]; choices[0]="Travel template"; choices[1]="Language template (180 English entries)";
   for(int i=0;i<packs.length();i++) choices[i+2]=packs.getJSONObject(i).getString("country");
   new AlertDialog.Builder(this).setTitle("Offline resources").setItems(choices,(dialog,index)-> {
    try {
     if(index<2) showResource(choices[index], data.getString(index==0?"travel_template":"language_template"));
     else {
      JSONObject pack=packs.getJSONObject(index-2);
      getPreferences(MODE_PRIVATE).edit().putString("destination",pack.getString("code")).apply();
      showResource(pack.getString("country"), "Selected destination saved on device.\nTranslation and target-language speech assets are not connected yet.\n\n"+pack.toString(2));
     }
    } catch(JSONException e) { status.setText("Invalid resource: "+e.getMessage()); }
   }).show();
  } catch(Exception e) { status.setText("Could not load bundled resources: "+e.getMessage()); }
 }
 private void showResource(String title,String text) {
  ScrollView scroll=new ScrollView(this); TextView body=new TextView(this); body.setText(text); body.setPadding(24,24,24,24); body.setTextIsSelectable(true); scroll.addView(body);
  new AlertDialog.Builder(this).setTitle(title).setView(scroll).setPositiveButton("Close",null).show();
 }
 private Button button(LinearLayout parent,String label,View.OnClickListener action) { Button b=new Button(this); b.setText(label); b.setOnClickListener(action); parent.addView(b); return b; }
 private void start() {
  if(listening) return;
  if(checkSelfPermission(Manifest.permission.RECORD_AUDIO)!=PackageManager.PERMISSION_GRANTED) { requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO},1); return; }
  if(!SpeechRecognizer.isOnDeviceRecognitionAvailable(this)) { status.setText("On-device speech recognition is unavailable. No cloud fallback is used."); return; }
  tts.stop();
  if(recognizer != null) recognizer.destroy();
  recognizer=SpeechRecognizer.createOnDeviceSpeechRecognizer(this); recognizer.setRecognitionListener(this);
  Intent request=new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
  request.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL,RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
  request.putExtra(RecognizerIntent.EXTRA_LANGUAGE,language.toLanguageTag()); request.putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS,true);
  request.putExtra(RecognizerIntent.EXTRA_PREFER_OFFLINE,true);
  listening=true; record.setEnabled(false); status.setText("Listening locally…"); recognizer.startListening(request);
 }
 private void speak() { if(!ready) { status.setText("Offline playback voice is unavailable."); return; } if(listening) { status.setText("Finish recording before playback."); return; } String text=transcript.getText().toString().trim(); if(!text.isEmpty() && tts.speak(text,TextToSpeech.QUEUE_FLUSH,null,"echo")==TextToSpeech.ERROR) status.setText("Playback failed."); }
 private void update(Bundle result) { ArrayList<String> words=result.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION); if(words!=null && !words.isEmpty()) transcript.setText(words.get(0)); }
 public void onResults(Bundle result) { listening=false; record.setEnabled(true); update(result); status.setText("Transcript ready. Tap Read aloud."); }
 public void onPartialResults(Bundle result) { update(result); }
 public void onError(int error) { listening=false; record.setEnabled(true); status.setText("Local recognition failed ("+error+"). Confirm the English speech pack is installed."); }
 public void onReadyForSpeech(Bundle b) {} public void onBeginningOfSpeech() {} public void onRmsChanged(float r) {} public void onBufferReceived(byte[] b) {} public void onEndOfSpeech() {} public void onEvent(int e,Bundle b) {}
 @Override public void onRequestPermissionsResult(int r,String[] p,int[] g) { super.onRequestPermissionsResult(r,p,g); if(r==1 && g.length>0 && g[0]==PackageManager.PERMISSION_GRANTED) start(); else status.setText("Microphone permission is required to record."); }
 @Override protected void onSaveInstanceState(Bundle b) { b.putString("transcript",transcript.getText().toString()); super.onSaveInstanceState(b); }
 @Override protected void onStop() { super.onStop(); if(recognizer!=null) recognizer.cancel(); listening=false; record.setEnabled(true); if(tts!=null) tts.stop(); }
 @Override protected void onDestroy() { if(recognizer!=null) recognizer.destroy(); if(tts!=null) tts.shutdown(); super.onDestroy(); }
}
