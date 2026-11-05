# 📱 Мобільні застосунки / Mobile apps

Recipe Distiller — **self-hosted**: мобільна оболонка (Capacitor) не містить
власного UI, а підключається до **вашого сервера**. Адреса сервера вводиться
на splash-екрані при першому запуску й зберігається на пристрої.

Recipe Distiller is **self-hosted**: the mobile shell (Capacitor) ships no
bundled UI — it connects to **your own server**. You enter the server address
on the splash screen at first launch; it is stored on the device.

---

## 🇺🇦 Українською

### Android — sideload APK (безкоштовно)

1. Відкрийте [Releases](https://github.com/bigpi/recipe-distiller/releases)
   і скачайте `app-debug.apk` (артефакт збірки CI додається до кожного тега;
   окремі APK зі звичайних пушів лежать у артефактах Actions, 30 днів).
2. Дозвольте «Встановлення невідомих застосунків» для браузера/файлового
   менеджера → відкрийте APK → «Встановити».
3. При першому запуску введіть адресу сервера, напр. `http://192.168.1.10:8000`.

APK — debug-збірка: підходить для особистого користування; release-підпис
не потрібен, бо застосунок не публікується в магазині.

### iOS — AltStore / Sideloadly (безкоштовно, re-sign кожні 7 днів)

App Store вимагає Apple Developer ($99/рік) — це не в бюджеті проєкту, тому
збирається **unsigned** `.app` (zip-артефакт у Actions, 30 днів):

1. Скачайте `RecipeDistiller-unsigned.zip` зі сторінки виконання
   [Actions → ios-build](https://github.com/bigpi/recipe-distiller/actions/workflows/ios-build.yml).
2. Розпакуйте, отриману папку `App.app` перетягніть у
   [Sideloadly](https://sideloadly.io) або [AltStore](https://altstore.io)
   → підпис вашим безкоштовним Apple ID → встановлення на пристрій.
3. Безкоштовний сертифікат діє 7 днів — перевстановіть/re-sign після
   закінчення строку.

### Змінити адресу сервера

На splash-екрані: якщо збережений сервер недоступний, застосунок сам поверне
поле введення з повідомленням про помилку; кнопка «Змінити сервер» доступна
під час підключення. Адреса зберігається через `@capacitor/preferences`.

### Віддалений доступ: Tailscale (безкоштовно)

Сервер слухає у локальній мережі; щоб користуватися застосунком ззовні:

1. Встановіть [Tailscale](https://tailscale.com) на сервер і на телефон
   (безкоштовний тариф Enough для особистого use-case).
2. На сервері: `tailscale up` — пристрій отримає IP `100.x.y.z`.
3. У застосунку введіть `http://100.x.y.z:8000`.
   Аналогічно працює WireGuard / VPN вашого вибору.

> Через Tailscale можна також HTTPS: `tailscale serve` / Funnel — тоді
> адреса буде `https://<machine>.<tailnet>.ts.net`.

### Збірка локально

```bash
npm install          # @capacitor/* + typescript
npm run cap:android  # або: npx cap sync ios
cd android && ./gradlew assembleDebug   # APK: android/app/build/outputs/apk/debug/
# iOS: needs macOS + Xcode + CocoaPods
cd ../ios/App && pod install && \
  xcodebuild -workspace App.xcworkspace -scheme App -configuration Release \
  -sdk iphoneos -derivedDataPath build CODE_SIGNING_ALLOWED=NO
```

Обмеження: `android/` — minSdk 24 (Android 7.0), targetSdk 35 (Android 16);
`ios/` — deployment target iOS 14.0; єдиний Android-дозвіл — `INTERNET`;
в Info.plist дозволено http (`NSAppTransportSecurity`) для LAN/Tailscale.

---

## 🇬🇧 English

### Android — sideload the APK (free)

1. Open [Releases](https://github.com/bigpi/recipe-distiller/releases) and
   download `app-debug.apk` (CI attaches it to every tag; per-push APKs live
   in Actions artifacts, 30-day retention).
2. Allow "Install unknown apps" for your browser/file manager → open the
   APK → Install.
3. On first launch enter your server address, e.g. `http://192.168.1.10:8000`.

It is a debug-signed APK — fine for personal use; no store signing required.

### iOS — AltStore / Sideloadly (free, re-sign every 7 days)

The App Store requires Apple Developer ($99/yr) — out of budget for this
project, so CI builds an **unsigned** `.app` (zip artifact in Actions,
30-day retention):

1. Download `RecipeDistiller-unsigned.zip` from a
   [Actions → ios-build](https://github.com/bigpi/recipe-distiller/actions/workflows/ios-build.yml)
   run.
2. Unzip it and drop the `App.app` folder into
   [Sideloadly](https://sideloadly.io) or [AltStore](https://altstore.io)
   → sign with your free Apple ID → install on the device.
3. Free certificates expire after 7 days — re-sign/reinstall when they do.

### Changing the server address

If the saved server is unreachable, the splash screen returns to the address
field with an error message; a "Change server" button is available while
connecting. The address is stored via `@capacitor/preferences`.

### Remote access: Tailscale (free)

1. Install [Tailscale](https://tailscale.com) on the server and the phone
   (free tier is enough for personal use).
2. On the server: `tailscale up` — it gets a `100.x.y.z` IP.
3. Enter `http://100.x.y.z:8000` in the app. WireGuard or any VPN works the
   same way. For HTTPS: `tailscale serve` → `https://<machine>.<tailnet>.ts.net`.

### Building locally

```bash
npm install          # @capacitor/* + typescript
npm run cap:android  # or: npx cap sync ios
cd android && ./gradlew assembleDebug   # APK: android/app/build/outputs/apk/debug/
# iOS: needs macOS + Xcode + CocoaPods
cd ../ios/App && pod install && \
  xcodebuild -workspace App.xcworkspace -scheme App -configuration Release \
  -sdk iphoneos -derivedDataPath build CODE_SIGNING_ALLOWED=NO
```

Limits: `android/` — minSdk 24 (Android 7.0), targetSdk 35 (Android 16);
`ios/` — deployment target iOS 14.0; the only Android permission is
`INTERNET`; `NSAppTransportSecurity` allows plain http for LAN/Tailscale.
