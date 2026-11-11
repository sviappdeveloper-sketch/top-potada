import UIKit
import WebKit
import AuthenticationServices
import AppTrackingTransparency
import CryptoKit
import GoogleSignIn
import GoogleMobileAds
import UserMessagingPlatform

// =====================================================================
// Top Potada iOS kabuğu
// Oyun (public/ klasörü) uygulamanın içinden "toppotada://app/" adresiyle açılır.
// Web kodu Android'deki köprüyü (window.TPAndroid) bekler; aynı arayüz burada
// WKWebView mesajlarıyla sağlanır: Google/Apple girişi, reklamlar, titreşim.
// =====================================================================
final class GameViewController: UIViewController {
  static let background = UIColor(red: 0.973, green: 0.925, blue: 0.863, alpha: 1)
  static let scheme = "toppotada"

  private var web: WKWebView!
  private var appleNonce: String?

  // reklamlar
  private var adsStarted = false
  private var inter: InterstitialAd?
  private var rewarded: RewardedAd?
  private var interLoading = false, rewardLoading = false
  private var pendingAd: String?            // gösterilen tam ekran reklamın türü ("inter" / "reward")
  private var rewardEarned = false

  override var prefersStatusBarHidden: Bool { true }
  override var prefersHomeIndicatorAutoHidden: Bool { true }
  override var supportedInterfaceOrientations: UIInterfaceOrientationMask { .portrait }

  override func viewDidLoad() {
    super.viewDidLoad()
    view.backgroundColor = Self.background

    let cfg = WKWebViewConfiguration()
    if let root = Bundle.main.url(forResource: "public", withExtension: nil) {
      cfg.setURLSchemeHandler(BundleSchemeHandler(root: root), forURLScheme: Self.scheme)
    }
    cfg.allowsInlineMediaPlayback = true
    cfg.mediaTypesRequiringUserActionForPlayback = []
    cfg.userContentController.add(WeakMessageHandler(self), name: "tp")
    cfg.userContentController.addUserScript(WKUserScript(source: Self.bridgeJS, injectionTime: .atDocumentStart, forMainFrameOnly: true))

    web = WKWebView(frame: view.bounds, configuration: cfg)
    web.autoresizingMask = [.flexibleWidth, .flexibleHeight]
    web.isOpaque = false
    web.backgroundColor = Self.background
    web.scrollView.backgroundColor = Self.background
    web.scrollView.bounces = false
    web.scrollView.contentInsetAdjustmentBehavior = .never
    web.allowsLinkPreview = false
    web.navigationDelegate = self
    if #available(iOS 16.4, *) { web.isInspectable = false }
    view.addSubview(web)
    web.load(URLRequest(url: URL(string: "\(Self.scheme)://app/index.html?kaynak=ios")!))
  }

  private var askedConsent = false
  override func viewDidAppear(_ animated: Bool) {
    super.viewDidAppear(animated)
    if !askedConsent && Self.adsReady { askedConsent = true; setupAds() }
  }

  // Web tarafına köprü: Android'deki TPAndroid ile aynı adlar (oyun kodu değişmeden çalışır)
  // Google girişi için iOS istemci kimliği (Config.xcconfig) girilmiş mi
  private static var googleReady: Bool {
    let id = (Bundle.main.object(forInfoDictionaryKey: "GIDClientID") as? String) ?? ""
    return !id.isEmpty && !id.hasPrefix("BURAYA")
  }
  // Reklamlar: Config.xcconfig'te gerçek iOS AdMob kimlikleri girilmiş mi
  // (Google'ın test kimlikleriyle mağazaya "Test Ad" yazılı reklam çıkmasın: o durumda reklam kapalı)
  static var adsReady: Bool {
    let id = (Bundle.main.object(forInfoDictionaryKey: "GADApplicationIdentifier") as? String) ?? ""
    return id.hasPrefix("ca-app-pub-") && !id.contains("3940256099942544")
  }
  private static var bridgeJS: String {
    "window.TPiOSGoogle = \(googleReady);\nwindow.TPiOSAds = \(adsReady);\n" + bridgeCore
  }
  private static let bridgeCore = """
  (function(){
    var post=function(cmd,extra){ var m={cmd:cmd}; if(extra){ for(var k in extra) m[k]=extra[k]; } window.webkit.messageHandlers.tp.postMessage(m); };
    window.TPiOS = true;
    window.TPAndroid = {
      googleSignIn: function(){ post('googleSignIn'); },
      googleSignOut: function(){ post('googleSignOut'); },
      appleSignIn: function(){ post('appleSignIn'); },
      showInterstitial: function(){ post('showInterstitial'); },
      showRewarded: function(){ post('showRewarded'); }
    };
    // reklam kimlikleri yoksa reklam düğmeleri hiç görünmesin
    if(!window.TPiOSAds){ delete window.TPAndroid.showInterstitial; delete window.TPAndroid.showRewarded; }
    // iOS WebView'da navigator.vibrate yok: dokunsal geri bildirime çevir
    navigator.vibrate = function(p){ var ms = Array.isArray(p) ? p.reduce(function(a,b){return a+(+b||0);},0) : (+p||0); if(ms>0) post('haptic',{ms:ms}); return true; };
  })();
  """

  fileprivate func handle(_ body: [String: Any]) {
    switch body["cmd"] as? String ?? "" {
    case "googleSignIn": googleSignIn()
    case "googleSignOut": GIDSignIn.sharedInstance.signOut()
    case "appleSignIn": appleSignIn()
    case "showInterstitial": showInterstitial()
    case "showRewarded": showRewarded()
    case "haptic":
      let ms = (body["ms"] as? NSNumber)?.doubleValue ?? 30
      let gen = UIImpactFeedbackGenerator(style: ms >= 100 ? .heavy : (ms >= 60 ? .medium : .light))
      gen.impactOccurred()
    default: break
    }
  }

  private func js(_ code: String) {
    DispatchQueue.main.async { self.web.evaluateJavaScript(code, completionHandler: nil) }
  }
  private static func quote(_ s: String) -> String {
    guard let d = try? JSONSerialization.data(withJSONObject: s, options: .fragmentsAllowed),
          let q = String(data: d, encoding: .utf8) else { return "\"\"" }
    return q
  }

  // ---------------- Google ile giriş ----------------
  private func googleSignIn() {
    let done: (Bool, String) -> Void = { ok, val in
      self.js("window.__tpGoogle&&window.__tpGoogle(\(ok),\(Self.quote(val)))")
    }
    let clientID = (Bundle.main.object(forInfoDictionaryKey: "GIDClientID") as? String) ?? ""
    if clientID.isEmpty || clientID.hasPrefix("BURAYA") { done(false, "iOS Google ayarı eksik"); return }
    GIDSignIn.sharedInstance.configuration = GIDConfiguration(clientID: clientID)
    GIDSignIn.sharedInstance.signIn(withPresenting: self) { result, error in
      if let error = error {
        done(false, (error as NSError).code == GIDSignInError.Code.canceled.rawValue ? "cancel" : error.localizedDescription)
        return
      }
      guard let token = result?.user.idToken?.tokenString else { done(false, "Google yanıtı okunamadı"); return }
      done(true, token)
    }
  }

  // ---------------- Apple ile giriş ----------------
  private func appleSignIn() {
    let nonce = Self.randomNonce()
    appleNonce = nonce
    let req = ASAuthorizationAppleIDProvider().createRequest()
    req.requestedScopes = [.fullName, .email]
    req.nonce = SHA256.hash(data: Data(nonce.utf8)).map { String(format: "%02x", $0) }.joined()
    let c = ASAuthorizationController(authorizationRequests: [req])
    c.delegate = self
    c.presentationContextProvider = self
    c.performRequests()
  }
  fileprivate func appleDone(_ ok: Bool, _ val: String) {
    js("window.__tpApple&&window.__tpApple(\(ok),\(Self.quote(val)))")
  }
  private static func randomNonce(_ length: Int = 32) -> String {
    let chars = Array("0123456789ABCDEFGHIJKLMNOPQRSTUVXYZabcdefghijklmnopqrstuvwxyz-._")
    var out = ""
    while out.count < length {
      var b = [UInt8](repeating: 0, count: 16)
      if SecRandomCopyBytes(kSecRandomDefault, b.count, &b) != errSecSuccess { b = (0..<16).map { _ in UInt8.random(in: 0...255) } }
      for x in b where out.count < length && Int(x) < chars.count { out.append(chars[Int(x)]) }
    }
    return out
  }

  // ---------------- reklamlar (AdMob + izin formu) ----------------
  private func setupAds() {
    let info = ConsentInformation.shared
    info.requestConsentInfoUpdate(with: RequestParameters()) { [weak self] _ in
      guard let self = self else { return }
      ConsentForm.loadAndPresentIfRequired(from: self) { [weak self] _ in
        self?.askTrackingThenStart()
      }
    }
    if info.canRequestAds { askTrackingThenStart() }
  }
  private func askTrackingThenStart() {
    guard ConsentInformation.shared.canRequestAds else { return }
    if ATTrackingManager.trackingAuthorizationStatus == .notDetermined {
      ATTrackingManager.requestTrackingAuthorization { [weak self] _ in DispatchQueue.main.async { self?.startAds() } }
    } else { startAds() }
  }
  private func startAds() {
    if adsStarted { return }
    adsStarted = true
    MobileAds.shared.start(completionHandler: nil)
    loadInter(); loadRewarded()
  }
  private func unit(_ key: String) -> String { (Bundle.main.object(forInfoDictionaryKey: key) as? String) ?? "" }

  private func loadInter() {
    guard adsStarted, inter == nil, !interLoading else { return }
    interLoading = true
    InterstitialAd.load(with: unit("TPAdInterstitial"), request: Request()) { [weak self] ad, _ in
      self?.interLoading = false; self?.inter = ad
    }
  }
  private func loadRewarded() {
    guard adsStarted, rewarded == nil, !rewardLoading else { return }
    rewardLoading = true
    RewardedAd.load(with: unit("TPAdRewarded"), request: Request()) { [weak self] ad, _ in
      self?.rewardLoading = false; self?.rewarded = ad
    }
  }
  private func adDone(_ kind: String, _ ok: Bool) {
    js("window.__tpAd&&window.__tpAd(\(Self.quote(kind)),\(ok))")
  }
  private func showInterstitial() {
    guard let ad = inter else { adDone("inter", false); loadInter(); return }
    inter = nil; pendingAd = "inter"
    ad.fullScreenContentDelegate = self
    ad.present(from: self)
  }
  private func showRewarded() {
    guard let ad = rewarded else { adDone("reward", false); loadRewarded(); return }
    rewarded = nil; pendingAd = "reward"; rewardEarned = false
    ad.fullScreenContentDelegate = self
    ad.present(from: self) { [weak self] in self?.rewardEarned = true }
  }
  private func fullScreenEnded(_ shown: Bool) {
    let kind = pendingAd ?? "inter"; pendingAd = nil
    adDone(kind, kind == "reward" ? (shown && rewardEarned) : shown)
    if kind == "reward" { loadRewarded() } else { loadInter() }
  }
}

// ---------------- reklam geri çağrıları ----------------
extension GameViewController: FullScreenContentDelegate {
  func adDidDismissFullScreenContent(_ ad: FullScreenPresentingAd) { fullScreenEnded(true) }
  func ad(_ ad: FullScreenPresentingAd, didFailToPresentFullScreenContentWithError error: Error) { fullScreenEnded(false) }
}

// ---------------- Apple girişi geri çağrıları ----------------
extension GameViewController: ASAuthorizationControllerDelegate, ASAuthorizationControllerPresentationContextProviding {
  func presentationAnchor(for controller: ASAuthorizationController) -> ASPresentationAnchor {
    return view.window ?? UIWindow()
  }
  func authorizationController(controller: ASAuthorizationController, didCompleteWithAuthorization authorization: ASAuthorization) {
    guard let cred = authorization.credential as? ASAuthorizationAppleIDCredential,
          let tokenData = cred.identityToken, let token = String(data: tokenData, encoding: .utf8),
          let nonce = appleNonce else { appleDone(false, "Apple yanıtı okunamadı"); return }
    let name = [cred.fullName?.givenName, cred.fullName?.familyName].compactMap { $0 }.joined(separator: " ")
    // authorizationCode: hesap silinirken Apple izninin geri alınması (revoke) için gerekir
    let code = cred.authorizationCode.flatMap { String(data: $0, encoding: .utf8) } ?? ""
    let payload: [String: Any] = ["idToken": token, "nonce": nonce, "name": name, "code": code]
    guard let d = try? JSONSerialization.data(withJSONObject: payload), let s = String(data: d, encoding: .utf8) else {
      appleDone(false, "Apple yanıtı okunamadı"); return
    }
    appleDone(true, s)
  }
  func authorizationController(controller: ASAuthorizationController, didCompleteWithError error: Error) {
    let canceled = (error as? ASAuthorizationError)?.code == .canceled
    appleDone(false, canceled ? "cancel" : error.localizedDescription)
  }
}

// ---------------- dış bağlantılar Safari'de açılır ----------------
extension GameViewController: WKNavigationDelegate {
  func webView(_ webView: WKWebView, decidePolicyFor action: WKNavigationAction,
               decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
    guard let url = action.request.url else { decisionHandler(.allow); return }
    if url.scheme == Self.scheme || url.scheme == "about" || url.scheme == "blob" || url.scheme == "data" {
      decisionHandler(.allow); return
    }
    if action.targetFrame?.isMainFrame ?? true {
      UIApplication.shared.open(url)
      decisionHandler(.cancel)
    } else {
      decisionHandler(.allow)    // Firebase'in gizli çerçeveleri vb.
    }
  }
  // WebView süreci kapanırsa (bellek) oyunu yeniden yükle
  func webViewWebContentProcessDidTerminate(_ webView: WKWebView) { webView.reload() }
}

// WKUserContentController denetleyiciyi güçlü tutar; döngüyü kırmak için zayıf aracı
private final class WeakMessageHandler: NSObject, WKScriptMessageHandler {
  weak var target: GameViewController?
  init(_ t: GameViewController) { target = t }
  func userContentController(_ c: WKUserContentController, didReceive message: WKScriptMessage) {
    if let body = message.body as? [String: Any] { target?.handle(body) }
  }
}

// Uygulama içindeki public/ klasörünü "toppotada://app/..." adresinden sunar
private final class BundleSchemeHandler: NSObject, WKURLSchemeHandler {
  let root: URL
  init(root: URL) { self.root = root.standardizedFileURL }

  func webView(_ webView: WKWebView, start task: WKURLSchemeTask) {
    guard let url = task.request.url else { task.didFailWithError(URLError(.badURL)); return }
    var path = url.path
    if path.isEmpty || path == "/" { path = "/index.html" }
    let file = root.appendingPathComponent(String(path.dropFirst())).standardizedFileURL
    guard file.path.hasPrefix(root.path), let data = try? Data(contentsOf: file) else {
      let r = HTTPURLResponse(url: url, statusCode: 404, httpVersion: "HTTP/1.1", headerFields: ["Content-Type": "text/plain"])!
      task.didReceive(r); task.didReceive(Data()); task.didFinish(); return
    }
    let headers = ["Content-Type": Self.mime(file.pathExtension), "Content-Length": String(data.count),
                   "Cache-Control": "no-cache", "Access-Control-Allow-Origin": "*"]
    let r = HTTPURLResponse(url: url, statusCode: 200, httpVersion: "HTTP/1.1", headerFields: headers)!
    task.didReceive(r); task.didReceive(data); task.didFinish()
  }
  func webView(_ webView: WKWebView, stop task: WKURLSchemeTask) {}

  static func mime(_ ext: String) -> String {
    switch ext.lowercased() {
    case "html", "htm": return "text/html; charset=utf-8"
    case "js", "mjs": return "text/javascript; charset=utf-8"
    case "css": return "text/css; charset=utf-8"
    case "json", "webmanifest": return "application/json"
    case "png": return "image/png"
    case "jpg", "jpeg": return "image/jpeg"
    case "svg": return "image/svg+xml"
    case "mp3": return "audio/mpeg"
    case "wav": return "audio/wav"
    case "txt": return "text/plain; charset=utf-8"
    default: return "application/octet-stream"
    }
  }
}
