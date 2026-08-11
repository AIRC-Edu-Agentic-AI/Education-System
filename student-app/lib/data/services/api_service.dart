import 'dart:convert';
import 'package:dio/dio.dart';
import 'package:student_agent/core/config/env_config.dart';
import 'package:student_agent/data/mock/mock_data.dart';
import 'package:student_agent/models/assignment_milestone_model.dart';
import 'package:student_agent/models/assignment_submission_model.dart';
import 'package:student_agent/models/course_model.dart';
import 'package:student_agent/models/student_model.dart';
import 'package:student_agent/data/mock/mock_message_store.dart';
import 'dart:io';
import 'package:student_agent/models/instructor_feedback_model.dart';
import 'package:student_agent/models/class_comment_model.dart';

class ApiService {
  
  late final Dio _dio;
  bool _useMock = false;
  static final Map<String, AssignmentSubmission> _mockSubmissions = {};
  static final Map<int, List<InstructorFeedback>> _mockFeedbacks = {
    1753: [
      InstructorFeedback(
        id: 1,
        assessmentId: 1753,
        content: 'Good submission, but argument clarity and formatting could be improved.',
        score: 7.5,
        createdAt: DateTime.now().subtract(const Duration(days: 1)),
        instructorName: 'Dr. John Doe',
      ),
    ],
  };
  static final Map<int, List<ClassComment>> _mockClassComments = {
    1753: [
      ClassComment(
        id: 1,
        assessmentId: 1753,
        studentId: 101,
        studentName: 'Jane Smith',
        content: 'How is everyone progressing on this assignment?',
        isInstructor: false,
        createdAt: DateTime.now().subtract(const Duration(hours: 3)),
      ),
      ClassComment(
        id: 2,
        assessmentId: 1753,
        studentId: 0,
        studentName: 'Instructor',
        content: 'Reminder to all students: deadline is 23:59 tomorrow.',
        isInstructor: true,
        createdAt: DateTime.now().subtract(const Duration(hours: 1)),
      ),
    ],
  };

  ApiService({String? token}) {
    _dio = Dio(BaseOptions(
      baseUrl: EnvConfig.apiBaseUrl,
      connectTimeout: const Duration(seconds: 5),
      receiveTimeout: const Duration(seconds: 600),
      headers: {
        'Content-Type': 'application/json',
        if (token != null) 'Authorization': 'Bearer $token',
      },
    ));

    _useMock = EnvConfig.useMockData;

    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) => handler.next(options),
      onError: (error, handler) {
        // _useMock = true;
        handler.next(error);
      },
    ));
  }

  // ── Health check ──────────────────────────────────────────────
  Future<bool> isBackendReachable() async {
    try {
      final res = await _dio.get('/health');
      return res.statusCode == 200;
    } catch (_) {
      // _useMock = true;
      return false;
    }
  }

  Future<Map<String, dynamic>?> checkHealth() async {
    try {
      final res = await _dio.get('/health');
      if (res.statusCode == 200) return Map<String, dynamic>.from(res.data);
      return null;
    } catch (_) {
      // _useMock = true;
      return null;
    }
  }

  // ── Student ───────────────────────────────────────────────────
  Future<StudentModel> getStudent(int studentId) async {
    try {
      final res = await _dio.get('/student/$studentId');
      return StudentModel.fromJson(res.data);
    } catch (_) {
      final pres = studentId.toString().startsWith('2013') ? '2013J' : (studentId.toString().startsWith('2014') ? '2014J' : '2013J');
      return StudentModel(
        id: 'student_$studentId',
        auth0Id: 'auth0|student_$studentId',
        studentId: studentId,
        fullName: studentId == 28400 ? 'Nguyen Van An' : 'Student $studentId',
        shortName: studentId == 28400 ? 'Van An' : 'ST $studentId',
        demographics: const Demographics(
          gender: 'M',
          ageBand: '18-25',
          region: 'Hanoi',
          highestEducation: 'HE Qualification',
          imdBand: '20-30%',
          disability: false,
          numPrevAttempts: 0,
          studiedCredits: 60,
        ),
        enrollments: [
          Enrollment(
            codeModule: 'AAA',
            codePresentation: pres,
            title: 'Course AAA ($pres)',
            moduleLength: 30,
            finalResult: null,
            assessments: const [],
            vleSummary: VleSummary(
              totalClicks: 3842,
              lastActiveDay: 42,
              byActivityType: const {},
              weeklyClicks: const [],
            ),
          ),
        ],
        risk: RiskProfile(tier: 0, score: 0.0, flags: const [], computedAt: DateTime.now()),
        prerequisiteGaps: const [],
      );
    }
  }

  // ── Schedule / Weekly view ────────────────────────────────────
  Future<WeeklySchedule> getWeeklySchedule(int studentId) async {
    if (_useMock) return MockData.weeklySchedule;
    try {
      final res = await _dio.get('/schedule/$studentId/weekly');
      return WeeklySchedule.fromJson(res.data);
    } catch (_) {
      // _useMock = true;
      return MockData.weeklySchedule;
    }
  }

  Future<List<CourseModel>> getStudentCourses(int studentId) async {
    if (_useMock) return MockData.courses;
    try {
      final res = await _dio.get('/course/course-communication/student/$studentId');
      return (res.data as List)
          .map((course) => CourseModel.fromJson(
            Map<String, dynamic>.from(course),
          ))
          .toList();
    } catch (_) {
      // _useMock = true;
      return MockData.courses;
    }
  }

  Future<CourseModel> getCourseInfo(String courseCode) async {
    if (_useMock) {
      return CourseModel(
        id: '',
        courseCode: courseCode,
        title: courseCode,
        presentation: '',
        term: '',
        instructors: const [],
        classReps: const [],
        members: const [],
        status: 'unknown',
        settings: const {},
        createdAt: DateTime.now(),
        updatedAt: DateTime.now(),
      );
    }
    try {
      final res = await _dio.get('/course/course-communication/$courseCode');
      return CourseModel.fromJson(Map<String, dynamic>.from(res.data));
    } catch (_) {
      // _useMock = true;
      return CourseModel(
        id: '',
        courseCode: courseCode,
        title: courseCode,
        presentation: '',
        term: '',
        instructors: const [],
        classReps: const [],
        members: const [],
        status: 'unknown',
        settings: const {},
        createdAt: DateTime.now(),
        updatedAt: DateTime.now(),
      );
    }
  }

  Future<List<CourseChannel>> getCourseChannels(String courseCode) async {
    if (_useMock) return MockData.channelsFor(courseCode);
    try {
      final res = await _dio.get('/course/course-communication/courses/$courseCode/channels');
      return (res.data as List)
        .map((channel) => CourseChannel.fromJson(Map<String, dynamic>.from(channel)))
        .toList();
    } catch (_) {
      // _useMock = true;
      return MockData.channelsFor(courseCode);
    }
  }

  Future<CourseChannel> getPrivateChannel(int studentId, {String? courseCode}) async {
    try {
      final res = await _dio.get(
        '/realtime-chat/private-channel',
        queryParameters: {
          'student_id': studentId,
          if (courseCode != null) 'course_code': courseCode,
        },
      );
      return CourseChannel.fromJson(Map<String, dynamic>.from(res.data));
    } catch (_) {
      return CourseChannel(
        id: 'private_$studentId',
        courseCode: courseCode ?? 'AAA 2013J',
        type: 'private_message',
        name: 'Instructor',
        isReadOnly: false,
        allowedPostRoles: const [],
        status: 'active',
        createdAt: DateTime.now(),
        updatedAt: DateTime.now(),
      );
    }
  }

  Future<CourseChannel> getChannel(String channelId) async {
    if (_useMock) {
      return CourseChannel(
        id: channelId,
        courseCode: '',
        type: 'discussion',
        name: 'Discussion Channel',
        isReadOnly: false,
        allowedPostRoles: const [],
        status: 'active',
        createdAt: DateTime.now(),
        updatedAt: DateTime.now(),
      );
    }
    try {
      final res = await _dio.get('/course/course-communication/$channelId');
      return CourseChannel.fromJson(Map<String, dynamic>.from(res.data));
    } catch (_) {
      // _useMock = true;
      return CourseChannel(
        id: channelId,
        courseCode: '',
        type: 'discussion',
        name: 'Discussion Channel',
        isReadOnly: false,
        allowedPostRoles: const [],
        status: 'active',
        createdAt: DateTime.now(),
        updatedAt: DateTime.now(),
      );
    }
  }

  Future<List<CourseMessage>> getChannelMessages(String channelId,
    {String? parentId}) async {
  if (_useMock) {
    return MockMessageStore.allFor(channelId, parentId: parentId);
  }
  try {
    final res = await _dio.get(
      '/course/course-communication/$channelId/messages',
      queryParameters: parentId == null ? null : {'parent_id': parentId},
    );
    return (res.data as List)
        .map((message) =>
            CourseMessage.fromJson(Map<String, dynamic>.from(message)))
        .toList();
  } catch (_) {
    // _useMock = true;
    return MockMessageStore.allFor(channelId, parentId: parentId);
  }
}

  Future<CourseMessage?> postChannelMessage({
  required String channelId,
  required int senderId,
  required String content,
  String? parentId,
  String? courseCode,
  String? channelType,
}) async {
  if (_useMock) {
    final msg = CourseMessage(
      id: 'mock_post_${DateTime.now().microsecondsSinceEpoch}',
      channelId: channelId,
      courseCode: MockMessageStore.courseCodeFromChannelId(channelId),
      senderId: senderId,
      senderRole: 'student',
      content: content.trim(),
      createdAt: DateTime.now(),
      parentId: parentId,
    );
    MockMessageStore.add(msg);
    return msg;
  }
  try {
    final res = await _dio.post(
      '/course/course-communication/$channelId/messages',
      data: {
        'sender_id': senderId,
        'content': content,
        if (parentId != null) 'parent_id': parentId,
        if (courseCode != null && courseCode.isNotEmpty) 'course_code': courseCode,
        if (channelType != null && channelType.isNotEmpty) 'channel_type': channelType,
      },
    );
    return CourseMessage.fromJson(Map<String, dynamic>.from(res.data));
  } catch (_) {
    // _useMock = true;
    return null;
  }
}

  Future<bool> addChannelReaction(
      String messageId, int userId, String emoji) async {
    if (_useMock) return false;
    try {
      await _dio.post('/course/course-communication/messages/$messageId/reactions', data: {
        'user_id': userId,
        'emoji': emoji,
      });
      return true;
    } catch (_) {
      return false;
    }
  }

  // ── Notifications (polling) ───────────────────────────────────
  Future<List<NotificationModel>> getNotifications(int studentId, {bool unreadOnly = false}) async {
    if (_useMock) return MockData.notifications;
    try {
      final res = await _dio
          .get('/notify/$studentId', queryParameters: {'unread_only': unreadOnly});
      return (res.data as List)
          .map((n) => NotificationModel.fromJson(n))
          .toList();
    } catch (_) {
      // _useMock = true;
      return MockData.notifications;
    }
  }

  Future<void> markNotificationRead(String notifId) async {
    if (_useMock) return;
    try {
      await _dio.patch('/notify/$notifId/read');
    } catch (_) {}
  }

  Future<List<NotificationModel>> getCourseNotifications(
      String courseCode, int studentId) async {
    if (_useMock) {
      return MockData.notifications.where((n) {
        final title = n.title.toLowerCase();
        final body = n.body.toLowerCase();
        final code = courseCode.toLowerCase();
        return title.contains(code) || body.contains(code);
      }).toList();
    }
    try {
      final res = await _dio.get(
        '/notify/course/$courseCode',
        queryParameters: {'student_id': studentId},
      );
      return (res.data as List)
          .map((n) => NotificationModel.fromJson(n))
          .toList();
    } catch (_) {
      return MockData.notifications.where((n) {
        final title = n.title.toLowerCase();
        final body = n.body.toLowerCase();
        final code = courseCode.toLowerCase();
        return title.contains(code) || body.contains(code);
      }).toList();
    }
  }

  // ── Chat (streaming SSE) ──────────────────────────────────────
  Stream<Map<String, dynamic>> streamChatMessage({
    required int studentId,
    required List<Map<String, dynamic>> messages,
  }) async* {
    if (_useMock) {
      yield {'type': 'content', 'delta': 'Mock mode — backend offline.'};
      yield {'type': 'done'};
      return;
    }
    try {
      final response = await _dio.post<ResponseBody>(
        '/chat/stream',
        data: {'student_id': studentId, 'messages': messages},
        options: Options(responseType: ResponseType.stream),
      );
      var leftover = '';
      await for (final chunk in response.data!.stream) {
        final text = leftover + utf8.decode(chunk);
        final lines = text.split('\n');
        leftover = lines.removeLast();
        for (final line in lines) {
          if (!line.startsWith('data: ')) continue;
          final raw = line.substring(6).trim();
          if (raw.isEmpty) continue;
          try {
            yield json.decode(raw) as Map<String, dynamic>;
          } catch (_) {}
        }
      }

      if (leftover.startsWith('data: ')) {
        final raw = leftover.substring(6).trim();
        if (raw.isNotEmpty) {
          try {
            yield json.decode(raw) as Map<String, dynamic>;
          } catch (_) {}
        }
      }
    } catch (_) {
      yield {'type': 'error'};
    }
  }

  // ── Assignment Milestones ─────────────────────────────────────
  Future<AssignmentMilestonesData> getMilestones(
      int idAssessment, int studentId) async {
    if (_useMock) return MockData.milestonesFor(idAssessment);
    try {
      final res = await _dio.get(
        '/student/$idAssessment/milestones',
        queryParameters: {'student_id': studentId},
      );
      return AssignmentMilestonesData.fromJson(
          Map<String, dynamic>.from(res.data));
    } catch (_) {
      // _useMock = true;
      return MockData.milestonesFor(idAssessment);
    }
  }

  Future<AssignmentMilestonesData> triggerBreakdown(
      int idAssessment, int studentId) async {
    if (_useMock) return MockData.milestonesFor(idAssessment);
    try {
      final res = await _dio.post(
        '/student/$idAssessment/breakdown',
        queryParameters: {'student_id': studentId},
      );
      return AssignmentMilestonesData.fromJson(
          Map<String, dynamic>.from(res.data));
    } catch (_) {
      // _useMock = true;
      return MockData.milestonesFor(idAssessment);
    }
  }

  Future<void> updateMilestoneStatus({
    required int studentId,
    required int idAssessment,
    required String milestoneId,
    required String status,
  }) async {
    if (_useMock) return;
    try {
      await _dio.patch('/student/milestone/status', data: {
        'student_id': studentId,
        'id_assessment': idAssessment,
        'milestone_id': milestoneId,
        'status': status,
      });
    } catch (_) {}
  }

  // ── Assignment Submission ─────────────────────────────────────
  
  // Lấy danh sách submissions
  Future<List<AssignmentSubmission>> getSubmissions(
    int assessmentId,
    int studentId,
  ) async {
    if (_useMock) {
      return _mockGetSubmissions(assessmentId, studentId);
    }
    try {
      final response = await _dio.get(
        '/student/$assessmentId/submissions',
        queryParameters: {'student_id': studentId},
      );
      if (response.data['submissions'] != null) {
        return (response.data['submissions'] as List)
            .map((s) => AssignmentSubmission.fromJson(s))
            .toList();
      }
      return [];
    } catch (e) {
      // _useMock = true;
      return _mockGetSubmissions(assessmentId, studentId);
    }
  }

  List<AssignmentSubmission> _mockGetSubmissions(int assessmentId, int studentId) {
    final key = '$studentId-$assessmentId';
    if (_mockSubmissions.containsKey(key)) {
      return [_mockSubmissions[key]!];
    }
    return [];
  }

  // Lấy 1 submission (cũ)
  Future<AssignmentSubmission?> getSubmission(
      int idAssessment, int studentId) async {
    if (_useMock) {
      return _mockSubmission(idAssessment, studentId);
    }
    try {
      final res = await _dio.get(
        '/student/$idAssessment/submission',
        queryParameters: {'student_id': studentId},
      );
      final data = Map<String, dynamic>.from(res.data);
      final sub = data['submission'];
      if (sub == null) return null;
      return AssignmentSubmission.fromJson(Map<String, dynamic>.from(sub));
    } catch (_) {
      return _mockSubmission(idAssessment, studentId);
    }
  }

  // Submit assignment với file
  Future<AssignmentSubmission> submitAssignment({
    required int idAssessment,
    required int studentId,
    required File file,
  }) async {
    if (_useMock) {
      return _mockSubmit(idAssessment, studentId, file);
    }
    try {
      final formData = FormData.fromMap({
        'student_id': studentId.toString(),
        'file': await MultipartFile.fromFile(
          file.path,
          filename: file.path.split('/').last,
        ),
      });
      
      final response = await _dio.post(
        '/student/$idAssessment/submit-file',
        data: formData,
      );
      
      final sub = Map<String, dynamic>.from(response.data['submission']);
      return AssignmentSubmission.fromJson(sub);
    } catch (e) {
      rethrow;
    }
  }

  // Hủy nộp bài
  Future<void> unsumbitAssignment(int assessmentId, String submissionId) async {
    if (_useMock) {
      return _mockUnsubmit(assessmentId, submissionId);
    }
    try {
      await _dio.delete(
        '/student/$assessmentId/submissions/$submissionId',
      );
    } catch (e) {
      // _useMock = true;
      _mockUnsubmit(assessmentId, submissionId);
    }
  }

  void _mockUnsubmit(int assessmentId, String submissionId) {
    // Xóa khỏi mock storage
    _mockSubmissions.removeWhere((key, sub) => sub.id == submissionId);
  }

  // Mock methods
  AssignmentSubmission? _mockSubmission(int idAssessment, int studentId) {
    final key = '$studentId-$idAssessment';
    return _mockSubmissions[key];
  }

  AssignmentSubmission _mockSubmit(
    int idAssessment,
    int studentId,
    File file,
  ) {
    final sub = AssignmentSubmission(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      studentId: studentId,
      idAssessment: idAssessment,
      courseCode: 'MOCK_COURSE',
      fileName: file.path.split('/').last,
      fileUrl: 'mock_url/${file.path.split('/').last}',
      fileType: 'pdf',
      submittedAt: DateTime.now(),
      submittedDay: DateTime.now().day,
      status: 'submitted',
    );
    _mockSubmissions['$studentId-$idAssessment'] = sub;
    return sub;
  }

  // ── Instructor Feedbacks ─────────────────────────────────────
  Future<List<InstructorFeedback>> getFeedbacks(int assessmentId) async {
    if (_useMock) {
      return _mockGetFeedbacks(assessmentId);
    }
    try {
      final response = await _dio.get(
        '/student/$assessmentId/feedbacks',
      );
      if (response.data['feedbacks'] != null) {
        return (response.data['feedbacks'] as List)
            .map((f) => InstructorFeedback.fromJson(f))
            .toList();
      }
      return [];
    } catch (e) {
      // _useMock = true;
      return _mockGetFeedbacks(assessmentId);
    }
  }

  List<InstructorFeedback> _mockGetFeedbacks(int assessmentId) {
    return _mockFeedbacks[assessmentId] ?? [];
  }

  // ── Class Comments ────────────────────────────────────────────
  Future<List<ClassComment>> getClassComments(int assessmentId) async {
    if (_useMock) {
      return _mockGetClassComments(assessmentId);
    }
    try {
      final response = await _dio.get(
        '/student/$assessmentId/comments',
      );
      if (response.data['comments'] != null) {
        return (response.data['comments'] as List)
            .map((c) => ClassComment.fromJson(c))
            .toList();
      }
      return [];
    } catch (e) {
      // _useMock = true;
      return _mockGetClassComments(assessmentId);
    }
  }

  List<ClassComment> _mockGetClassComments(int assessmentId) {
    return _mockClassComments[assessmentId] ?? [];
  }

  // Thêm comment lớp học
  Future<ClassComment> addClassComment({
    required int assessmentId,
    required int studentId,
    required String content,
  }) async {
    if (_useMock) {
      return _mockAddClassComment(assessmentId, studentId, content);
    }
    try {
      final response = await _dio.post(
        '/student/$assessmentId/comments',
        data: {
          'student_id': studentId,
          'content': content,
        },
      );
      return ClassComment.fromJson(response.data);
    } catch (e) {
      // _useMock = true;
      return _mockAddClassComment(assessmentId, studentId, content);
    }
  }

  ClassComment _mockAddClassComment(
    int assessmentId,
    int studentId,
    String content,
  ) {
    return ClassComment(
      id: DateTime.now().millisecondsSinceEpoch,
      assessmentId: assessmentId,
      studentId: studentId,
      studentName: 'Student $studentId',
      content: content,
      isInstructor: false,
      createdAt: DateTime.now(),
    );
  }

  // ── Knowledge State ──────────────────────────────────────────
  Future<Map<String, dynamic>> getKnowledgeState(int studentId) async {
    if (_useMock) return MockData.knowledgeState;
    try {
      final res = await _dio.get('/student/$studentId/knowledge');
      return Map<String, dynamic>.from(res.data);
    } catch (_) {
      // _useMock = true;
      return MockData.knowledgeState;
    }
  }

  // ── Risk history ──────────────────────────────────────────────
  Future<List<RiskPoint>> getRiskHistory(int studentId) async {
    if (_useMock) return MockData.riskHistory;
    try {
      final res = await _dio.get('/student/$studentId/risk-history');
      return (res.data as List).map((e) => RiskPoint.fromJson(e)).toList();
    } catch (_) {
      // _useMock = true;
      return MockData.riskHistory;
    }
  }

  // ── Study Plan ────────────────────────────────────────────────
  Future<List<Map<String, dynamic>>> getStudyPlan(int studentId) async {
    if (_useMock) return MockData.studyPlanSessions;
    try {
      final res = await _dio.get('/schedule/$studentId/plan');
      return List<Map<String, dynamic>>.from(res.data);
    } catch (_) {
      // _useMock = true;
      return MockData.studyPlanSessions;
    }
  }

  Future<bool> updateStudyPlan(int studentId, List<Map<String, dynamic>> sessions) async {
    if (_useMock) return true;
    try {
      final res = await _dio.put('/schedule/$studentId/plan', data: {'sessions': sessions});
      return res.statusCode == 200 || res.statusCode == 201;
    } catch (e) {
      return false;
    }
  }

  // ── Resources ─────────────────────────────────────────────────
  Future<List<Map<String, dynamic>>> getResources(int studentId) async {
    if (_useMock) return MockData.resources;
    try {
      final res = await _dio.get('/resources/$studentId');
      return List<Map<String, dynamic>>.from(res.data);
    } catch (_) {
      // _useMock = true;
      return MockData.resources;
    }
  }

  bool get isMockMode => _useMock;
}
