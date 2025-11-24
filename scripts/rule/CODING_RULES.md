# CODING RULES

Quy tắc code cho dự án Flutter - Clean Architecture với GetX state management.

---

## 1. NAMING CONVENTIONS

### File Naming (snake_case)

```
# Screens
{feature_name}_screen.dart          → setting_screen.dart

# Controllers
{feature_name}_controller.dart      → setting_controller.dart

# Widgets
{widget_name}_widget.dart           → button_widget.dart

# Dialogs
dialog_{purpose}.dart               → dialog_delete.dart

# Entities
{entity_name}_entity.dart           → auth_entity.dart
{entity_name}.dart (core)           → user.dart

# Models
{model_name}_model.dart             → user_model.dart
{model_name}_response.dart          → user_response.dart

# Use Cases
{feature_name}_usecase.dart         → setting_usecase.dart

# Repositories
{feature_name}_repository.dart      → setting_repository.dart
{feature_name}_repository_impl.dart → setting_repository_impl.dart

# Mappers
{entity_name}_mapper.dart           → user_auth_mapper.dart
```

### Class Naming (PascalCase)

```dart
// Screens
class SettingScreen extends StatelessWidget {}

// Controllers
class SettingController extends GetxController {}

// Widgets
class ButtonWidget extends StatefulWidget {}

// Entities
@immutable
class AuthEntity {
  const AuthEntity({required this.accessToken});
  final String accessToken;
}

// Models
class UserModel extends User {
  factory UserModel.fromJson(Map<String, dynamic> json) {...}
}

// Repositories
abstract class SettingRepository {...}
class SettingRepositoryImpl implements SettingRepository {...}
```

### Variables & Methods (camelCase)

```dart
// Variables
String userName = 'John';
bool isLoading = false;

// GetX Observables
final RxBool isNotificationEnabled = true.obs;
Rx<User?> user = Rx<User?>(null);

// Private
final ApiService _apiService;

// Methods (verb-first)
void onTapLanguage() {}
Future<void> updateUserStatus() async {}
bool validateEmail(String email) {}
```

---

## 2. ASSETS MANAGEMENT

### ✅ ĐÚNG - Type-safe với flutter_gen

```dart
import 'package:base_project/core/gen/assets.gen.dart';

// SVG Icons
SvgPicture.asset(Assets.icons.iconsSettings.iconApple)
SvgPicture.asset(Assets.icons.iconBack)

// Images
Assets.images.logoTqc.image()

// Fonts
Assets.fonts.sourceSans3Bold
```

### ❌ SAI - Hardcode string path

```dart
// KHÔNG BAO GIỜ làm thế này
SvgPicture.asset('assets/icons/icons_settings/icon_apple.svg')
Image.asset('assets/images/logo_tqc.png')
```

### Asset Organization

```
# Icons (snake_case)
assets/icons/icon_back.svg
  → Assets.icons.iconBack

# Nested folders
assets/icons/icons_settings/icon_apple.svg
  → Assets.icons.iconsSettings.iconApple

# Images (snake_case)
assets/images/logo_tqc.png
  → Assets.images.logoTqc

# Fonts (PascalCase-PascalCase)
assets/fonts/SourceSans3-Bold.ttf
```

**Quy tắc:** snake_case file → camelCase property, nested folders → nested classes

---

## 3. LOCALIZATION

### Translation Files

```
assets/translations/
  ├── en-US.json  (lowercase-UPPERCASE)
  ├── vi-VN.json
  └── ja-JP.json
```

### Translation Keys (snake_case, hierarchical)

```json
{
  "app": { "name": "OIO Track" },
  "common": { "save": "Save", "cancel": "Cancel" },
  "auth": {
    "sign_in": "Sign In",
    "email": "Email",
    "welcome_user": "Welcome, {name}"
  },
  "settings": { "language": "Language" },
  "validation": { "email_required": "Please enter email" },
  "messages": { "success": "Success" }
}
```

**Categories:** `app.*`, `common.*`, `auth.*`, `settings.*`, `validation.*`, `messages.*`

### Usage

```dart
import 'package:easy_localization/easy_localization.dart';

// Basic
Text(context.tr('settings.language'))
ButtonWidget(text: context.tr('common.save'))

// Interpolation
Text(context.tr('auth.welcome_user', namedArgs: {'name': userName}))

// ✅ Luôn dùng context.tr() cho UI text
// ❌ Không hardcode string
// ❌ Không dùng camelCase cho keys
```

---

## 4. ERROR HANDLING

### Custom Failures

```dart
// Location: lib/core/errors/

abstract class Failure implements Exception {
  Failure({this.message = ''});
  final String message;
}

// Concrete types
class NetworkException extends Failure {...}
class ServerFailure extends Failure {...}
class ServerTimeOut extends Failure {...}
class ServerNotFound extends Failure {...}
class UnknownException extends Failure {...}
```

### Either<Failure, T> Pattern

```dart
import 'package:dartz/dartz.dart';

// Repository Interface
abstract class SettingRepository {
  Future<Either<Failure, User>> updateAccount(String? name, String? avatar);
}

// Implementation
@override
Future<Either<Failure, User>> updateAccount(String? name, String? avatar) async {
  try {
    final response = await apiService.put(AppUrl.updateAccount, data: {...});

    if (response['error_code'] == 0) {
      return Right(UserModel.fromJson(response['data']));
    }

    return Left(ServerFailure(message: response['message']));
  } catch (e) {
    return Left(Failure(message: e.toString()));
  }
}
```

### Controller Error Handling

```dart
// Basic pattern
Future<void> updateAccount() async {
  final result = await useCase.updateAccount(name, avatar);

  result.fold(
    (failure) => CustomSnackBar.showError(message: failure.message),
    (user) {
      this.user.value = user;
      CustomSnackBar.showSuccess(message: 'Profile updated');
    },
  );
}

// With Loading
Future<void> deleteAccount() async {
  Loading.show();

  try {
    final result = await useCase.deleteAccount();

    result.fold(
      (failure) => CustomSnackBar.showError(message: failure.message),
      (success) => Get.offAllNamed(RouterName.signIn),
    );
  } finally {
    Loading.hide();
  }
}
```

### User Feedback

```dart
// CustomSnackBar types
CustomSnackBar.showError(message: 'Login failed');      // Red with X
CustomSnackBar.showSuccess(message: 'Account created'); // Green with ✓
CustomSnackBar.showWarning(message: 'Check input');     // Yellow
CustomSnackBar.showInfo(message: 'Coming soon');        // Blue

// Loading
Loading.show();  // Non-dismissible
Loading.hide();
```

### Best Practices

**✅ DO:**
- Return `Either<Failure, T>` trong repositories
- Sử dụng specific Failure types
- Hiển thị Loading trước async operations
- Hide loading trong finally block
- Handle cả success và failure trong fold()

**❌ DON'T:**
- Throw raw exceptions ra UI layer
- Hardcode error messages
- Quên hide loading dialog
- Ignore failure case
- Show multiple loading cùng lúc

---

## 5. ADDITIONAL PATTERNS

### Text Styling

```dart
import 'package:base_project/core/constants/app_text_style.dart';

context.textStyle.bodyLG.medium
context.textStyle.headingMD.bold.textPrimary
context.textStyle.bodySM.regular.textSecondary

// Sizes: heading2XL(64), headingXL(40), headingLG(32), headingMD(24),
//        headingSM(20), headingXS(18), bodyLG(16), bodyMD(14), bodySM(12)
// Weights: .bold, .semiBold, .medium, .regular
// Colors: .textPrimary, .textSecondary, .textBrandPrimary
```

### Spacing

```dart
import 'package:base_project/core/constants/values.dart';

AppValue.hSpaceTiny    // 8px width
AppValue.hSpaceSmall   // 16px
AppValue.vSpaceSmall   // 16px height
AppValue.hSpace(12)    // Custom
```

### Colors & Router

```dart
import 'package:base_project/core/constants/colors.dart';
import 'package:base_project/core/constants/router_name.dart';

AppColors.bgrPrimary
AppColors.textPrimary

RouterName.home      // '/home'
Get.toNamed(RouterName.signIn);
Get.offAllNamed(RouterName.home);
```

---

## 6. COMMON MISTAKES

### ❌ Asset Hardcoding
```dart
Image.asset('assets/images/logo.png')        // WRONG
Assets.images.logo.image()                   // CORRECT
```

### ❌ String Hardcoding
```dart
Text('Settings')                             // WRONG
Text(context.tr('settings.settings'))        // CORRECT
```

### ❌ Raw Exception
```dart
throw Exception('Failed');                   // WRONG
return Left(ServerFailure(message: '...'));  // CORRECT
```

### ❌ Missing Loading
```dart
final result = await useCase.delete();       // WRONG

Loading.show();                              // CORRECT
try { await useCase.delete(); }
finally { Loading.hide(); }
```

### ❌ Inconsistent Naming
```dart
class settingScreen {}                       // WRONG (lowercase)
class Setting_Controller {}                  // WRONG (underscore)

class SettingScreen {}                       // CORRECT (PascalCase)
class SettingController {}                   // CORRECT
```

---

## 7. ARCHITECTURE CHECKLIST

- ✅ Clean Architecture: domain/data/presentation layers
- ✅ Dependency injection trong service_locator.dart
- ✅ Immutable entities với @immutable
- ✅ GetX observables (.obs) cho reactive state
- ✅ Either<Failure, T> cho error handling
- ✅ Type-safe assets với flutter_gen
- ✅ Structured translations với easy_localization
- ✅ Format code: 80 char line length
- ✅ Pre-commit hooks với lint_staged

---

**Tuân thủ quy tắc này để codebase nhất quán, dễ maintain và scalable.**
