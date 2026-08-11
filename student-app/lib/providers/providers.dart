import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:collection/collection.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:student_agent/core/config/env_config.dart';
import 'package:student_agent/data/services/api_service.dart';
import 'package:student_agent/models/assignment_milestone_model.dart';
import 'package:student_agent/models/chat_message_model.dart';
import 'package:student_agent/models/course_model.dart';
import 'package:student_agent/models/student_model.dart';
import 'package:student_agent/providers/auth_provider.dart';

// ── API Service ───────────────────────────────────────────────────────────────
final apiServiceProvider = Provider<ApiService>((ref) {
  final token = ref.watch(authNotifierProvider).state.token;
  return ApiService(token: token);
});

// ── Active student ID (derived from auth session) ─────────────────────────────
final activeStudentIdProvider = Provider<int>((ref) {
  final sid = ref.watch(authNotifierProvider).state.studentId;
  return (sid != null && sid > 0) ? sid : 28400;
});

// ── Student profile ───────────────────────────────────────────────────────────
final studentProvider = FutureProvider<StudentModel>((ref) async {
  final api = ref.read(apiServiceProvider);
  final studentId = ref.watch(activeStudentIdProvider);
  return api.getStudent(studentId);
});

// ── Weekly schedule ───────────────────────────────────────────────────────────
final weeklyScheduleProvider = FutureProvider<WeeklySchedule>((ref) async {
  final api = ref.read(apiServiceProvider);
  final studentId = ref.watch(activeStudentIdProvider);
  return api.getWeeklySchedule(studentId);
});

// ── Notifications & Real-time Messages Stream ──────────────────────────────────
final newNotificationStreamController = StreamController<NotificationModel>.broadcast();
final newMessageStreamController = StreamController<CourseMessage>.broadcast();
class NotificationNotifier extends AsyncNotifier<List<NotificationModel>> {
  WebSocket? _socket;
  bool _isDisposed = false;

  @override
  Future<List<NotificationModel>> build() async {
    _isDisposed = false;
    ref.watch(activeStudentIdProvider);
    ref.onDispose(() {
      _isDisposed = true;
      _socket?.close();
    });
    final result = await _fetch();
    _connectWebSocket();
    return result;
  }

  static int _sortNotifications(NotificationModel a, NotificationModel b) {
    if (a.read != b.read) {
      return a.read ? 1 : -1;
    }
    return b.createdAt.compareTo(a.createdAt);
  }

  Future<List<NotificationModel>> _fetch() async {
    final api = ref.read(apiServiceProvider);
    final studentId = ref.read(activeStudentIdProvider);
    final raw = await api.getNotifications(studentId);
    final seen = <String>{};
    final unique = <NotificationModel>[];
    for (final item in raw) {
      final key = '${item.id}_${item.title}_${item.body}';
      if (!seen.contains(key)) {
        seen.add(key);
        unique.add(item);
      }
    }
    unique.sort(_sortNotifications);
    return unique;
  }

  void _connectWebSocket() async {
    if (_isDisposed) return;
    final studentId = ref.read(activeStudentIdProvider);
    try {
      final wsUrl = '${EnvConfig.wsBaseUrl}/realtime-chat/ws/$studentId';
      _socket = await WebSocket.connect(wsUrl);
      _socket?.listen(
        (message) {
          if (_isDisposed) return;
          try {
            final data = jsonDecode(message as String) as Map<String, dynamic>;
            final eventType = data['type'] as String?;

            if (eventType == 'new_notification' && data['notification'] != null) {
              final newNotif = NotificationModel.fromJson(Map<String, dynamic>.from(data['notification']));
              final current = state.value ?? [];
              final isDuplicate = current.any((n) =>
                n.id == newNotif.id || (n.title == newNotif.title && n.body == newNotif.body));
              if (!isDuplicate) {
                final updated = [newNotif, ...current];
                updated.sort(_sortNotifications);
                state = AsyncData(updated);
                newNotificationStreamController.add(newNotif);
              }
            } else if (eventType == 'notification_updated' && data['notification'] != null) {
              final updatedNotif = NotificationModel.fromJson(Map<String, dynamic>.from(data['notification']));
              final current = state.value ?? [];
              final updatedList = current.map((n) {
                if (n.id == updatedNotif.id ||
                    (data['title'] != null && n.title == data['title'])) {
                  return n.copyWith(
                    title: updatedNotif.title,
                    body: updatedNotif.body,
                  );
                }
                return n;
              }).toList();
              updatedList.sort(_sortNotifications);
              state = AsyncData(updatedList);
            } else if (eventType == 'notification_deleted') {
              final targetId = data['notification_id']?.toString();
              if (targetId == 'ALL') {
                state = const AsyncData([]);
                return;
              }
              final targetTitle = data['title']?.toString();
              final targetContent = data['content']?.toString();
              final current = state.value ?? [];
              final updatedList = current.where((n) {
                if (targetId != null && n.id == targetId) return false;
                if (targetTitle != null && (n.title == targetTitle || n.title.trim() == targetTitle.trim())) return false;
                if (targetContent != null && (n.body == targetContent || n.body.trim() == targetContent.trim())) return false;
                return true;
              }).toList();
              updatedList.sort(_sortNotifications);
              state = AsyncData(updatedList);
            } else if (eventType == 'new_message' && data['message'] != null) {
              final msgData = Map<String, dynamic>.from(data['message']);
              final msg = CourseMessage.fromJson(msgData);
              final activeStudentId = ref.read(activeStudentIdProvider).toString();
              if (msg.senderId.toString() != activeStudentId) {
                newMessageStreamController.add(msg);
              }
              ref.invalidate(channelThreadMessagesProvider(ChannelMessagesArgs(channelId: msg.channelId)));
              ref.invalidate(channelThreadMessagesProvider(ChannelMessagesArgs(channelId: 'private_$activeStudentId')));
              ref.invalidate(notificationProvider);
            }
          } catch (e) {
            print('[WS Data Parse Error] $e');
          }
        },
        onError: (e) {
          print('[WS Connection Error] $e');
          if (!_isDisposed) {
            Future.delayed(const Duration(seconds: 3), _connectWebSocket);
          }
        },
        onDone: () {
          print('[WS Connection Closed] Auto reconnecting...');
          if (!_isDisposed) {
            Future.delayed(const Duration(seconds: 3), _connectWebSocket);
          }
        },
      );
    } catch (e) {
      print('[WS Connect Catch] $e');
      if (!_isDisposed) {
        Future.delayed(const Duration(seconds: 3), _connectWebSocket);
      }
    }
  }

  Future<void> markRead(String notifId) async {
    final api = ref.read(apiServiceProvider);
    await api.markNotificationRead(notifId);
    final updatedList = state.value
            ?.map((n) => n.id == notifId ? n.copyWith(read: true) : n)
            .toList() ??
        [];
    updatedList.sort(_sortNotifications);
    state = AsyncData(updatedList);
  }

  Future<void> markAllRead() async {
    final api = ref.read(apiServiceProvider);
    final current = state.value ?? [];
    for (final n in current.where((item) => !item.read)) {
      api.markNotificationRead(n.id);
    }
    final updatedList = current.map((n) => n.copyWith(read: true)).toList();
    updatedList.sort(_sortNotifications);
    state = AsyncData(updatedList);
  }

  int get unreadCount =>
      state.value?.where((n) => !n.read).length ?? 0;
}

final notificationProvider =
    AsyncNotifierProvider<NotificationNotifier, List<NotificationModel>>(
        NotificationNotifier.new);

final unreadCountProvider = Provider<int>((ref) {
  final notifs = ref.watch(notificationProvider);
  return notifs.when(
    data: (list) => list.where((n) => !n.read).length,
    loading: () => 0,
    error: (_, __) => 0,
  );
});

// ── Study Plan ────────────────────────────────────────────────────────────────
final studyPlanProvider =
    FutureProvider<List<Map<String, dynamic>>>((ref) async {
  final api = ref.read(apiServiceProvider);
  final studentId = ref.read(activeStudentIdProvider);
  return api.getStudyPlan(studentId);
});
// ── Course communication / channels ─────────────────────────────────────────
final studentCoursesProvider =
    FutureProvider<List<CourseModel>>((ref) async {
  final api = ref.read(apiServiceProvider);
  final studentId = ref.read(activeStudentIdProvider);
  return api.getStudentCourses(studentId);
});

final courseInfoProvider =
    FutureProvider.family<CourseModel, String>((ref, courseCode) async {
  final api = ref.read(apiServiceProvider);
  return api.getCourseInfo(courseCode);
});

final courseChannelsProvider =
    FutureProvider.family<List<CourseChannel>, String>((ref, courseCode) async {
  final api = ref.read(apiServiceProvider);
  return api.getCourseChannels(courseCode);
});

final courseNotificationsProvider =
    FutureProvider.family<List<NotificationModel>, String>((ref, courseCode) async {
  final notifs = ref.watch(notificationProvider).value ?? [];
  final cleanCode = courseCode.trim().toLowerCase();
  final moduleCode = cleanCode.split(' ').first;
  
  if (notifs.isNotEmpty) {
    return notifs.where((n) {
      if (n.courseCode == null || n.courseCode!.isEmpty) return true;
      final c = n.courseCode!.trim().toLowerCase();
      final nModule = c.split(' ').first;
      return c == cleanCode || nModule == moduleCode || c.startsWith(moduleCode) || cleanCode.startsWith(c);
    }).toList();
  }
  final api = ref.read(apiServiceProvider);
  final studentId = ref.read(activeStudentIdProvider);
  return api.getCourseNotifications(courseCode, studentId);
});

final courseChannelProvider =
    FutureProvider.family<CourseChannel, String>((ref, channelId) async {
  final api = ref.read(apiServiceProvider);
  return api.getChannel(channelId);
});

final channelMessagesProvider =
    FutureProvider.family<List<CourseMessage>, String>((ref, channelId) async {
  return ref.watch(
    channelThreadMessagesProvider(
      ChannelMessagesArgs(channelId: channelId),
    ).future,
  );
});

class ChannelMessagesArgs {
  final String channelId;
  final String? parentId;

  const ChannelMessagesArgs({
    required this.channelId,
    this.parentId,
  });

  @override
  bool operator ==(Object other) =>
      other is ChannelMessagesArgs &&
      other.channelId == channelId &&
      other.parentId == parentId;

  @override
  int get hashCode => Object.hash(channelId, parentId);
}

final channelThreadMessagesProvider =
    FutureProvider.family<List<CourseMessage>, ChannelMessagesArgs>(
  (ref, args) async {
    final api = ref.read(apiServiceProvider);
    return api.getChannelMessages(
      args.channelId,
      parentId: args.parentId,
    );
  },
);

// ── Resources ─────────────────────────────────────────────────────────────────
final resourcesProvider =
    FutureProvider<List<Map<String, dynamic>>>((ref) async {
  final api = ref.read(apiServiceProvider);
  final studentId = ref.read(activeStudentIdProvider);
  return api.getResources(studentId);
});

// ── Knowledge State ───────────────────────────────────────────────────────────
final knowledgeStateProvider =
    FutureProvider<Map<String, dynamic>>((ref) async {
  final api = ref.read(apiServiceProvider);
  final studentId = ref.read(activeStudentIdProvider);
  return api.getKnowledgeState(studentId);
});

// ── Risk history ──────────────────────────────────────────────────────────────
final riskHistoryProvider = FutureProvider<List<RiskPoint>>((ref) async {
  final api = ref.read(apiServiceProvider);
  final studentId = ref.read(activeStudentIdProvider);
  return api.getRiskHistory(studentId);
});

// ── Assignment Milestones (family keyed by id_assessment) ─────────────────────
final assignmentMilestonesProvider =
    FutureProvider.family<AssignmentMilestonesData, int>((ref, idAssessment) async {
  final api = ref.read(apiServiceProvider);
  final studentId = ref.read(activeStudentIdProvider);
  return api.getMilestones(idAssessment, studentId);
});

// ── Mock mode indicator ───────────────────────────────────────────────────────
final isMockModeProvider = Provider<bool>((ref) {
  return ref.read(apiServiceProvider).isMockMode;
});

// ── Backend / DB health ───────────────────────────────────────────────────────
final healthProvider = FutureProvider<Map<String, dynamic>?>((ref) async {
  final api = ref.read(apiServiceProvider);
  return api.checkHealth();
});

// ── Chat ──────────────────────────────────────────────────────────────────────

class ChatConversation {
  final String id;
  final String title;
  final List<ChatMessage> messages;
  final DateTime createdAt;
  final bool isLoading;

  const ChatConversation({
    required this.id,
    required this.title,
    required this.messages,
    required this.createdAt,
    this.isLoading = false,
  });

  ChatConversation copyWith({
    String? title,
    List<ChatMessage>? messages,
    bool? isLoading,
  }) =>
      ChatConversation(
        id: id,
        title: title ?? this.title,
        messages: messages ?? this.messages,
        createdAt: createdAt,
        isLoading: isLoading ?? this.isLoading,
      );
}

class ChatState {
  final List<ChatConversation> conversations;
  final String? activeId;

  const ChatState({this.conversations = const [], this.activeId});

  ChatConversation? get active =>
      conversations.firstWhereOrNull((c) => c.id == activeId);

  bool get isLoading => active?.isLoading ?? false;

  ChatState copyWith({
    List<ChatConversation>? conversations,
    String? activeId,
    bool clearActiveId = false,
  }) =>
      ChatState(
        conversations: conversations ?? this.conversations,
        activeId: clearActiveId ? null : (activeId ?? this.activeId),
      );
}

class ChatNotifier extends Notifier<ChatState> {
  @override
  ChatState build() => const ChatState();

  String newConversation() {
    final id = DateTime.now().microsecondsSinceEpoch.toString();
    final conv = ChatConversation(
      id: id,
      title: 'New chat',
      messages: const [],
      createdAt: DateTime.now(),
    );
    state = state.copyWith(
      conversations: [conv, ...state.conversations],
      activeId: id,
    );
    return id;
  }

  void switchConversation(String id) {
    state = state.copyWith(activeId: id);
  }

  void deleteConversation(String id) {
    final remaining = state.conversations.where((c) => c.id != id).toList();
    final newActiveId = state.activeId == id ? null : state.activeId;
    state = ChatState(
      conversations: remaining,
      activeId: newActiveId,
    );
  }

  Future<void> sendMessage(String text) async {
    if (text.trim().isEmpty) return;

    var activeId = state.activeId ?? newConversation();

    final conv = state.conversations.firstWhere((c) => c.id == activeId);

    // Set title from first user message
    final newTitle = conv.messages.isEmpty
        ? (text.length > 40 ? '${text.substring(0, 40)}...' : text)
        : conv.title;

    final userMsg = ChatMessage(
      id: '${DateTime.now().microsecondsSinceEpoch}',
      role: 'user',
      content: text.trim(),
      timestamp: DateTime.now(),
    );

    final assistantId = '${DateTime.now().microsecondsSinceEpoch + 1}';
    var assistantMsg = ChatMessage(
      id: assistantId,
      role: 'assistant',
      content: '',
      timestamp: DateTime.now(),
      isLoading: true,
    );

    final history = [
      ...conv.messages.where((m) => !m.isLoading).map((m) => m.toJson()),
      userMsg.toJson(),
    ];

    _updateConv(activeId, (c) => c.copyWith(
          title: newTitle,
          messages: [...c.messages, userMsg, assistantMsg],
          isLoading: true,
        ));

    void updateMsg() {
      _updateConv(activeId, (c) {
        final idx = c.messages.indexWhere((m) => m.id == assistantId);
        if (idx == -1) return c;
        final msgs = [...c.messages];
        msgs[idx] = assistantMsg;
        return c.copyWith(
          messages: msgs,
          isLoading: assistantMsg.isLoading,
        );
      });
    }

    try {
      final api = ref.read(apiServiceProvider);
      final studentId = ref.read(activeStudentIdProvider);

      await for (final event in api.streamChatMessage(
        studentId: studentId,
        messages: history,
      )) {
        final type = event['type'] as String? ?? '';
        final delta = event['delta'] as String? ?? '';

        switch (type) {
          case 'tool_call':
            final name = event['name'] as String? ?? '';
            final label = kToolDisplayLabels[name] ?? name;
            assistantMsg = assistantMsg.copyWith(
              toolCalls: [
                ...assistantMsg.toolCalls,
                ToolCallInfo(name: name, displayLabel: label),
              ],
            );
          case 'thinking':
            assistantMsg = assistantMsg.copyWith(
              reasoning: assistantMsg.reasoning + delta,
            );
          case 'thinking_done':
            assistantMsg = assistantMsg.copyWith(isThinkingDone: true);
          case 'content':
            assistantMsg = assistantMsg.copyWith(
              content: assistantMsg.content + delta,
            );
          case 'data_updated':
            final resources =
                (event['resources'] as List?)?.cast<String>() ?? [];
            for (final r in resources) {
              switch (r) {
                case 'study_plan':
                  ref.invalidate(studyPlanProvider);
                case 'notifications':
                  ref.invalidate(notificationProvider);
                case 'resources':
                  ref.invalidate(resourcesProvider);
                case 'assignments':
                  ref.invalidate(studentProvider);
                case 'knowledge_state':
                  ref.invalidate(knowledgeStateProvider);
                case 'milestones':
                  ref.invalidate(assignmentMilestonesProvider);
              }
            }
          case 'done':
            assistantMsg = assistantMsg.copyWith(isLoading: false);
          case 'error':
            assistantMsg = assistantMsg.copyWith(
              content: 'Unable to connect to AI. Please try again.',
              isLoading: false,
            );
        }
        updateMsg();
      }

      if (assistantMsg.isLoading) {
        assistantMsg = assistantMsg.copyWith(isLoading: false);
        updateMsg();
      }
    } catch (_) {
      assistantMsg = assistantMsg.copyWith(
        content: 'Unable to connect to AI. Please try again.',
        isLoading: false,
      );
      updateMsg();
    }
  }

  void _updateConv(String id, ChatConversation Function(ChatConversation) fn) {
    state = state.copyWith(
      conversations: state.conversations.map((c) => c.id == id ? fn(c) : c).toList(),
    );
  }
}

final chatProvider =
    NotifierProvider<ChatNotifier, ChatState>(ChatNotifier.new);

final activeChatProvider = Provider<ChatConversation?>((ref) {
  return ref.watch(chatProvider).active;
});
