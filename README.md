# AI-Driven Child Online Protection System

An end-to-end AI-powered protection system that monitors child devices for grooming and cyberbullying threats. The system utilizes Edge AI to ensure maximum privacy, scrubbing PII and performing text classification directly on the intercepted chat messages.

## System Architecture

1. **Native Message Interception**: An Android `AccessibilityService` written in Kotlin silently intercepts incoming and outgoing texts from apps like WhatsApp and Instagram.
2. **Privacy-by-Design Scrubber**: All emails, phone numbers, and URLs are stripped locally before analysis.
3. **Edge AI Classification (TFLite)**: A lightweight `Conv1D` TensorFlow Lite model analyzes the text on the edge for Grooming (PAN12 dataset) or Cyberbullying. 
4. **Auto-Translation**: Integrates `deep-translator` to translate Kinyarwanda/French into English before tokenization.
5. **Parental Dashboard**: Real-time Expo/React Native dashboard for parents to view threats and manage devices.

## How to Start the Project

To run the full GuardianEdge system, you need to open **three separate terminal windows** and start the three components in this order:

### 1. Start the Backend API & AI Engine
Open your first terminal window:
```bash
cd backend
npm run dev
```
*(This starts the Node.js server on port `5050` and initializes the Python TensorFlow Lite bridge for AI analysis).*

### 2. Start the Parental Dashboard
Open your second terminal window:
```bash
cd dashboard
npx expo start --web --port 8081
```
*(This opens the React web dashboard in your browser. Log in with the default administrator credentials: **Username:** `admin`, **Password:** `admin123` to register parent accounts).*

### 3. Start the Child Mobile App (Native Android)
Open your third terminal window. Make sure your Android Emulator is running or a physical Android phone is connected via USB:
```bash
cd child-app
npx expo run:android
```
*(This will compile the Native Kotlin Accessibility Service and install the `child-app` APK onto your emulator/phone).*

---

## Deploying to Production (Native Android)
The `child-app` contains a custom Native Expo Module (`message-interceptor`). Because it contains native Kotlin code (`ChatAccessibilityService.kt`), it cannot be run inside the standard "Expo Go" app. You must always use `npx expo run:android` to compile it.

To test the background interception on your Android device:
1. Open the **GuardianEdge** Child App and accept the Legal Consent disclosure.
2. Enter the Pairing Code generated from your Parental Dashboard.
3. Go to **Android Settings -> Accessibility** and enable **"GuardianEdge Parental Control"**.
4. Type a cyberbullying or grooming message in any app (Chrome, Messages, WhatsApp), and watch the alert pop up live on your Dashboard!
