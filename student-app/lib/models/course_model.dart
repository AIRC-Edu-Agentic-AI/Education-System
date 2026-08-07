import 'package:student_agent/models/student_model.dart';

class CourseModel {
  final String id;
  final String courseCode;
  final String title;
  final String presentation;
  final String term;
  final List<int> instructors;
  final List<int> classReps;
  final List<int> members;
  final String status;
  final Map<String, dynamic> settings;
  final DateTime createdAt;
  final DateTime updatedAt;
  final DateTime? archivedAt;
  final DateTime? retentionExpiresAt;

  CourseModel({
    required this.id,
    required this.courseCode,
    required this.title,
    required this.presentation,
    required this.term,
    required this.instructors,
    required this.classReps,
    required this.members,
    required this.status,
    required this.settings,
    required this.createdAt,
    required this.updatedAt,
    this.archivedAt,
    this.retentionExpiresAt,
  });

  factory CourseModel.fromJson(Map<String, dynamic> json) => CourseModel(
        id: json['_id']?.toString() ?? '',
        courseCode: json['course_code'] ?? '',
        title: json['title'] ?? '',
        presentation: json['presentation'] ?? '',
        term: json['term'] ?? '',
        instructors: List<int>.from(json['instructors'] ?? []),
        classReps: List<int>.from(json['class_reps'] ?? []),
        members: List<int>.from(json['members'] ?? []),
        status: json['status'] ?? '',
        settings: Map<String, dynamic>.from(json['settings'] ?? {}),
        createdAt: parseServerTime(json['created_at']),
        updatedAt: parseServerTime(json['updated_at']),
        archivedAt: json['archived_at'] != null ? parseServerTime(json['archived_at']) : null,
        retentionExpiresAt: json['retention_expires_at'] != null
            ? parseServerTime(json['retention_expires_at'])
            : null,
      );

  String get displayName => title.isNotEmpty ? title : courseCode;
}

class CourseChannel {
  final String id;
  final String courseCode;
  final String type;
  final String name;
  final bool isReadOnly;
  final List<String> allowedPostRoles;
  final String status;
  final DateTime createdAt;
  final DateTime updatedAt;

  CourseChannel({
    required this.id,
    required this.courseCode,
    required this.type,
    required this.name,
    required this.isReadOnly,
    required this.allowedPostRoles,
    required this.status,
    required this.createdAt,
    required this.updatedAt,
  });

  factory CourseChannel.fromJson(Map<String, dynamic> json) => CourseChannel(
        id: json['_id']?.toString() ?? '',
        courseCode: json['course_code'] ?? '',
        type: json['type'] ?? '',
        name: json['name'] ?? '',
        isReadOnly: json['is_read_only'] ?? false,
        allowedPostRoles: List<String>.from(json['allowed_post_roles'] ?? []),
        status: json['status'] ?? '',
        createdAt: parseServerTime(json['created_at']),
        updatedAt: parseServerTime(json['updated_at']),
      );
}

class CourseMessageReaction {
  final int userId;
  final String emoji;
  final DateTime createdAt;

  const CourseMessageReaction({
    required this.userId,
    required this.emoji,
    required this.createdAt,
  });

  factory CourseMessageReaction.fromJson(Map<String, dynamic> json) => CourseMessageReaction(
        userId: json['user_id'] ?? 0,
        emoji: json['emoji'] ?? '',
        createdAt: parseServerTime(json['created_at']),
      );
}

class CourseMessage {
  final String id;
  final String channelId;
  final String courseCode;
  final dynamic senderId;
  final String senderRole;
  final String content;
  final DateTime createdAt;
  final String? parentId;
  final String? channelType;
  final List<CourseMessageReaction> reactions;

  CourseMessage({
    required this.id,
    required this.channelId,
    required this.courseCode,
    required this.senderId,
    required this.senderRole,
    required this.content,
    required this.createdAt,
    this.parentId,
    this.channelType,
    this.reactions = const [],
  });

  factory CourseMessage.fromJson(Map<String, dynamic> json) {
    final rawSenderId = json['sender_id'] ?? json['senderId'];
    dynamic parsedSenderId = rawSenderId;
    if (rawSenderId != null) {
      if (rawSenderId is int) {
        parsedSenderId = rawSenderId;
      } else if (rawSenderId is String) {
        parsedSenderId = int.tryParse(rawSenderId) ?? rawSenderId;
      }
    } else {
      parsedSenderId = 0;
    }

    return CourseMessage(
      id: json['_id']?.toString() ?? json['id']?.toString() ?? '',
      channelId: json['channel_id']?.toString() ?? '',
      courseCode: json['course_code'] ?? '',
      senderId: parsedSenderId,
      senderRole: json['sender_role'] ?? json['senderRole'] ?? '',
      content: json['content'] ?? '',
      createdAt: parseServerTime(json['created_at'] ?? json['createdAt']),
      parentId: json['parent_id']?.toString(),
      channelType: json['channel_type']?.toString(),
      reactions: (json['reactions'] as List? ?? [])
          .map((r) => CourseMessageReaction.fromJson(Map<String, dynamic>.from(r)))
          .toList(),
    );
  }
}
