# Flutter Code Review Guide - Clean Architecture + GetX

Comprehensive guide for reviewing Flutter code following Clean Architecture principles with GetX state management.

---

## 1. CLEAN ARCHITECTURE - DEPENDENCY RULES

### Core Principle
> **Domain is the center. Domain depends on NOTHING!**

### Layer Dependencies
```
Presentation Layer (UI, Controllers, Widgets)
    ↓ CAN import Domain
    ✗ CANNOT import Data

Domain Layer (Entities, UseCases, Repositories)
    ✗ CANNOT import Data
    ✗ CANNOT import Presentation

Data Layer (Models, DataSources, Implementations)
    ↓ CAN import Domain interfaces
```

### Review Checklist - Domain Layer

**✅ CORRECT:**
```dart
// domain/entities/user_entity.dart
class UserEntity {
  final String id;
  final String email;
  final String name;

  const UserEntity({required this.id, required this.email, required this.name});
}

// domain/repositories/user_repository.dart
abstract class UserRepository {
  Future<Either<Failure, UserEntity>> login(String email, String password);
}
```

**❌ VIOLATIONS:**
```dart
// ❌ Domain importing Data
import 'package:app/features/auth/data/models/user_model.dart';

// ❌ Entity with JSON logic
class UserEntity {
  UserEntity.fromJson(Map<String, dynamic> json) {...}
}

// ❌ Repository returning Model instead of Entity
Future<UserModel> login();
```

**Domain Must:**
- [ ] NO imports from `data/` or `presentation/`
- [ ] Entities are pure objects (no `.fromJson()`, `.toJson()`)
- [ ] Repository interfaces return `Either<Failure, Entity>`
- [ ] UseCases return entities

---

### Review Checklist - Data Layer

**✅ CORRECT:**
```dart
// data/models/user_model.dart
class UserModel {
  String? id;
  String? email;

  UserModel.fromJson(Map<String, dynamic> json) {
    id = json['id'];
    email = json['email'];
  }

  Map<String, dynamic> toJson() => {'id': id, 'email': email};
}

// data/mappers/user_mapper.dart
class UserMapper {
  static UserEntity toEntity(UserModel model) {
    return UserEntity(
      id: model.id ?? '',
      email: model.email ?? '',
    );
  }
}

// data/repositories/user_repository_impl.dart
class UserRepositoryImpl implements UserRepository {
  @override
  Future<Either<Failure, UserEntity>> login(String email, String password) async {
    try {
      final response = await _apiService.post('/login', {...});
      final model = UserModel.fromJson(response.data);
      final entity = UserMapper.toEntity(model); // ✅ Map to entity
      return Right(entity);
    } catch (e) {
      return Left(ServerFailure(e.toString()));
    }
  }
}
```

**Data Must:**
- [ ] Models have JSON serialization (`.fromJson()`, `.toJson()`)
- [ ] Repository implementations use mappers
- [ ] Always convert Model → Entity before returning
- [ ] Only Data layer knows about API/Database

---

### Review Checklist - Presentation Layer

**✅ CORRECT:**
```dart
// presentation/controllers/login_controller.dart
import 'package:app/features/auth/domain/entities/user_entity.dart'; // ✅
import 'package:app/features/auth/domain/usecases/login_usecase.dart'; // ✅

class LoginController extends GetxController {
  final LoginUseCase _loginUseCase;

  LoginController(this._loginUseCase);

  Future<void> login(String email, String password) async {
    final result = await _loginUseCase.execute(email, password);

    result.fold(
      (failure) => showError(failure.message),
      (userEntity) => navigateToHome(userEntity), // ✅ Receives entity
    );
  }
}
```

**❌ VIOLATIONS:**
```dart
// ❌ Importing Data layer
import 'package:app/features/auth/data/models/user_model.dart';

// ❌ Calling API directly
final model = await ApiService().login();
```

**Presentation Must:**
- [ ] Import domain only (entities, usecases)
- [ ] Use UseCases, NOT API services directly
- [ ] Work with entities, NOT models
- [ ] NO imports from `data/models/`

---

## 2. GETX CONTROLLER MANAGEMENT

### Golden Rule
> **ONE Controller = ONE Instance = MANY Widgets**

### 3-Step Pattern

**1️⃣ Register in Service Locator**
```dart
// lib/core/di/service_locator.dart
..registerFactory(HomeController.new)
```

**2️⃣ Initialize ONCE at Root Widget**
```dart
// Root screen only (HomeScreen, NavigatorScreen)
GetBuilder<HomeController>(
  init: locator<HomeController>(),  // ✅ Initialize once
  builder: (controller) => ...,
)
```

**3️⃣ Reuse in Child Widgets**
```dart
// In tabs, dialogs, child widgets
GetBuilder<HomeController>(  // ✅ NO init parameter
  builder: (controller) => ...,
)

// OR
final controller = Get.find<HomeController>();  // ✅ Find existing instance
```

### Review Checklist - GetX

**❌ VIOLATIONS:**
```dart
Get.put(HomeController())        // ❌ Creates new instance
final c = HomeController()       // ❌ Manual instantiation
GetBuilder<HomeController>(
  init: locator<HomeController>(),  // ❌ In child widget (should be at root only)
  builder: ...,
)
```

**GetX Must:**
- [ ] Controllers registered in service locator
- [ ] `init:` parameter used ONLY in root widget
- [ ] Child widgets use `Get.find()` or `GetBuilder` without `init`
- [ ] NO `Get.put()` in dialogs or child widgets
- [ ] NO manual instantiation (`HomeController()`)

---

## 3. NAMING CONVENTIONS

### File Names (snake_case)
```
✅ setting_screen.dart
✅ setting_controller.dart
✅ user_model.dart
✅ dialog_delete.dart
✅ button_widget.dart
✅ user_auth_mapper.dart
```

### Class Names (PascalCase)
```dart
✅ class SettingScreen extends StatelessWidget {}
✅ class SettingController extends GetxController {}
✅ class UserModel extends User {}
✅ @immutable class AuthEntity {}
```

### Variables & Methods (camelCase)
```dart
✅ String userName = 'John';
✅ final RxBool isNotificationEnabled = true.obs;
✅ Rx<User?> user = Rx<User?>(null);
✅ void onTapLanguage() {}
✅ Future<void> updateUserStatus() async {}
```

### Review Checklist - Naming
- [ ] Files use snake_case
- [ ] Classes use PascalCase
- [ ] Variables/methods use camelCase
- [ ] Private members start with `_`
- [ ] Methods start with verbs (get, set, update, validate, on)

---

## 4. TYPE-SAFE ASSETS

### Review Checklist

**✅ CORRECT:**
```dart
import 'package:base_project/core/gen/assets.gen.dart';

// SVG Icons
SvgPicture.asset(Assets.icons.iconBack)
SvgPicture.asset(Assets.icons.iconsSettings.iconApple)

// Images
Assets.images.logoTqc.image()

// Fonts
Assets.fonts.sourceSans3Bold
```

**❌ VIOLATIONS:**
```dart
// ❌ Hardcoded paths
SvgPicture.asset('assets/icons/icon_back.svg')
Image.asset('assets/images/logo_tqc.png')
```

**Assets Must:**
- [ ] Use `Assets.` generated classes
- [ ] NO hardcoded string paths
- [ ] Follow folder structure: `Assets.icons.iconsSettings.iconApple`

---

## 5. LOCALIZATION

### Translation File Structure
```
assets/translations/
  ├── en-US.json
  ├── vi-VN.json
  └── ja-JP.json
```

### Translation Keys (snake_case, hierarchical)
```json
{
  "app": {"name": "App Name"},
  "common": {"save": "Save", "cancel": "Cancel"},
  "auth": {
    "sign_in": "Sign In",
    "welcome_user": "Welcome, {name}"
  },
  "settings": {"language": "Language"},
  "validation": {"email_required": "Please enter email"},
  "messages": {"success": "Success"}
}
```

### Review Checklist - i18n

**✅ CORRECT:**
```dart
import 'package:easy_localization/easy_localization.dart';

Text(context.tr('settings.language'))
ButtonWidget(text: context.tr('common.save'))

// With interpolation
Text(context.tr('auth.welcome_user', namedArgs: {'name': userName}))
```

**❌ VIOLATIONS:**
```dart
Text('Settings')  // ❌ Hardcoded string
Text(context.tr('settingsLanguage'))  // ❌ camelCase key (should be snake_case)
```

**i18n Must:**
- [ ] All UI text uses `context.tr()`
- [ ] Keys use snake_case with dot notation
- [ ] Keys organized by category (app, common, auth, settings, validation, messages)
- [ ] NO hardcoded UI strings
- [ ] Translation files named `en-US.json` (lowercase-UPPERCASE)

---

## 6. ERROR HANDLING

### Failure Types
```dart
// lib/core/errors/
abstract class Failure implements Exception {
  Failure({this.message = ''});
  final String message;
}

class NetworkException extends Failure {}
class ServerFailure extends Failure {}
class ServerTimeOut extends Failure {}
class UnknownException extends Failure {}
```

### Either Pattern

**Repository:**
```dart
abstract class SettingRepository {
  Future<Either<Failure, User>> updateAccount(String? name, String? avatar);
}

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

**Controller:**
```dart
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

### Review Checklist - Error Handling

**✅ DO:**
- [ ] Return `Either<Failure, T>` in repositories
- [ ] Use specific Failure types
- [ ] Show Loading before async operations
- [ ] Hide loading in `finally` block
- [ ] Handle both success and failure in `fold()`
- [ ] Use CustomSnackBar for user feedback

**❌ DON'T:**
```dart
throw Exception('Failed');  // ❌ Raw exception
final result = await useCase.delete();  // ❌ Missing Loading
// Ignoring failure case  // ❌
```

---

## 7. STYLING & UI CONSTANTS

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

Get.toNamed(RouterName.signIn);
Get.offAllNamed(RouterName.home);
```

---

## 8. QUICK VIOLATION DETECTION

### Command-line Checks
```bash
# Check Domain importing Data (should return nothing)
grep -r "import.*data/" lib/features/*/domain/

# Check Presentation importing Data models (should return nothing)
grep -r "import.*data/models/" lib/features/*/presentation/

# Find hardcoded asset paths
grep -r "assets/" lib/ --include="*.dart" | grep -v "Assets."

# Find hardcoded strings in Text widgets
grep -r "Text(" lib/ | grep -v "context.tr"
```

---

## 9. SUMMARY MATRIX

| Aspect | ✅ CORRECT | ❌ WRONG |
|--------|-----------|---------|
| **Architecture** | Domain independent | Domain imports Data |
| **Entities** | Pure objects | Has `.fromJson()` |
| **Repositories** | Return `Either<Failure, Entity>` | Return `Model` |
| **Controllers** | Import domain, use UseCases | Import data, call API directly |
| **GetX** | `init:` at root, `Get.find()` in children | `Get.put()` everywhere |
| **Assets** | `Assets.icons.iconBack` | `'assets/icons/icon_back.svg'` |
| **i18n** | `context.tr('auth.sign_in')` | `'Sign In'` |
| **Errors** | `Either<Failure, T>` + `.fold()` | `throw Exception()` |
| **Naming** | snake_case files, PascalCase classes | Inconsistent naming |

---

## 10. CODE REVIEW PRIORITIES

### Critical (Must Fix)
1. Architecture violations (Domain importing Data/Presentation)
2. Repository returning Models instead of Entities
3. Missing error handling (`Either` pattern)
4. GetX instance management (`Get.put()` in wrong places)
5. Hardcoded strings in UI

### Important (Should Fix)
1. Hardcoded asset paths
2. Missing type safety
3. Raw exceptions instead of Failures
4. Missing Loading indicators
5. Naming convention violations

### Nice to Have
1. Code comments in English
2. Consistent code formatting (80 char line length)
3. Organized imports
4. Immutability annotations
