# GetX Controller Rules

## Nguyên tắc vàng

> **MỘT Controller = MỘT Instance = NHIỀU Widgets**

## Quy tắc 3 bước

### 1️⃣ Đăng ký trong Service Locator
```dart
// lib/core/di/service_locator.dart
..registerFactory(HomeController.new)
```

### 2️⃣ Khởi tạo 1 LẦN ở root widget
```dart
// Root screen (HomeScreen, NavigatorScreen...)
GetBuilder<HomeController>(
  init: locator<HomeController>(),  // ✅ Chỉ 1 lần duy nhất
  builder: (controller) => ...,
)
```

### 3️⃣ Tái sử dụng ở child widgets
```dart
// Trong tabs, dialogs, child widgets
GetBuilder<HomeController>(  // ✅ KHÔNG có init
  builder: (controller) => ...,
)

// HOẶC

final controller = Get.find<HomeController>();  // ✅ Tìm instance có sẵn
```

---

## ❌ KHÔNG BAO GIỜ

```dart
Get.put(HomeController())        // ❌ Tạo instance mới
final c = HomeController()       // ❌ Tạo instance thủ công
```

---

## Lý do

- ❌ `Get.put()` trong dialog → **State sai** + **Memory leak**
- ✅ `Get.find()` → Dùng chung 1 instance → **State đúng**

---

##Ví dụ thực tế project

```dart
✅ HomeScreen         → init: locator<HomeController>()
✅ CheerfulPondTab    → GetBuilder<HomeController>() (no init)
✅ HappyFarmTab       → GetBuilder<HomeController>() (no init)
✅ ZoomImageDialog    → Get.find<HomeController>()
```
