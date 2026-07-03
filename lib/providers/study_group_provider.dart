import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:student_agent/core/config/env_config.dart';
import 'package:student_agent/data/services/study_group_service.dart';
import 'package:student_agent/models/study_group_model.dart';
import 'package:student_agent/providers/auth_provider.dart';

final studyGroupServiceProvider = Provider<StudyGroupService>((ref) {
  final token = ref.watch(authNotifierProvider).state.token;
  return StudyGroupService(
    dio: Dio(
      BaseOptions(
        baseUrl: EnvConfig.apiBaseUrl,
        headers: token != null ? {'Authorization': 'Bearer $token'} : {},
      ),
    ),
  );
});

// ── Active student ID ──
final activeStudentIdProvider = Provider<int>((ref) {
  return ref.watch(authNotifierProvider).state.studentId ?? 0;
});

// ── My Groups ──
final myGroupsProvider = FutureProvider<List<StudyGroup>>((ref) async {
  try {
    final service = ref.read(studyGroupServiceProvider);
    final studentId = ref.read(activeStudentIdProvider);
    print('🔍 Fetching groups for student: $studentId');
    
    if (studentId == 0) return [];
    
    final result = await service.getMyGroups(studentId);
    print('✅ Groups loaded: ${result.length}');
    print('📊 First group: ${result.isNotEmpty ? result.first.name : "none"}');
    return result;
  } catch (e, stacktrace) {
    print('❌ Error: $e');
    print('📚 Stacktrace: $stacktrace');
    return [];
  }
});

// ── Group Detail ──
final groupDetailProvider = FutureProvider.family<StudyGroup, String>(
    (ref, groupId) async {
  final service = ref.read(studyGroupServiceProvider);
  final studentId = ref.read(activeStudentIdProvider);
  if (studentId == 0) throw Exception('Not logged in');
  return service.getGroupDetail(groupId: groupId, studentId: studentId);
});

// ── Group Messages ──
final groupMessagesProvider = FutureProvider.family<List<GroupMessage>, String>(
    (ref, groupId) async {
  final service = ref.read(studyGroupServiceProvider);
  final studentId = ref.read(activeStudentIdProvider);
  if (studentId == 0) return [];
  return service.getMessages(groupId: groupId, studentId: studentId);
});

// ── Group Resources ──
final groupResourcesProvider = FutureProvider.family<List<GroupResource>, String>(
    (ref, groupId) async {
  final service = ref.read(studyGroupServiceProvider);
  final studentId = ref.read(activeStudentIdProvider);
  if (studentId == 0) return [];
  return service.getResources(groupId: groupId, studentId: studentId);
});

// ── Create Group ──
// lib/providers/study_group_provider.dart
final createGroupProvider = FutureProvider.family<StudyGroup, Map<String, dynamic>>(
    (ref, params) async {
  try {
    final service = ref.read(studyGroupServiceProvider);
    final studentId = ref.read(activeStudentIdProvider);
    print('🔍 Creating group for student: $studentId');
    
    if (studentId == 0) throw Exception('Not logged in');
    
    final result = await service.createGroup(
      studentId: studentId,
      name: params['name'] as String,
      description: params['description'] as String? ?? '',
    );
    
    print('✅ Group created successfully: ${result.id}');
    return result;
  } catch (e) {
    print('❌ Error in createGroupProvider: $e');
    throw Exception('Không thể tạo nhóm: $e');
  }
});

// ── Join Group ──
final joinGroupProvider = FutureProvider.family<StudyGroup, String>(
    (ref, groupCode) async {
  final service = ref.read(studyGroupServiceProvider);
  final studentId = ref.read(activeStudentIdProvider);
  if (studentId == 0) throw Exception('Not logged in');
  return service.joinGroup(studentId: studentId, groupCode: groupCode);
});

// ── Send Message ──
final sendGroupMessageProvider = FutureProvider.family<GroupMessage, Map<String, dynamic>>(
    (ref, params) async {
  final service = ref.read(studyGroupServiceProvider);
  final studentId = ref.read(activeStudentIdProvider);
  if (studentId == 0) throw Exception('Not logged in');
  
  // ⭐ SỬA: Xác định type dưới dạng String
  String typeStr = 'text';
  if (params['type'] is String) {
    typeStr = params['type'] as String;
  } else if (params['type'] is GroupMessageType) {
    typeStr = (params['type'] as GroupMessageType).apiValue;
  }
  
  return service.sendMessage(
    groupId: params['groupId'] as String,
    studentId: studentId,
    content: params['content'] as String,
    fileUrl: params['fileUrl'] as String?,
    fileName: params['fileName'] as String?,
    fileSize: params['fileSize'] as int?,
    fileType: params['fileType'] as String?,
    type: typeStr,  // ⭐ Truyền String
  );
});

// ── Add Resource ──
final addGroupResourceProvider = FutureProvider.family<GroupResource, Map<String, dynamic>>(
    (ref, params) async {
  final service = ref.read(studyGroupServiceProvider);
  final studentId = ref.read(activeStudentIdProvider);
  if (studentId == 0) throw Exception('Not logged in');
  return service.addResource(
    groupId: params['groupId'] as String,
    studentId: studentId,
    title: params['title'] as String,
    type: params['type'] as GroupResourceType,
    url: params['url'] as String,
  );
});

// ── Leave Group ──
final leaveGroupProvider = FutureProvider.family<void, String>((ref, groupId) async {
  final service = ref.read(studyGroupServiceProvider);
  final studentId = ref.read(activeStudentIdProvider);
  if (studentId == 0) throw Exception('Not logged in');
  await service.leaveGroup(groupId: groupId, studentId: studentId);
  ref.invalidate(myGroupsProvider);
});

