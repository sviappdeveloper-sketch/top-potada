import UIKit
import GoogleSignIn

@main
final class AppDelegate: UIResponder, UIApplicationDelegate {
  var window: UIWindow?

  func application(_ application: UIApplication,
                   didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
    let w = UIWindow(frame: UIScreen.main.bounds)
    w.backgroundColor = GameViewController.background
    w.rootViewController = GameViewController()
    w.makeKeyAndVisible()
    window = w
    return true
  }

  // Google girişi Safari/uygulama dönüşü
  func application(_ app: UIApplication, open url: URL,
                   options: [UIApplication.OpenURLOptionsKey: Any] = [:]) -> Bool {
    return GIDSignIn.sharedInstance.handle(url)
  }
}
