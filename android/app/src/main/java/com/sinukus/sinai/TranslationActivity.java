package com.sinukus.sinai;

import android.app.Activity;
import android.os.Bundle;
import android.widget.*;
import android.view.View;
import com.google.mlkit.nl.translate.*;
import com.google.mlkit.common.model.*;
import org.json.*;
import java.io.*;
import java.nio.charset.StandardCharsets;

public class TranslationActivity extends Activity {
 private Translator translator;
 private EditText source;
 private TextView result, status;
 private Button prepare, translate;
 private boolean busy, closed;
 private final RemoteModelManager manager = RemoteModelManager.getInstance();
 private final TranslateRemoteModel english = new TranslateRemoteModel.Builder(TranslateLanguage.ENGLISH).build();
 private TranslateRemoteModel targetModel;
 private Spinner targetPicker;
 private String targetLanguage = TranslateLanguage.JAPANESE;
 @Override public void onCreate(Bundle saved) {
  super.onCreate(saved);
  configureTranslator();
  LinearLayout content=new LinearLayout(this); content.setOrientation(LinearLayout.VERTICAL); content.setPadding(24,40,24,24);
  TextView title=new TextView(this); title.setText("English → selected language · on-device translation"); title.setTextSize(22); content.addView(title);
  status=new TextView(this); status.setText("Prepare models on Wi-Fi first. Translation itself uses local models."); content.addView(status);
  source=new EditText(this); source.setMinLines(3); source.setText(getIntent().getStringExtra("source")); content.addView(source);
  try(InputStream input=getAssets().open("travel-resources.json")) {
   ByteArrayOutputStream bytes=new ByteArrayOutputStream(); byte[] buffer=new byte[4096]; int n;
   while((n=input.read(buffer))!=-1) bytes.write(buffer,0,n);
   JSONArray entries=new JSONObject(new String(bytes.toByteArray(),StandardCharsets.UTF_8)).getJSONArray("language_entries");
   String[] labels=new String[entries.length()+1]; labels[0]="Choose a template entry";
   for(int i=0;i<entries.length();i++) labels[i+1]=entries.getJSONObject(i).getString("id")+" · "+entries.getJSONObject(i).getString("english");
   Spinner picker=new Spinner(this); picker.setAdapter(new ArrayAdapter<String>(this,android.R.layout.simple_spinner_dropdown_item,labels));
   picker.setOnItemSelectedListener(new android.widget.AdapterView.OnItemSelectedListener() {
    public void onNothingSelected(android.widget.AdapterView<?> a) {}
    public void onItemSelected(android.widget.AdapterView<?> a,View v,int index,long id) { if(index>0) try { source.setText(entries.getJSONObject(index-1).getString("english")); result.setText(""); } catch(JSONException e) { status.setText(e.getMessage()); } }
   }); content.addView(picker);
  } catch(Exception e) { status.setText("Template loading failed: "+e.getMessage()); }
  targetPicker = new Spinner(this);
  java.util.List<String> codes = TranslateLanguage.getAllLanguages();
  java.util.List<String> names = new java.util.ArrayList<>();
  for(String code : codes) names.add(java.util.Locale.forLanguageTag(code).getDisplayName()+" ("+code+")");
  targetPicker.setAdapter(new ArrayAdapter<String>(this,android.R.layout.simple_spinner_dropdown_item,names));
  targetPicker.setSelection(codes.indexOf(targetLanguage));
  targetPicker.setOnItemSelectedListener(new android.widget.AdapterView.OnItemSelectedListener() {
   public void onNothingSelected(android.widget.AdapterView<?> a) {}
   public void onItemSelected(android.widget.AdapterView<?> a,View v,int index,long id) {
    String selected=codes.get(index); if(!selected.equals(targetLanguage)) { targetLanguage=selected; configureTranslator(); result.setText(""); status.setText("Target changed. Prepare its models while online before offline use."); }
   }
  }); content.addView(targetPicker);
  prepare=new Button(this); prepare.setText("Prepare models (Wi-Fi download)"); content.addView(prepare);
  translate=new Button(this); translate.setText("Translate locally"); content.addView(translate);
  result=new TextView(this); result.setTextIsSelectable(true); result.setTextSize(22); content.addView(result);
  TextView warning=new TextView(this); warning.setText("Machine translation is unverified. Confirm critical allergy or medical wording with a person."); content.addView(warning);
  prepare.setOnClickListener(v -> {
   if(busy) return; setBusy(true); status.setText("Preparing translation models…");
   translator.downloadModelIfNeeded(new DownloadConditions.Builder().requireWifi().build()).addOnSuccessListener(x -> { if(closed)return; setBusy(false); status.setText("Models ready. You can now test translation in airplane mode."); }).addOnFailureListener(e -> { if(closed)return; setBusy(false); status.setText("Model preparation failed: "+e.getMessage()); });
  });
  translate.setOnClickListener(v -> translate());
  ScrollView scroll=new ScrollView(this); scroll.addView(content); setContentView(scroll);
 }
 private void configureTranslator() {
  if(translator!=null)translator.close();
  translator=Translation.getClient(new TranslatorOptions.Builder().setSourceLanguage(TranslateLanguage.ENGLISH).setTargetLanguage(targetLanguage).build());
  targetModel=new TranslateRemoteModel.Builder(targetLanguage).build();
 }
 private void setBusy(boolean value) { busy=value; targetPicker.setEnabled(!value); prepare.setEnabled(!value); translate.setEnabled(!value); }
 private void translate() {
  String text=source.getText().toString().trim(); if(busy||text.isEmpty())return;
  setBusy(true); result.setText(""); status.setText("Verifying installed local models…");
  manager.isModelDownloaded(english).addOnSuccessListener(en -> manager.isModelDownloaded(targetModel).addOnSuccessListener(ja -> {
   if(closed)return;
   if(!en||!ja) { setBusy(false); status.setText("Models not installed. Use Prepare models while on Wi-Fi."); return; }
   translator.translate(text).addOnSuccessListener(output -> { if(closed)return; setBusy(false); result.setText(output); status.setText("Translated on device. Output is machine-generated, not reviewed."); }).addOnFailureListener(this::fail);
  }).addOnFailureListener(this::fail)).addOnFailureListener(this::fail);
 }
 private void fail(Exception e) { if(closed)return; setBusy(false); status.setText("Local translation failed: "+e.getMessage()); }
 @Override protected void onDestroy() { closed=true; if(translator!=null)translator.close(); super.onDestroy(); }
}
