<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://ai.google.dev/static/site-assets/images/share-ais-513315318.png" />
</div>

# Run and deploy your AI Studio app

This contains everything you need to run your app locally.

View your app in AI Studio: https://ai.studio/apps/9bf06d0a-43a2-419f-b3b3-327519efb395

## Signing & Keystore Configuration (Permanent Debug Signature)

This repository uses a single, permanent Debug Keystore for all builds and GitHub Actions CI pipelines to ensure consistent application signatures and allow seamless in-place APK updates without `INSTALL_FAILED_UPDATE_INCOMPATIBLE` ("package conflicts with an existing package") errors:

- **Alias:** `androiddebugkey`
- **Store Password:** `android`
- **Key Password:** `android`
- **Certificate Validity:** Until 2054
- **Keystore Encoding:** `debug.keystore.base64` (and `DEBUG_KEYSTORE_BASE64` GitHub Secret)

### GitHub Actions Secrets
In your GitHub repository settings under **Settings > Secrets and variables > Actions**, add the repository secret:
- **Name:** `DEBUG_KEYSTORE_BASE64`
- **Value:** The content of `debug.keystore.base64`

The CI workflow automatically decodes this permanent keystore to `~/.android/debug.keystore` prior to compiling the APK, eliminating any random key generation.

> **Note on Initial Update:** Installing the first APK built with this permanent keystore over an old build signed with an arbitrary temporary key requires uninstalling the old version once. All subsequent APKs will install seamlessly over each other.


**Prerequisites:**  [Android Studio](https://developer.android.com/studio)


1. Open Android Studio
2. Select **Open** and choose the directory containing this project
3. Allow Android Studio to fix any incompatibilities as it imports the project.
4. Create a file named `.env` in the project directory and set `GEMINI_API_KEY` in that file to your Gemini API key (see `.env.example` for an example)
5. Remove this line from the app's `build.gradle.kts` file: `signingConfig = signingConfigs.getByName("debugConfig")`
6. Run the app on an emulator or physical device
7. If you have already published your app in AI Studio, please [request upload key reset](https://support.google.com/googleplay/android-developer/answer/9842756#zippy=%2Crequest-an-upload-key-reset) in Google Play Console.
