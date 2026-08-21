# DeutschAr - قاموس ومترجم ألماني - عربي (Offline)

تطبيق أندرويد متكامل وشامل لتعلم اللغة الألمانية وترجمة الكلمات والنصوص (ألماني - عربي - إنجليزي) بدون الحاجة إلى اتصال بالإنترنت.

---

## 🌟 المميزات الرئيسية (Features)

- 📚 **قاعدة بيانات ضخمة (239,000+ كلمة):** قاموس ألماني-عربي شامل يحتوي على أدوات التعريف (`der`, `die`, `das`)، صيغ الجمع، تصريفات الأفعال، ومستويات الشيوع اللغوي (A1 إلى C2).
- ⚡ **ترجمة فورية بدون إنترنت (Offline ML Translation):** ترجمة نصوص فورية ودقيقة باستخدام Google ML Kit مدمجة كلياً على الجهاز.
- 🔍 **بحث ذكي وفوري:** بحث سريع مع دعم البحث باللغة العربية أو الألمانية مع مقترحات فورية وفلاتر حسب نوع الكلمة (اسم، فعل، صفة...).
- 🎨 **تصميم عصري (Material 3):** واجهة مستخدم مبنية بالكامل باستخدام Jetpack Compose مع دعم الوضع الداكن والفاتح وأحدث معايير التصميم.
- 📱 **نطق صوتي (Text-to-Speech):** استماع للنطق الصحيح للكلمات والجمل الألمانية.

---

## 🛠️ التقنيات المستخدمة (Tech Stack)

- **Language:** Kotlin 100%
- **UI Framework:** Jetpack Compose & Material 3
- **Architecture:** MVVM / Clean Architecture with Coroutines & StateFlow
- **Local Persistence:** Room Database (SQLite with custom indexing)
- **Machine Learning:** Google ML Kit Offline Translation
- **Build System:** Gradle (Kotlin DSL - `.gradle.kts`)

---

## 🚀 تشغيل المشروع في Android Studio

1. افتح **Android Studio** (نسخة Iguana أو أحدث).
2. اختر **Open** ثم حدد مجلد هذا المشروع.
3. انتظر حتى يكتمل الـ Gradle Sync وتحميل التبعيات.
4. قم بتشغيل التطبيق بالضغط على زر **Run ▶️** على هاتف فعلي أو محاكي (Emulator).

---

## 🔑 إعدادات التوقيع وبناء الـ APK (GitHub Actions CI/CD)

يحتوي المستودع على سير عمل جاهز ومُعد مسبقاً في `.github/workflows/build-apk.yml` لبناء ملف الـ APK وتوقيعه تلقائياً بمفتاح Debug دائم وثابت:

1. في إعدادات مستودعك على GitHub، توجه إلى:
   `Settings` ➔ `Secrets and variables` ➔ `Actions`
2. اضغط على **New repository secret** وأضف:
   - **Name:** `DEBUG_KEYSTORE_BASE64`
   - **Value:** القيمة الموجودة داخل ملف `debug.keystore.base64`
3. سيقوم سير العمل ببناء وتوقيع الـ APK وإرفاقه في قسم الـ **Releases** والـ **Artifacts** عند كل `push` أو `workflow_dispatch`.

---

## 📄 الترخيص (License)

هذا المشروع مفتوح المصدر ومتاح للاستخدام الحر.
