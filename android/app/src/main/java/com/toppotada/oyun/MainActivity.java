package com.toppotada.oyun;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.os.CancellationSignal;
import android.os.Handler;
import android.os.Looper;
import android.webkit.JavascriptInterface;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import androidx.credentials.ClearCredentialStateRequest;
import androidx.credentials.Credential;
import androidx.credentials.CredentialManager;
import androidx.credentials.CredentialManagerCallback;
import androidx.credentials.CustomCredential;
import androidx.credentials.GetCredentialRequest;
import androidx.credentials.GetCredentialResponse;
import androidx.credentials.exceptions.ClearCredentialException;
import androidx.credentials.exceptions.GetCredentialCancellationException;
import androidx.credentials.exceptions.GetCredentialException;
import androidx.webkit.WebViewAssetLoader;

import com.google.android.libraries.identity.googleid.GetSignInWithGoogleOption;
import com.google.android.libraries.identity.googleid.GoogleIdTokenCredential;

import com.google.android.gms.ads.AdError;
import com.google.android.gms.ads.AdRequest;
import com.google.android.gms.ads.FullScreenContentCallback;
import com.google.android.gms.ads.LoadAdError;
import com.google.android.gms.ads.MobileAds;
import com.google.android.gms.ads.interstitial.InterstitialAd;
import com.google.android.gms.ads.interstitial.InterstitialAdLoadCallback;
import com.google.android.gms.ads.rewarded.RewardedAd;
import com.google.android.gms.ads.rewarded.RewardedAdLoadCallback;
import com.google.android.ump.ConsentInformation;
import com.google.android.ump.ConsentRequestParameters;
import com.google.android.ump.UserMessagingPlatform;

import org.json.JSONObject;

import java.util.concurrent.atomic.AtomicBoolean;

import java.util.concurrent.Executor;

public class MainActivity extends Activity {
  private static final String HOST = "appassets.androidplatform.net";
  // Firebase > Authentication > Google > Web SDK configuration > Web client ID
  private static final String WEB_CLIENT_ID = "746866370670-sts0eebodr8nm0d1f8p5brsqc971p6tu.apps.googleusercontent.com";

  private WebView web;
  private CredentialManager creds;
  private final Handler main = new Handler(Looper.getMainLooper());
  private final Executor onMain = main::post;

  // ---- reklamlar ----
  private ConsentInformation consent;
  private final AtomicBoolean adsStarted = new AtomicBoolean(false);
  private InterstitialAd inter;
  private RewardedAd rewarded;
  private boolean interLoading, rewardLoading;

  @SuppressLint({"SetJavaScriptEnabled", "AddJavascriptInterface"})
  @Override protected void onCreate(Bundle saved) {
    super.onCreate(saved);
    creds = CredentialManager.create(this);
    final WebViewAssetLoader loader = new WebViewAssetLoader.Builder()
        .setDomain(HOST)
        .addPathHandler("/assets/", new WebViewAssetLoader.AssetsPathHandler(this))
        .build();
    web = new WebView(this);
    WebSettings s = web.getSettings();
    s.setJavaScriptEnabled(true);
    s.setDomStorageEnabled(true);
    s.setDatabaseEnabled(true);
    s.setMediaPlaybackRequiresUserGesture(false);
    s.setAllowFileAccess(false);
    s.setTextZoom(100);
    web.addJavascriptInterface(new Bridge(), "TPAndroid");
    web.setWebViewClient(new WebViewClient() {
      @Override public WebResourceResponse shouldInterceptRequest(WebView v, WebResourceRequest r) {
        return loader.shouldInterceptRequest(r.getUrl());
      }
      @Override public boolean shouldOverrideUrlLoading(WebView v, WebResourceRequest r) {
        Uri u = r.getUrl();
        if (HOST.equals(u.getHost())) return false;
        try { startActivity(new Intent(Intent.ACTION_VIEW, u)); } catch (Exception ignored) {}
        return true;
      }
    });
    setContentView(web);
    if (saved != null) web.restoreState(saved);
    else web.loadUrl("https://" + HOST + "/assets/www/index.html?kaynak=android");
    setupAds();
  }

  // AEA/BK kullanıcıları için izin formu (UMP), ardından AdMob başlatılır
  private void setupAds() {
    consent = UserMessagingPlatform.getConsentInformation(this);
    consent.requestConsentInfoUpdate(this, new ConsentRequestParameters.Builder().build(),
        () -> UserMessagingPlatform.loadAndShowConsentFormIfRequired(this, err -> { if (consent.canRequestAds()) startAds(); }),
        err -> { if (consent.canRequestAds()) startAds(); });
    if (consent.canRequestAds()) startAds();
  }

  private void startAds() {
    if (!adsStarted.compareAndSet(false, true)) return;
    new Thread(() -> {
      MobileAds.initialize(this, st -> {});
      main.post(() -> { loadInter(); loadRewarded(); });
    }).start();
  }

  private void loadInter() {
    if (!adsStarted.get() || inter != null || interLoading) return;
    interLoading = true;
    InterstitialAd.load(this, getString(R.string.ad_interstitial), new AdRequest.Builder().build(), new InterstitialAdLoadCallback() {
      @Override public void onAdLoaded(InterstitialAd ad) { interLoading = false; inter = ad; }
      @Override public void onAdFailedToLoad(LoadAdError e) { interLoading = false; inter = null; main.postDelayed(MainActivity.this::loadInter, 30000); }
    });
  }

  private void loadRewarded() {
    if (!adsStarted.get() || rewarded != null || rewardLoading) return;
    rewardLoading = true;
    RewardedAd.load(this, getString(R.string.ad_rewarded), new AdRequest.Builder().build(), new RewardedAdLoadCallback() {
      @Override public void onAdLoaded(RewardedAd ad) { rewardLoading = false; rewarded = ad; }
      @Override public void onAdFailedToLoad(LoadAdError e) { rewardLoading = false; rewarded = null; main.postDelayed(MainActivity.this::loadRewarded, 30000); }
    });
  }

  private void adDone(String kind, boolean ok) {
    final String js = "window.__tpAd&&window.__tpAd(" + JSONObject.quote(kind) + "," + ok + ")";
    main.post(() -> web.evaluateJavascript(js, null));
  }

  private void showInterstitial() {
    final InterstitialAd ad = inter;
    if (ad == null) { adDone("inter", false); loadInter(); return; }
    inter = null;
    ad.setFullScreenContentCallback(new FullScreenContentCallback() {
      @Override public void onAdDismissedFullScreenContent() { adDone("inter", true); loadInter(); }
      @Override public void onAdFailedToShowFullScreenContent(AdError e) { adDone("inter", false); loadInter(); }
    });
    ad.show(this);
  }

  private void showRewarded() {
    final RewardedAd ad = rewarded;
    if (ad == null) { adDone("reward", false); loadRewarded(); return; }
    rewarded = null;
    final boolean[] earned = { false };
    ad.setFullScreenContentCallback(new FullScreenContentCallback() {
      @Override public void onAdDismissedFullScreenContent() { adDone("reward", earned[0]); loadRewarded(); }
      @Override public void onAdFailedToShowFullScreenContent(AdError e) { adDone("reward", false); loadRewarded(); }
    });
    ad.show(this, item -> earned[0] = true);
  }

  private void toJs(boolean ok, String val) {
    final String js = "window.__tpGoogle&&window.__tpGoogle(" + ok + "," + JSONObject.quote(val == null ? "" : val) + ")";
    main.post(() -> web.evaluateJavascript(js, null));
  }

  private void googleSignIn() {
    GetSignInWithGoogleOption opt = new GetSignInWithGoogleOption.Builder(WEB_CLIENT_ID).build();
    GetCredentialRequest req = new GetCredentialRequest.Builder().addCredentialOption(opt).build();
    creds.getCredentialAsync(this, req, new CancellationSignal(), onMain,
        new CredentialManagerCallback<GetCredentialResponse, GetCredentialException>() {
          @Override public void onResult(GetCredentialResponse r) {
            Credential c = r.getCredential();
            if (c instanceof CustomCredential && GoogleIdTokenCredential.TYPE_GOOGLE_ID_TOKEN_CREDENTIAL.equals(c.getType())) {
              try { toJs(true, GoogleIdTokenCredential.createFrom(c.getData()).getIdToken()); }
              catch (Exception e) { toJs(false, "Google yanıtı okunamadı"); }
            } else toJs(false, "Beklenmeyen giriş türü");
          }
          @Override public void onError(GetCredentialException e) {
            toJs(false, e instanceof GetCredentialCancellationException ? "cancel" : String.valueOf(e.getMessage()));
          }
        });
  }

  private void googleSignOut() {
    creds.clearCredentialStateAsync(new ClearCredentialStateRequest(), new CancellationSignal(), onMain,
        new CredentialManagerCallback<Void, ClearCredentialException>() {
          @Override public void onResult(Void v) {}
          @Override public void onError(ClearCredentialException e) {}
        });
  }

  private class Bridge {
    @JavascriptInterface public void googleSignIn() { main.post(MainActivity.this::googleSignIn); }
    @JavascriptInterface public void googleSignOut() { main.post(MainActivity.this::googleSignOut); }
    @JavascriptInterface public void showInterstitial() { main.post(MainActivity.this::showInterstitial); }
    @JavascriptInterface public void showRewarded() { main.post(MainActivity.this::showRewarded); }
  }

  @Override protected void onSaveInstanceState(Bundle out) { super.onSaveInstanceState(out); web.saveState(out); }
  @Override protected void onPause() { super.onPause(); web.onPause(); }
  @Override protected void onResume() { super.onResume(); web.onResume(); }
  @Override public void onBackPressed() { if (web.canGoBack()) web.goBack(); else super.onBackPressed(); }
}
