import 'package:flutter/material.dart';
import 'package:student_agent/core/theme/app_theme.dart';

// ── Helper ──
DateTime parseServerTime(dynamic raw) {
  if (raw == null) return DateTime.now();
  final s = raw.toString();
  final hasTz = RegExp(r'[zZ]|[+-]\d\d:?\d\d$').hasMatch(s);
  try {
    return DateTime.parse(hasTz ? s : '${s}Z').toLocal();
  } catch (_) {
    return DateTime.now();
  }
}

// ── Enums ──
enum GroupMessageType { text, image, file, system, document }

enum GroupResourceType { document, link, image, video }

extension GroupMessageTypeExt on GroupMessageType {
  String get apiValue {
    switch (this) {
      case GroupMessageType.image:
        return 'image';
      case GroupMessageType.file:
        return 'file';
      case GroupMessageType.system:
        return 'system';
      case GroupMessageType.document:
        return 'document';
      default:
        return 'text';
    }
  }

  static GroupMessageType fromApi(String? value) {
    switch (value?.toLowerCase()) {
      case 'image':
        return GroupMessageType.image;
      case 'file':
        return GroupMessageType.file;
      case 'system':
        return GroupMessageType.system;
      case 'document':
        return GroupMessageType.document;
      default:
        return GroupMessageType.text;
    }
  }

  static GroupMessageType fromString(String value) {
    return fromApi(value);
  }
}

extension GroupResourceTypeExt on GroupResourceType {
  String get apiValue {
    switch (this) {
      case GroupResourceType.link:
        return 'link';
      case GroupResourceType.image:
        return 'image';
      case GroupResourceType.video:
        return 'video';
      default:
        return 'document';
    }
  }

  static GroupResourceType fromApi(String? value) {
    switch (value?.toLowerCase()) {
      case 'link':
        return GroupResourceType.link;
      case 'image':
        return GroupResourceType.image;
      case 'video':
        return GroupResourceType.video;
      default:
        return GroupResourceType.document;
    }
  }

  IconData get icon {
    switch (this) {
      case GroupResourceType.link:
        return Icons.link_rounded;
      case GroupResourceType.image:
        return Icons.image_rounded;
      case GroupResourceType.video:
        return Icons.video_library_rounded;
      default:
        return Icons.description_rounded;
    }
  }

  Color get color {
    switch (this) {
      case GroupResourceType.link:
        return AppTheme.primaryBlue;
      case GroupResourceType.image:
        return AppTheme.accentGreen;
      case GroupResourceType.video:
        return AppTheme.danger;
      default:
        return AppTheme.warning;
    }
  }

  String get label {
    switch (this) {
      case GroupResourceType.link:
        return 'Liên kết';
      case GroupResourceType.image:
        return 'Hình ảnh';
      case GroupResourceType.video:
        return 'Video';
      default:
        return 'Tài liệu';
    }
  }
}

// ── Group Message ──
class GroupMessage {
  final String id;
  final String groupId;
  final String senderId;
  final String senderName;
  final String content;
  final String? fileUrl;
  final GroupMessageType type;
  final DateTime timestamp;
  final bool isRead;
  final String? fileName;      // Tên file
  final int? fileSize;         // Kích thước file (bytes)
  final String? fileType;      // Loại file (pdf, doc, xlsx, ...)

  GroupMessage({
    required this.id,
    required this.groupId,
    required this.senderId,
    required this.senderName,
    required this.content,
    this.fileUrl,
    this.type = GroupMessageType.text,
    required this.timestamp,
    this.isRead = false,
    this.fileName,
    this.fileSize,
    this.fileType,
  });

  factory GroupMessage.fromJson(Map<String, dynamic> json) => GroupMessage(
        id: json['_id'] ?? json['id'] ?? '',
        groupId: json['group_id'] ?? '',
        senderId: json['sender_id']?.toString() ?? '',
        senderName: json['sender_name'] ?? '',
        content: json['content'] ?? '',
        fileUrl: json['file_url'],
        type: GroupMessageTypeExt.fromApi(json['type']),
        timestamp: parseServerTime(json['timestamp']),
        isRead: json['is_read'] ?? false,
        fileName: json['file_name'],
        fileSize: json['file_size'],
        fileType: json['file_type'],
      );

  Map<String, dynamic> toJson() => {
        'group_id': groupId,
        'sender_id': senderId,
        'sender_name': senderName,
        'content': content,
        'file_url': fileUrl,
        'type': type.apiValue,
        'timestamp': timestamp.toIso8601String(),
        'is_read': isRead,
        'file_name': fileName,
        'file_size': fileSize,
        'file_type': fileType,
      };
}

// ── Group Resource ──
class GroupResource {
  final String id;
  final String groupId;
  final String title;
  final GroupResourceType type;
  final String url;
  final String uploadedBy;
  final DateTime uploadedAt;

  GroupResource({
    required this.id,
    required this.groupId,
    required this.title,
    required this.type,
    required this.url,
    required this.uploadedBy,
    required this.uploadedAt,
  });

  factory GroupResource.fromJson(Map<String, dynamic> json) => GroupResource(
        id: json['_id'] ?? json['id'] ?? '',
        groupId: json['group_id'] ?? '',
        title: json['title'] ?? '',
        type: GroupResourceTypeExt.fromApi(json['type']),
        url: json['url'] ?? '',
        uploadedBy: json['uploaded_by']?.toString() ?? '',
        uploadedAt: parseServerTime(json['uploaded_at']),
      );

  Map<String, dynamic> toJson() => {
        'title': title,
        'type': type.apiValue,
        'url': url,
        'uploaded_by': uploadedBy,
        'uploaded_at': uploadedAt.toIso8601String(),
      };
}

// ── Study Group ──
class StudyGroup {
  final String id;
  final String groupCode;
  final String name;
  final String description;
  final String createdBy;
  final List<String> members;
  final List<GroupMessage> messages;
  final List<GroupResource> resources;
  final DateTime createdAt;
  final DateTime? lastActiveAt;
  final int? memberCount;

  StudyGroup({
    required this.id,
    required this.groupCode,
    required this.name,
    required this.description,
    required this.createdBy,
    required this.members,
    this.messages = const [],
    this.resources = const [],
    required this.createdAt,
    this.lastActiveAt,
    this.memberCount,
  });


  factory StudyGroup.fromJson(Map<String, dynamic> json) {
    print('📥 StudyGroup.fromJson: ${json.keys}');
    print('📥 members: ${json['members']} (${json['members'].runtimeType})');
    print('📥 member_count: ${json['member_count']} (${json['member_count'].runtimeType})');
    
    return StudyGroup(
      id: json['_id']?.toString() ?? json['id']?.toString() ?? '',
      groupCode: json['group_code']?.toString() ?? '',
      name: json['name']?.toString() ?? '',
      description: json['description']?.toString() ?? '',
      createdBy: json['created_by']?.toString() ?? '',
      members: (json['members'] as List?)?.map((e) => e?.toString() ?? '').toList() ?? [],
      messages: (json['messages'] as List? ?? [])
          .map((m) => GroupMessage.fromJson(m as Map<String, dynamic>))
          .toList(),
      resources: (json['resources'] as List? ?? [])
          .map((r) => GroupResource.fromJson(r as Map<String, dynamic>))
          .toList(),
      createdAt: parseServerTime(json['created_at']),
      lastActiveAt: json['last_active_at'] != null ? parseServerTime(json['last_active_at']) : null,
      memberCount: json['member_count'] is int 
          ? json['member_count'] as int 
          : int.tryParse(json['member_count']?.toString() ?? '0'),
    );
  }

  Map<String, dynamic> toJson() => {
        'group_code': groupCode,
        'name': name,
        'description': description,
        'created_by': createdBy,
        'members': members,
        'created_at': createdAt.toIso8601String(),
        'last_active_at': lastActiveAt?.toIso8601String(),
      };

  int get totalMembers => memberCount ?? members.length;
  bool isCreator(String studentId) => createdBy == studentId;
  bool isMember(String studentId) => members.contains(studentId);
}