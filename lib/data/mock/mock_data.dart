import 'package:student_agent/models/assignment_milestone_model.dart';
import 'package:student_agent/models/student_model.dart';

class MockData {
  static final StudentModel student = StudentModel(
    id: 'mock_student_001',
    auth0Id: 'auth0|mock_student_001',
    studentId: 28400,
    fullName: 'Nguyễn Văn An',
    shortName: 'Văn An',
    demographics: const Demographics(
      gender: 'M',
      ageBand: '25-35',
      region: 'Hà Nội',
      highestEducation: 'HE Qualification',
      imdBand: '20-30%',
      disability: false,
      numPrevAttempts: 0,
      studiedCredits: 60,
    ),
    enrollments: [
      // PRIMARY — at-risk course
      const Enrollment(
        codeModule: 'DATA201',
        codePresentation: '2024A',
        title: 'Phân tích Dữ liệu & Thống kê',
        moduleLength: 30,
        finalResult: null,
        assessments: [
          Assessment(
            idAssessment: 1752, type: 'TMA', dueDate: 19, weight: 10,
            score: 42, submittedDate: 18, isBanked: false,
          ),
          Assessment(
            idAssessment: 1753, type: 'TMA', dueDate: 49, weight: 25,
            score: null, submittedDate: null, isBanked: false,
          ),
          Assessment(
            idAssessment: 1754, type: 'CMA', dueDate: 68, weight: 15,
            score: null, submittedDate: null, isBanked: false,
          ),
          Assessment(
            idAssessment: 1755, type: 'Exam', dueDate: 261, weight: 50,
            score: null, submittedDate: null, isBanked: false,
          ),
        ],
        vleSummary: VleSummary(
          totalClicks: 3842,
          lastActiveDay: 42,
          byActivityType: {
            'resource': 1240, 'forumng': 287, 'oucontent': 1100,
            'quiz': 420, 'url': 312, 'homepage': 483,
          },
          weeklyClicks: [
            320, 410, 380, 300, 210, 120, 45,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
          ],
        ),
      ),
      // Đại số Tuyến tính — mixed
      const Enrollment(
        codeModule: 'MATH102',
        codePresentation: '2024A',
        title: 'Đại số Tuyến tính',
        moduleLength: 30,
        finalResult: null,
        assessments: [
          Assessment(
            idAssessment: 2010, type: 'TMA', dueDate: 22, weight: 20,
            score: 65, submittedDate: 21, isBanked: false,
          ),
          Assessment(
            idAssessment: 2011, type: 'CMA', dueDate: 55, weight: 30,
            score: 58, submittedDate: 54, isBanked: false,
          ),
          Assessment(
            idAssessment: 2012, type: 'Exam', dueDate: 250, weight: 50,
            score: null, submittedDate: null, isBanked: false,
          ),
        ],
        vleSummary: VleSummary(
          totalClicks: 2110,
          lastActiveDay: 45,
          byActivityType: {
            'resource': 720, 'oucontent': 640, 'quiz': 410, 'homepage': 340,
          },
          weeklyClicks: [
            180, 220, 240, 210, 190, 160, 140,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
          ],
        ),
      ),
      // Lập trình Python — strong
      const Enrollment(
        codeModule: 'COMP101',
        codePresentation: '2024A',
        title: 'Lập trình Python',
        moduleLength: 30,
        finalResult: null,
        assessments: [
          Assessment(
            idAssessment: 3010, type: 'TMA', dueDate: 20, weight: 15,
            score: 88, submittedDate: 19, isBanked: false,
          ),
          Assessment(
            idAssessment: 3011, type: 'TMA', dueDate: 48, weight: 25,
            score: 79, submittedDate: 47, isBanked: false,
          ),
          Assessment(
            idAssessment: 3012, type: 'Exam', dueDate: 255, weight: 60,
            score: null, submittedDate: null, isBanked: false,
          ),
        ],
        vleSummary: VleSummary(
          totalClicks: 5240,
          lastActiveDay: 46,
          byActivityType: {
            'resource': 1480, 'oucontent': 1620, 'quiz': 1100,
            'forumng': 540, 'homepage': 500,
          },
          weeklyClicks: [
            410, 460, 520, 480, 500, 470, 510,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
          ],
        ),
      ),
      // Xác suất & Thống kê — on track
      const Enrollment(
        codeModule: 'STAT110',
        codePresentation: '2024A',
        title: 'Xác suất & Thống kê Suy luận',
        moduleLength: 30,
        finalResult: null,
        assessments: [
          Assessment(
            idAssessment: 4010, type: 'TMA', dueDate: 25, weight: 20,
            score: 71, submittedDate: 24, isBanked: false,
          ),
          Assessment(
            idAssessment: 4011, type: 'CMA', dueDate: 60, weight: 20,
            score: null, submittedDate: null, isBanked: false,
          ),
          Assessment(
            idAssessment: 4012, type: 'Exam', dueDate: 258, weight: 60,
            score: null, submittedDate: null, isBanked: false,
          ),
        ],
        vleSummary: VleSummary(
          totalClicks: 2980,
          lastActiveDay: 44,
          byActivityType: {
            'resource': 980, 'oucontent': 870, 'quiz': 620, 'homepage': 510,
          },
          weeklyClicks: [
            260, 300, 280, 310, 270, 240, 230,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
          ],
        ),
      ),
    ],
    risk: RiskProfile(
      tier: 3,
      score: 0.82,
      flags: const ['low_vle_engagement', 'assessment_due_soon', 'assessment_shock'],
      computedAt: DateTime.now().subtract(const Duration(hours: 6)),
    ),
    prerequisiteGaps: const ['Thống kê cơ bản', 'Đại số tuyến tính'],
  );

  static final WeeklySchedule weeklySchedule = WeeklySchedule(
    currentWeek: 7,
    totalWeeks: 30,
    streakDays: 12,
    lectures: [
      WeekItem(
        title: 'Phân tích Dữ liệu & Thống kê',
        subtitle: 'Thứ 2, 08:00',
        dateTime: DateTime.now().add(const Duration(days: 1)),
        isCompleted: false,
      ),
      WeekItem(
        title: 'Đại số Tuyến tính',
        subtitle: 'Thứ 4, 10:00',
        dateTime: DateTime.now().add(const Duration(days: 3)),
        isCompleted: false,
      ),
      WeekItem(
        title: 'Kiểm định giả thuyết',
        subtitle: 'Thứ 6, 14:00',
        dateTime: DateTime.now().add(const Duration(days: 5)),
        isCompleted: false,
      ),
    ],
    classes: [
      WeekItem(
        title: 'Lab Lập trình Python',
        subtitle: 'Thứ 3, 13:00 · Phòng B204',
        dateTime: DateTime.now().add(const Duration(days: 2)),
        isCompleted: false,
      ),
      WeekItem(
        title: 'Xác suất & Thống kê Suy luận',
        subtitle: 'Thứ 5, 09:00 · Online',
        dateTime: DateTime.now().add(const Duration(days: 4)),
        isCompleted: false,
      ),
    ],
    assignments: [
      WeekItem(
        title: 'TMA-02 — Phân tích hồi quy',
        subtitle: 'Nộp trước Thứ 6',
        dateTime: DateTime.now().add(const Duration(days: 5)),
        isCompleted: false,
        isUrgent: true,
      ),
      WeekItem(
        title: 'CMA — Đại số Tuyến tính',
        subtitle: 'Nộp trước Thứ 7',
        dateTime: DateTime.now().add(const Duration(days: 6)),
        isCompleted: false,
        isUrgent: false,
      ),
    ],
    exams: [],
  );

  static final List<NotificationModel> notifications = [
    NotificationModel(
      id: 'notif_001',
      studentId: 28400,
      type: 'deadline_warning',
      title: 'TMA-02 — Phân tích Dữ liệu sắp đến hạn',
      body: 'Còn 3 ngày (đến ngày 49). Hãy bắt đầu sớm.',
      read: false,
      createdAt: DateTime.now().subtract(const Duration(hours: 2)),
      actionOptions: [
        const NotificationAction(
          label: 'Lên kế hoạch',
          action: 'open_chat',
          payload: {'message': 'Giúp tôi lên kế hoạch hoàn thành TMA-02 môn Phân tích Dữ liệu'},
        ),
        const NotificationAction(
          label: 'Nhắc lại sau',
          action: 'snooze',
          payload: {},
        ),
      ],
    ),
    NotificationModel(
      id: 'notif_002',
      studentId: 28400,
      type: 'reminder',
      title: 'Ôn tập hôm nay',
      body: 'Bạn có 4 thẻ flashcard cần ôn tập theo lịch SM-2.',
      read: false,
      createdAt: DateTime.now().subtract(const Duration(hours: 5)),
      actionOptions: [
        const NotificationAction(
          label: 'Hỏi trợ lý',
          action: 'open_chat',
          payload: {'message': 'Hôm nay tôi nên ôn tập gì?'},
        ),
      ],
    ),
  ];

  static final List<Map<String, dynamic>> studyPlanSessions = [
    {
      'subject': 'Ôn tập Tuần 6 — Phân tích Dữ liệu',
      'type': 'review',
      'duration': 45,
      'day': 'Thứ 2',
      'time': '19:00',
      'sm2_interval': 3,
    },
    {
      'subject': 'Đọc tài liệu Tuần 7',
      'type': 'new',
      'duration': 60,
      'day': 'Thứ 3',
      'time': '20:00',
      'sm2_interval': null,
    },
    {
      'subject': 'Luyện tập TMA-02',
      'type': 'practice',
      'duration': 90,
      'day': 'Thứ 4',
      'time': '19:30',
      'sm2_interval': null,
    },
    {
      'subject': 'Flashcard Tuần 5–6',
      'type': 'spaced_rep',
      'duration': 20,
      'day': 'Thứ 5',
      'time': '08:00',
      'sm2_interval': 7,
    },
    {
      'subject': 'Hoàn thiện TMA-02',
      'type': 'assignment',
      'duration': 120,
      'day': 'Thứ 6',
      'time': '14:00',
      'sm2_interval': null,
    },
  ];

  static final Map<String, dynamic> knowledgeState = {
    'Thống kê cơ bản': {
      'mastery': 0.35,
      'last_updated': '2025-01-10',
      'evidence_count': 2,
    },
    'Đại số tuyến tính': {
      'mastery': 0.28,
      'last_updated': '2025-01-12',
      'evidence_count': 1,
    },
    'Hồi quy tuyến tính': {
      'mastery': 0.55,
      'last_updated': '2025-01-18',
      'evidence_count': 3,
    },
    'Kiểm định giả thuyết': {
      'mastery': 0.42,
      'last_updated': '2025-01-20',
      'evidence_count': 2,
    },
  };

  static const List<RiskPoint> riskHistory = [
    RiskPoint(week: 1, score: 0.30, tier: 1),
    RiskPoint(week: 2, score: 0.38, tier: 1),
    RiskPoint(week: 3, score: 0.46, tier: 2),
    RiskPoint(week: 4, score: 0.55, tier: 2),
    RiskPoint(week: 5, score: 0.66, tier: 2),
    RiskPoint(week: 6, score: 0.74, tier: 3),
    RiskPoint(week: 7, score: 0.82, tier: 3),
  ];

  static AssignmentMilestonesData milestonesFor(int idAssessment) {
    if (idAssessment == 1753) {
      return const AssignmentMilestonesData(
        idAssessment: 1753,
        module: 'DATA201',
        title: 'TMA-02 — Phân tích hồi quy',
        milestones: [
          MilestoneModel(
            id: 'm1',
            title: 'Đọc đề bài & tài liệu tham khảo',
            status: MilestoneStatus.done,
            dueOffsetDays: -14,
          ),
          MilestoneModel(
            id: 'm2',
            title: 'Phân tích dữ liệu ban đầu',
            status: MilestoneStatus.inProgress,
            dueOffsetDays: -7,
          ),
          MilestoneModel(
            id: 'm3',
            title: 'Viết báo cáo nháp',
            status: MilestoneStatus.pending,
            dueOffsetDays: -3,
          ),
          MilestoneModel(
            id: 'm4',
            title: 'Nộp bài chính thức',
            status: MilestoneStatus.pending,
            dueOffsetDays: 0,
          ),
        ],
      );
    }
    return const AssignmentMilestonesData(
      idAssessment: 0,
      module: '',
      title: '',
      milestones: [],
    );
  }

  static final List<Map<String, dynamic>> resources = [
    {
      'title': 'Slide Tuần 7 — Kiểm định giả thuyết',
      'module': 'DATA201',
      'type': 'slide',
      'url': 'https://example.com/data201-w7-slides.pdf',
      'bookmarked': true,
    },
    {
      'title': 'Tài liệu đọc thêm — Hồi quy tuyến tính',
      'module': 'DATA201',
      'type': 'document',
      'url': 'https://example.com/linear-regression.pdf',
      'bookmarked': false,
    },
    {
      'title': 'Video hướng dẫn Python pandas',
      'module': 'COMP101',
      'type': 'video',
      'url': 'https://example.com/pandas-tutorial',
      'bookmarked': true,
    },
    {
      'title': 'Quiz tự luyện — Đại số tuyến tính',
      'module': 'MATH102',
      'type': 'quiz',
      'url': 'https://example.com/linear-algebra-quiz',
      'bookmarked': false,
    },
  ];
}
