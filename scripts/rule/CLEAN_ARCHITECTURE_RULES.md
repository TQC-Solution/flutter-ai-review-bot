# Clean Architecture Rules - Quy Tắc Vàng

## 🎯 NGUYÊN TẮC CƠ BẢN

> **Domain là trung tâm. Domain KHÔNG phụ thuộc ai!**

---

## 📐 DEPENDENCY RULE (Quy tắc phụ thuộc)

```
┌─────────────────────────────────────┐
│         Presentation Layer          │
│    (UI, Controllers, Widgets)       │
│                                     │
│   ✅ import từ Domain               │
│   ❌ KHÔNG import từ Data           │
└──────────────┬──────────────────────┘
               ↓
┌──────────────▼──────────────────────┐
│          Domain Layer               │
│    (Entities, UseCases, Repos)      │
│                                     │
│   ❌ KHÔNG import từ Data           │
│   ❌ KHÔNG import từ Presentation   │
└─────────────────────────────────────┘
               ↑
┌──────────────┴──────────────────────┐
│           Data Layer                │
│    (Models, DataSources, Impls)     │
│                                     │
│   ✅ import từ Domain (interfaces)  │
└─────────────────────────────────────┘
```

### Chiều mũi tên = Chiều phụ thuộc

- **Presentation** → **Domain** ✅
- **Data** → **Domain** ✅
- **Domain** → **Data** ❌ **VI PHẠM!**
- **Domain** → **Presentation** ❌ **VI PHẠM!**

---

## 🏗️ CẤU TRÚC LAYERS

### 1️⃣ Domain Layer (Core Business Logic)

**Vai trò:** Quy tắc nghiệp vụ thuần túy, độc lập với framework

```dart
domain/
├── entities/          // Business objects (Novel, Tag, Banner...)
│   ├── novel.dart
│   ├── banner.dart
│   └── tag.dart
├── repositories/      // Interfaces (abstract classes)
│   └── home_repository.dart
└── usecases/         // Business logic
    └── home_usecase.dart
```

**Đặc điểm:**
- ✅ Không có JSON serialization (`.fromJson()`, `.toJson()`)
- ✅ Không có database logic
- ✅ Không có UI logic
- ✅ Chỉ chứa **business logic** thuần túy
- ✅ Pure Dart objects
- ❌ KHÔNG import `data/` hoặc `presentation/`

**Ví dụ Entity (Từ dự án thực tế):**

```dart
// ✅ ĐÚNG - lib/core/domain/entities/novel.dart
import 'package:oionovel/core/constants/app_url.dart';

class Novel {
  final String id;
  final String title;
  final String coverImage;
  final List<Tag> tags;

  Novel({
    required this.id,
    required this.title,
    required this.coverImage,
    required this.tags,
  });

  /// Business logic: Get full image URL
  String get fullImageUrl {
    if (coverImage.startsWith('http')) {
      return coverImage;
    }
    return '${AppUrl.urlImage}$coverImage';
  }

  /// Business logic: Get tag type for display
  String? get tagType {
    if (type == 'NEW') return 'new';
    if (type == 'END') return 'end';
    if (type == 'UP') return 'up';
    return null;
  }

  /// Business logic: Format subtitle from tags
  String? get subtitle {
    if (tags.isEmpty) return null;
    return tags.take(3).map((tag) => tag.name).join(', ');
  }
}
```

```dart
// ❌ SAI - Entity KHÔNG NÊN có JSON logic
class Novel {
  String? id;
  String? title;

  // ❌ KHÔNG được có JSON serialization trong Entity
  Novel.fromJson(Map<String, dynamic> json) {
    id = json['id'];
    title = json['title'];
  }

  // ❌ KHÔNG được có JSON serialization trong Entity
  Map<String, dynamic> toJson() => {
    'id': id,
    'title': title,
  };
}
```

**Ví dụ Repository Interface:**

```dart
// ✅ ĐÚNG - lib/features/home/domain/repositories/home_repository.dart
import 'package:dartz/dartz.dart';
import 'package:oionovel/core/domain/entities/novel.dart';
import 'package:oionovel/core/errors/failure.dart';

abstract class HomeRepository {
  // ✅ Trả về Entity, không phải Model
  Future<Either<Failure, List<Novel>>> getHotNovels({
    String? location,
    int? limit,
    int? page,
  });

  Future<Either<Failure, List<BannerEntity>>> getBanners();
}
```

---

### 2️⃣ Data Layer (Implementation Details)

**Vai trò:** Chi tiết cài đặt (API, Database, Cache...)

```dart
data/
├── models/           // Data models với JSON serialization
│   ├── novel_detail_model.dart
│   └── banner_model.dart
├── mappers/          // Convert models ↔ entities
│   ├── novel_mapper.dart
│   └── banner_mapper.dart
└── repositories/     // Implement domain interfaces
    └── home_repository_impl.dart
```

**Đặc điểm:**
- ✅ Có JSON serialization (`.fromJson()`, `.toJson()`)
- ✅ Gọi API, database
- ✅ Import domain interfaces
- ✅ Dùng mapper để convert Model → Entity
- ❌ KHÔNG chứa business logic
- ❌ KHÔNG có getter tính toán (để trong Entity)

**Ví dụ Model (DTO thuần túy):**

```dart
// ✅ ĐÚNG - lib/core/data/models/novel_detail_model.dart
class NovelDetailModel {
  final String id;
  final String title;
  final String coverImage;
  final List<TagModel> tags;

  NovelDetailModel({
    required this.id,
    required this.title,
    required this.coverImage,
    required this.tags,
  });

  // ✅ CHỈ chứa JSON serialization
  factory NovelDetailModel.fromJson(Map<String, dynamic> json) {
    return NovelDetailModel(
      id: json['id'] as String,
      title: json['title'] as String,
      coverImage: json['coverImage'] as String? ?? '',
      tags: (json['tags'] as List<dynamic>?)
          ?.map((tag) => TagModel.fromJson(tag as Map<String, dynamic>))
          .toList() ?? [],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'coverImage': coverImage,
      'tags': tags.map((tag) => tag.toJson()).toList(),
    };
  }

  static List<NovelDetailModel> fromJsonList(List<dynamic> jsonList) {
    return jsonList
        .map((json) => NovelDetailModel.fromJson(json as Map<String, dynamic>))
        .toList();
  }
}
```

```dart
// ❌ SAI - Model KHÔNG NÊN chứa business logic
class NovelDetailModel {
  final String coverImage;

  // ❌ Business logic phải ở Entity, không phải Model
  String get fullImageUrl {
    if (coverImage.startsWith('http')) {
      return coverImage;
    }
    return '${AppUrl.urlImage}$coverImage';
  }
}
```

**Ví dụ Mapper:**

```dart
// ✅ ĐÚNG - lib/core/data/mappers/novel_mapper.dart
import 'package:oionovel/core/data/models/novel_detail_model.dart';
import 'package:oionovel/core/domain/entities/novel.dart';

class NovelMapper {
  /// Convert Model → Entity
  static Novel toEntity(NovelDetailModel model) {
    return Novel(
      id: model.id,
      title: model.title,
      coverImage: model.coverImage,
      tags: model.tags.map(tagToEntity).toList(),
    );
  }

  /// Convert Entity → Model (nếu cần)
  static NovelDetailModel fromEntity(Novel entity) {
    return NovelDetailModel(
      id: entity.id,
      title: entity.title,
      coverImage: entity.coverImage,
      tags: entity.tags.map(tagFromEntity).toList(),
    );
  }

  /// Convert list
  static List<Novel> toEntityList(List<NovelDetailModel> models) {
    return models.map(toEntity).toList();
  }

  /// Helper: Convert TagModel → Tag entity
  static Tag tagToEntity(TagModel model) {
    return Tag(
      id: model.id,
      name: model.name,
      index: model.index,
      novelLength: model.novelLength,
    );
  }
}
```

**Ví dụ Repository Implementation:**

```dart
// ✅ ĐÚNG - lib/features/home/data/repositories/home_repository_impl.dart
import 'package:dartz/dartz.dart';
import 'package:oionovel/core/data/mappers/novel_mapper.dart';
import 'package:oionovel/core/data/models/novel_detail_model.dart';
import 'package:oionovel/core/domain/entities/novel.dart';
import 'package:oionovel/features/home/domain/repositories/home_repository.dart';

class HomeRepositoryImpl implements HomeRepository {
  final ApiService _apiService;

  HomeRepositoryImpl(this._apiService);

  @override
  Future<Either<Failure, List<Novel>>> getHotNovels({
    String? location,
    int? limit,
    int? page,
  }) async {
    try {
      // 1. Gọi API
      final response = await _apiService.post<Map<String, dynamic>>(
        AppUrl.hotNovels,
        data: {'location': location, 'limit': limit, 'page': page},
      );

      if (response['success'] == true && response['data'] != null) {
        final List<dynamic> data = response['data'] as List<dynamic>;

        // 2. Parse JSON → Model
        final models = NovelDetailModel.fromJsonList(data);

        // 3. Map Model → Entity ✅ QUAN TRỌNG!
        final entities = NovelMapper.toEntityList(models);

        // 4. Trả về Entity
        return Right(entities);
      }

      return Left(ServerFailure(message: 'Unknown error'));
    } on Exception catch (e) {
      return Left(ServerFailure(message: e.toString()));
    }
  }
}
```

```dart
// ❌ SAI - Repository KHÔNG được trả về Model
class HomeRepositoryImpl implements HomeRepository {
  @override
  Future<Either<Failure, List<NovelDetailModel>>> getHotNovels() async {
    // ❌ Trả về Model thay vì Entity
    final models = NovelDetailModel.fromJsonList(data);
    return Right(models); // ❌ SAI!
  }
}
```

---

### 3️⃣ Presentation Layer (UI)

**Vai trò:** Hiển thị và tương tác với user

```dart
presentation/
├── controllers/      // State management (GetX, Bloc...)
│   └── home_controller.dart
├── screens/         // Pages
│   └── home_screen.dart
└── widgets/         // Reusable UI components
    └── banner_carousel.dart
```

**Đặc điểm:**
- ✅ Import domain (entities, usecases, repositories)
- ✅ Sử dụng entities
- ❌ KHÔNG import `data/models/`
- ❌ KHÔNG gọi API trực tiếp
- ❌ KHÔNG có mapper logic

**Ví dụ Controller:**

```dart
// ✅ ĐÚNG - lib/features/home/presentation/controllers/home_controller.dart
import 'package:get/get.dart';
import 'package:oionovel/core/domain/entities/novel.dart';
import 'package:oionovel/features/home/domain/entities/banner.dart';
import 'package:oionovel/features/home/domain/repositories/home_repository.dart';

class HomeController extends GetxController {
  final HomeRepository _homeRepository;

  HomeController(this._homeRepository);

  // ✅ Sử dụng Entity, không phải Model
  final RxList<Novel> _hotNovels = <Novel>[].obs;
  final RxList<BannerEntity> _banners = <BannerEntity>[].obs;

  // ✅ Getter trả về Entity
  List<Novel> get hotNovels => _hotNovels;
  List<BannerEntity> get banners => _banners;

  Future<void> _loadHotNovels() async {
    final result = await _homeRepository.getHotNovels(
      location: 'home-box',
      limit: 10,
    );

    result.fold(
      (failure) => _hotNovels.clear(),
      (novels) => _hotNovels.assignAll(novels), // ✅ Nhận Entity
    );
  }
}
```

```dart
// ❌ SAI - Controller import từ Data layer
import 'package:oionovel/core/data/models/novel_detail_model.dart'; // ❌
import 'package:oionovel/core/network/api_service.dart'; // ❌

class HomeController extends GetxController {
  final ApiService _api; // ❌ Gọi API trực tiếp

  // ❌ Sử dụng Model thay vì Entity
  final RxList<NovelDetailModel> _hotNovels = <NovelDetailModel>[].obs;

  Future<void> loadHotNovels() async {
    // ❌ Gọi API trực tiếp
    final response = await _api.get('/hot-novels');
    final models = NovelDetailModel.fromJsonList(response.data);
    _hotNovels.assignAll(models);
  }
}
```

**Ví dụ Widget:**

```dart
// ✅ ĐÚNG - lib/features/home/presentation/widgets/banner_carousel.dart
import 'package:flutter/material.dart';
import 'package:oionovel/features/home/domain/entities/banner.dart';

class BannerCarousel extends StatelessWidget {
  final List<BannerEntity> banners; // ✅ Nhận Entity

  const BannerCarousel({required this.banners});

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      itemCount: banners.length,
      itemBuilder: (context, index) {
        final banner = banners[index];
        return Image.network(
          banner.fullImageUrl, // ✅ Dùng business logic từ Entity
        );
      },
    );
  }
}
```

---

## ⚠️ SEPARATION OF CONCERNS (Tách biệt trách nhiệm)

### Nguyên tắc: Mỗi layer chỉ lo việc của mình

#### Data Models (DTO - Data Transfer Objects)
**Chỉ lo:** Serialization/Deserialization

```dart
// ✅ ĐÚNG - Model thuần túy
class NovelDetailModel {
  final String id;
  final String title;

  // ✅ CHỈ có JSON logic
  factory NovelDetailModel.fromJson(Map<String, dynamic> json) {
    return NovelDetailModel(
      id: json['id'] as String,
      title: json['title'] as String,
    );
  }

  Map<String, dynamic> toJson() => {'id': id, 'title': title};
}
```

#### Domain Entities (Business Objects)
**Lo:** Business logic, validation, computed properties

```dart
// ✅ ĐÚNG - Entity chứa business logic
class Novel {
  final String id;
  final String title;
  final String coverImage;

  Novel({
    required this.id,
    required this.title,
    required this.coverImage,
  });

  // ✅ Business logic: tạo URL đầy đủ
  String get fullImageUrl {
    if (coverImage.startsWith('http')) {
      return coverImage;
    }
    return '${AppUrl.urlImage}$coverImage';
  }

  // ✅ Business logic: validation
  bool get isValid => title.isNotEmpty && id.isNotEmpty;
}
```

---

## ❌ CÁC VI PHẠM PHỔ BIẾN

### 1. Model chứa Business Logic

```dart
// ❌ SAI - lib/core/data/models/novel_detail_model.dart
import 'package:oionovel/core/constants/app_url.dart'; // ❌

class NovelDetailModel {
  final String coverImage;

  // ❌ Business logic ở Model - VI PHẠM!
  String get fullImageUrl {
    if (coverImage.startsWith('http')) {
      return coverImage;
    }
    return '${AppUrl.urlImage}$coverImage';
  }

  factory NovelDetailModel.fromJson(Map<String, dynamic> json) {
    // JSON logic...
  }
}
```

**Sửa:**
```dart
// ✅ ĐÚNG - Model chỉ lo JSON
class NovelDetailModel {
  final String coverImage;

  // ❌ XÓA getter fullImageUrl

  factory NovelDetailModel.fromJson(Map<String, dynamic> json) {
    return NovelDetailModel(
      coverImage: json['coverImage'] as String? ?? '',
    );
  }
}

// ✅ ĐÚNG - Business logic ở Entity
class Novel {
  final String coverImage;

  // ✅ Business logic ở đây
  String get fullImageUrl {
    if (coverImage.startsWith('http')) {
      return coverImage;
    }
    return '${AppUrl.urlImage}$coverImage';
  }
}
```

---

### 2. Entity có JSON Serialization

```dart
// ❌ SAI - lib/core/domain/entities/novel.dart
class Novel {
  String? id;
  String? title;

  // ❌ Entity KHÔNG được có fromJson
  Novel.fromJson(Map<String, dynamic> json) {
    id = json['id'];
    title = json['title'];
  }

  // ❌ Entity KHÔNG được có toJson
  Map<String, dynamic> toJson() => {
    'id': id,
    'title': title,
  };
}
```

**Sửa:**
```dart
// ✅ ĐÚNG - Entity thuần túy
class Novel {
  final String id;
  final String title;

  Novel({
    required this.id,
    required this.title,
  });

  // ✅ CHỈ có business logic
  bool get isValid => title.isNotEmpty;
}
```

---

### 3. Presentation import Data

```dart
// ❌ SAI - lib/features/home/presentation/controllers/home_controller.dart
import 'package:oionovel/core/data/models/novel_detail_model.dart'; // ❌

class HomeController extends GetxController {
  // ❌ Dùng Model
  final RxList<NovelDetailModel> _novels = <NovelDetailModel>[].obs;

  List<NovelDetailModel> get novels => _novels; // ❌
}
```

**Sửa:**
```dart
// ✅ ĐÚNG
import 'package:oionovel/core/domain/entities/novel.dart'; // ✅

class HomeController extends GetxController {
  // ✅ Dùng Entity
  final RxList<Novel> _novels = <Novel>[].obs;

  List<Novel> get novels => _novels; // ✅
}
```

---

### 4. Repository trả về Model

```dart
// ❌ SAI - lib/features/home/data/repositories/home_repository_impl.dart
class HomeRepositoryImpl implements HomeRepository {
  @override
  Future<Either<Failure, List<NovelDetailModel>>> getHotNovels() async {
    final response = await _apiService.get('/hot-novels');
    final models = NovelDetailModel.fromJsonList(response.data);

    // ❌ Trả về Model - VI PHẠM!
    return Right(models);
  }
}
```

**Sửa:**
```dart
// ✅ ĐÚNG
class HomeRepositoryImpl implements HomeRepository {
  @override
  Future<Either<Failure, List<Novel>>> getHotNovels() async {
    final response = await _apiService.get('/hot-novels');

    // 1. Parse JSON → Model
    final models = NovelDetailModel.fromJsonList(response.data);

    // 2. Map Model → Entity ✅
    final entities = NovelMapper.toEntityList(models);

    // 3. Trả về Entity ✅
    return Right(entities);
  }
}
```

---

### 5. Domain import Data hoặc Presentation

```dart
// ❌ SAI - lib/features/home/domain/repositories/home_repository.dart
import 'package:oionovel/core/data/models/novel_detail_model.dart'; // ❌

abstract class HomeRepository {
  Future<List<NovelDetailModel>> getHotNovels(); // ❌ Model
}
```

**Sửa:**
```dart
// ✅ ĐÚNG
import 'package:oionovel/core/domain/entities/novel.dart'; // ✅

abstract class HomeRepository {
  Future<Either<Failure, List<Novel>>> getHotNovels(); // ✅ Entity
}
```

---

## ✅ CHECKLIST KIỂM TRA

### Domain Layer ✅
- [ ] Không có import từ `data/` hoặc `presentation/`
- [ ] Entities KHÔNG có `.fromJson()` hoặc `.toJson()`
- [ ] Entities CHỈ chứa business logic
- [ ] Repository interfaces trả về entities, không phải models
- [ ] UseCases trả về entities, không phải models

### Data Layer ✅
- [ ] Models CHỈ có JSON serialization (`.fromJson()`, `.toJson()`)
- [ ] Models KHÔNG chứa business logic (getter tính toán, validation...)
- [ ] Repository implementations sử dụng mapper
- [ ] Mapper convert: Model → Entity và Entity → Model
- [ ] Repository implementation trả về Entity (sau khi map)

### Presentation Layer ✅
- [ ] Controllers import domain, KHÔNG import data/models
- [ ] Controllers dùng entities, KHÔNG dùng models
- [ ] Widgets nhận entities, KHÔNG nhận models
- [ ] Controllers gọi repository/usecase, KHÔNG gọi API trực tiếp

---

## 🔍 COMMAND KIỂM TRA

```bash
# 1. Kiểm tra Domain có import Data không
grep -r "import.*data/" lib/features/*/domain/
grep -r "import.*data/" lib/core/domain/

# 2. Kiểm tra Presentation có import Data/Models không
grep -r "import.*data/models/" lib/features/*/presentation/

# 3. Kiểm tra Entity có JSON serialization không
grep -r "fromJson\|toJson" lib/features/*/domain/entities/
grep -r "fromJson\|toJson" lib/core/domain/entities/

# ✅ Không có kết quả = ĐÚNG
# ❌ Có kết quả = VI PHẠM Clean Architecture
```

---

## 📊 FLOW CHUẨN

### Luồng dữ liệu: API → Model → Entity → UI

```
┌─────────┐      ┌──────────┐      ┌────────┐      ┌──────────┐      ┌────┐
│   API   │ JSON │  Model   │ Map  │ Entity │ Use  │Controller│ Show │ UI │
│ Response├─────→│ (Data)   ├─────→│(Domain)├─────→│  (Pres)  ├─────→│    │
└─────────┘      └──────────┘      └────────┘      └──────────┘      └────┘
                      ↑                  ↑                ↑
                 fromJson()         Mapper          Repository
```

### Ví dụ Flow thực tế:

```dart
// 1. API trả về JSON
{
  "id": "123",
  "title": "Novel Title",
  "coverImage": "/images/cover.jpg",
  "tags": [{"id": "1", "name": "Action"}]
}

// 2. Parse JSON → Model (Data Layer)
final model = NovelDetailModel.fromJson(jsonData);
// model.coverImage = "/images/cover.jpg"

// 3. Map Model → Entity (Data Layer)
final entity = NovelMapper.toEntity(model);
// entity.coverImage = "/images/cover.jpg"
// entity.fullImageUrl = "https://api.com/images/cover.jpg" ✅ Business logic

// 4. Repository trả về Entity
return Right(entity);

// 5. Controller nhận Entity (Presentation Layer)
_novels.assignAll(entities);

// 6. UI hiển thị
Image.network(novel.fullImageUrl) // ✅ Dùng business logic
```

---

## 🎓 CÁC CÂU HỎI THƯỜNG GẶP

### Q1: Tại sao phải tách Model và Entity?

**A:**
- **Model** (Data) thay đổi theo API format → dễ bị thay đổi
- **Entity** (Domain) là business logic → ổn định, không đổi
- Khi API thay đổi, chỉ sửa Model và Mapper, Entity không đổi
- Entity có thể tái sử dụng cho nhiều data source (API, Database, Cache)

### Q2: Mapper có cần thiết không? Có thể skip không?

**A:** KHÔNG thể skip! Mapper là cầu nối bắt buộc:
- ✅ Tách biệt rõ ràng Data ↔ Domain
- ✅ API thay đổi chỉ sửa Mapper
- ✅ Dễ test riêng từng phần

### Q3: Business logic nên ở đâu?

**A:**
- ✅ **Entity** (Domain): Logic nghiệp vụ (fullImageUrl, validation, computed properties)
- ✅ **UseCase** (Domain): Logic use case (login flow, checkout flow)
- ❌ **Model** (Data): KHÔNG - chỉ JSON serialization
- ❌ **Controller** (Presentation): KHÔNG - chỉ UI state

### Q4: Khi nào cần UseCase?

**A:**
- ✅ CẦN: Logic phức tạp (kết hợp nhiều repository, business rules)
- ✅ CẦN: Để test dễ hơn
- ⚠️ KHÔNG BẮT BUỘC: CRUD đơn giản (có thể gọi repository trực tiếp)

---

## 📚 TÓM TẮT NHANH

| Layer | Chứa | KHÔNG chứa | Return type | Import |
|-------|------|------------|-------------|---------|
| **Domain** | Business logic, Interfaces | JSON, API, DB | Entities | Chỉ domain |
| **Data** | JSON, API, DB, Mapper | Business logic | Entities (sau map) | Domain interfaces |
| **Presentation** | UI logic, State | Business logic, API | - | Domain only |

### Rule of Thumb:

1. **Entity** = Business object thuần túy + business logic
2. **Model** = DTO thuần túy (chỉ JSON)
3. **Mapper** = Bridge giữa Model và Entity
4. **Repository Implementation** = Luôn map Model → Entity trước khi return
5. **Presentation** = Chỉ biết Entity, không biết Model

---

## 🚀 HÀNH ĐỘNG KHI REFACTOR

### Bước 1: Xác định vi phạm
```bash
# Tìm Model có business logic
grep -A 10 "get.*{" lib/*/data/models/*.dart

# Tìm Entity có JSON
grep "fromJson\|toJson" lib/*/domain/entities/*.dart
```

### Bước 2: Tạo Entity thuần túy
```dart
// Chuyển business logic từ Model sang Entity
class Novel {
  final String coverImage;

  String get fullImageUrl {
    // Business logic ở đây
  }
}
```

### Bước 3: Làm sạch Model
```dart
// Xóa hết business logic, chỉ giữ JSON
class NovelDetailModel {
  final String coverImage;

  factory NovelDetailModel.fromJson(...) { }
  Map<String, dynamic> toJson() { }
}
```

### Bước 4: Tạo Mapper
```dart
class NovelMapper {
  static Novel toEntity(NovelDetailModel model) { }
  static List<Novel> toEntityList(...) { }
}
```

### Bước 5: Cập nhật Repository Implementation
```dart
// Thêm mapper vào repository
final models = NovelDetailModel.fromJsonList(data);
final entities = NovelMapper.toEntityList(models); // ✅
return Right(entities);
```

### Bước 6: Cập nhật Presentation
```dart
// Đổi từ Model sang Entity
final RxList<Novel> _novels = <Novel>[].obs; // ✅
```

---

## 💡 NGUYÊN TẮC VÀNG

> 1. **Domain** = Trung tâm của mọi thứ, không phụ thuộc ai
> 2. **Model** = CHỈ biết JSON, không biết business
> 3. **Entity** = CHỈ biết business, không biết JSON
> 4. **Mapper** = Cầu nối bắt buộc giữa Model và Entity
> 5. **Repository** = Luôn trả về Entity, không bao giờ trả về Model
> 6. **Presentation** = Chỉ biết Entity, quên luôn Model tồn tại

---

**Remember:**

> "Clean Architecture không phải là về code nhiều hơn.
> Nó là về code dễ maintain, dễ test, và dễ scale hơn!"

---

**Generated by:** Claude Code
**Date:** 2025-01-19
**Version:** 2.0 - Updated with real-world examples from oioNovel project
