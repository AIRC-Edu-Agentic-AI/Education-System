import 'dart:io';
import 'package:dio/dio.dart';
import 'package:path_provider/path_provider.dart';  // ⭐ THÊM IMPORT NÀY
import 'package:student_agent/core/config/env_config.dart';
import 'package:student_agent/models/study_group_model.dart';

class StudyGroupService {
  final Dio _dio;

  StudyGroupService({Dio? dio})
      : _dio = dio ?? Dio(
          BaseOptions(
            baseUrl: EnvConfig.apiBaseUrl,
            connectTimeout: const Duration(seconds: 10),
            receiveTimeout: const Duration(seconds: 30),
            headers: {'Content-Type': 'application/json'},
          ),
        );

  // ── Group CRUD ──

  Future<StudyGroup> createGroup({
    required int studentId,
    required String name,
    String description = '',
  }) async {
    try {
      final response = await _dio.post(
        '/study-groups/create',
        queryParameters: {'student_id': studentId},
        data: {
          'name': name,
          'description': description,
        },
      );
      return StudyGroup.fromJson(response.data);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  Future<StudyGroup> joinGroup({
    required int studentId,
    required String groupCode,
  }) async {
    try {
      final response = await _dio.post(
        '/study-groups/join',
        queryParameters: {'student_id': studentId},
        data: {'group_code': groupCode},
      );
      return StudyGroup.fromJson(response.data);
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) {
        throw Exception('Không tìm thấy nhóm với mã này');
      }
      throw _handleError(e);
    }
  }

  Future<List<StudyGroup>> getMyGroups(int studentId) async {
    try {
      final response = await _dio.get(
        '/study-groups/my-groups',
        queryParameters: {'student_id': studentId},
      );
      print('📥 API Response: ${response.data}');  // ⭐ THÊM DÒNG NÀY
      return (response.data as List)
          .map((g) => StudyGroup.fromJson(g))
          .toList();
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  Future<StudyGroup> getGroupDetail({
    required String groupId,
    required int studentId,
  }) async {
    try {
      final response = await _dio.get(
        '/study-groups/$groupId',
        queryParameters: {'student_id': studentId},
      );
      return StudyGroup.fromJson(response.data);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  Future<void> leaveGroup({
    required String groupId,
    required int studentId,
  }) async {
    try {
      await _dio.delete(
        '/study-groups/$groupId/leave',
        queryParameters: {'student_id': studentId},
      );
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  // ── Messages ──

  // ── Gửi tin nhắn với file ──
Future<GroupMessage> sendMessage({
  required String groupId,
  required int studentId,
  required String content,
  String? fileUrl,
  String? fileName,
  int? fileSize,
  String? fileType,
  String type = 'text',  // ⭐ SỬA: dùng string thay vì enum
}) async {
  try {
    final response = await _dio.post(
      '/study-groups/$groupId/messages',
      queryParameters: {'student_id': studentId},
      data: {
        'content': content,
        'file_url': fileUrl,
        'file_name': fileName,
        'file_size': fileSize,
        'file_type': fileType,
         'type': type,  // ⭐ Gửi string trực tiếp
      },
    );
    return GroupMessage.fromJson(response.data);
  } on DioException catch (e) {
    throw Exception('Không thể gửi tin nhắn: ${e.message}');
  }
}

  Future<List<GroupMessage>> getMessages({
    required String groupId,
    required int studentId,
    int limit = 50,
    int offset = 0,
  }) async {
    try {
      final response = await _dio.get(
        '/study-groups/$groupId/messages',
        queryParameters: {
          'student_id': studentId,
          'limit': limit,
          'offset': offset,
        },
      );
      return (response.data as List)
          .map((m) => GroupMessage.fromJson(m))
          .toList();
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  // ── Resources ──

  Future<GroupResource> addResource({
    required String groupId,
    required int studentId,
    required String title,
    required GroupResourceType type,
    required String url,
  }) async {
    try {
      final response = await _dio.post(
        '/study-groups/$groupId/resources',
        queryParameters: {'student_id': studentId},
        data: {
          'title': title,
          'type': type.apiValue,
          'url': url,
        },
      );
      return GroupResource.fromJson(response.data);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  Future<List<GroupResource>> getResources({
    required String groupId,
    required int studentId,
  }) async {
    try {
      final response = await _dio.get(
        '/study-groups/$groupId/resources',
        queryParameters: {'student_id': studentId},
      );
      return (response.data as List)
          .map((r) => GroupResource.fromJson(r))
          .toList();
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  // ── Upload file ──

  Future<Map<String, dynamic>> uploadFile({
    required String groupId,
    required int studentId,
    required File file,
    required String fileName,
  }) async {
    try {
      final formData = FormData.fromMap({
        'file': await MultipartFile.fromFile(
          file.path,
          filename: fileName,
        ),
        'group_id': groupId,
        'student_id': studentId,
      });

      final response = await _dio.post(
        '/study-groups/$groupId/upload',
        data: formData,
        options: Options(
          headers: {'Content-Type': 'multipart/form-data'},
        ),
      );
      return Map<String, dynamic>.from(response.data);
    } on DioException catch (e) {
      throw Exception('Không thể upload file: ${e.message}');
    }
  }

  // ── Gửi tin nhắn với file ──

  Future<GroupMessage> sendMessageWithFile({
    required String groupId,
    required int studentId,
    required String content,
    String? fileUrl,
    String? fileName,
    int? fileSize,
    String? fileType,
    GroupMessageType type = GroupMessageType.document,
  }) async {
    try {
      final response = await _dio.post(
        '/study-groups/$groupId/messages',
        queryParameters: {'student_id': studentId},
        data: {
          'content': content,
          'file_url': fileUrl,
          'file_name': fileName,
          'file_size': fileSize,
          'file_type': fileType,
          'type': type.apiValue,
        },
      );
      return GroupMessage.fromJson(response.data);
    } on DioException catch (e) {
      throw Exception('Không thể gửi tin nhắn: ${e.message}');
    }
  }

  // ── Lấy danh sách file trong nhóm ──

  Future<List<Map<String, dynamic>>> getGroupFiles({
    required String groupId,
    required int studentId,
  }) async {
    try {
      final response = await _dio.get(
        '/study-groups/$groupId/files',
        queryParameters: {'student_id': studentId},
      );
      return List<Map<String, dynamic>>.from(response.data);
    } on DioException catch (_) {
      return [];
    }
  }

  // ── Tải file xuống ──

  Future<String> downloadFile({
    required String fileId,
    required String groupId,
    required int studentId,
  }) async {
    try {
      final response = await _dio.get(
        '/study-groups/$groupId/files/$fileId/download',
        queryParameters: {'student_id': studentId},
        options: Options(responseType: ResponseType.bytes),
      );
      
      // ⭐ SỬA: Sử dụng getApplicationDocumentsDirectory thay vì getDownloadsDirectory
      final directory = await getApplicationDocumentsDirectory();
      final filePath = '${directory.path}/$fileId';
      final file = File(filePath);
      await file.writeAsBytes(response.data as List<int>);
      return filePath;
    } on DioException catch (e) {
      throw Exception('Không thể tải file: ${e.message}');
    }
  }

  Exception _handleError(DioException e) {
    final message = e.response?.data?['detail'] ?? e.message ?? 'Unknown error';
    return Exception(message);
  }
}