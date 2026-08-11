import 'package:student_agent/models/assignment_milestone_model.dart';
import 'package:student_agent/models/student_model.dart';

import 'package:student_agent/models/course_model.dart';

import 'package:student_agent/data/mock/mock_message_store.dart';
class MockData {
  static final StudentModel student = StudentModel(
    id: 'mock_student_001',
    auth0Id: 'auth0|mock_student_001',
    studentId: 28400,
    fullName: 'Nguyen Van An',
    shortName: 'Van An',
    demographics: const Demographics(
      gender: 'M',
      ageBand: '25-35',
      region: 'Hanoi',
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
        title: 'Data Analysis & Statistics',
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
      // Linear Algebra — mixed
      const Enrollment(
        codeModule: 'MATH102',
        codePresentation: '2024A',
        title: 'Linear Algebra',
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
      // Python Programming — strong
      const Enrollment(
        codeModule: 'COMP101',
        codePresentation: '2024A',
        title: 'Python Programming',
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
      // Inferential Statistics — on track
      const Enrollment(
        codeModule: 'STAT110',
        codePresentation: '2024A',
        title: 'Inferential Statistics & Probability',
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
    prerequisiteGaps: const ['Basic Statistics', 'Linear Algebra'],
  );

  static final WeeklySchedule weeklySchedule = WeeklySchedule(
    currentWeek: 7,
    totalWeeks: 30,
    streakDays: 12,
    lectures: [
      WeekItem(
        title: 'Data Analysis & Statistics',
        subtitle: 'Mon, 08:00',
        dateTime: DateTime.now().add(const Duration(days: 1)),
        isCompleted: false,
      ),
      WeekItem(
        title: 'Linear Algebra',
        subtitle: 'Wed, 10:00',
        dateTime: DateTime.now().add(const Duration(days: 3)),
        isCompleted: false,
      ),
      WeekItem(
        title: 'Hypothesis Testing',
        subtitle: 'Fri, 14:00',
        dateTime: DateTime.now().add(const Duration(days: 5)),
        isCompleted: false,
      ),
    ],
    classes: [
      WeekItem(
        title: 'Python Programming Lab',
        subtitle: 'Tue, 13:00 · Room B204',
        dateTime: DateTime.now().add(const Duration(days: 2)),
        isCompleted: false,
      ),
      WeekItem(
        title: 'Inferential Statistics & Probability',
        subtitle: 'Thu, 09:00 · Online',
        dateTime: DateTime.now().add(const Duration(days: 4)),
        isCompleted: false,
      ),
    ],
    assignments: [
      WeekItem(
        title: 'TMA-02 — Regression Analysis',
        subtitle: 'Due before Friday',
        dateTime: DateTime.now().add(const Duration(days: 5)),
        isCompleted: false,
        isUrgent: true,
      ),
      WeekItem(
        title: 'CMA — Linear Algebra',
        subtitle: 'Due before Saturday',
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
      title: 'TMA-02 — Data Analysis due soon',
      body: '3 days remaining (due day 49). Please start early.',
      read: false,
      createdAt: DateTime.now().subtract(const Duration(hours: 2)),
      actionOptions: [
        const NotificationAction(
          label: 'Plan study',
          action: 'open_chat',
          payload: {'message': 'Help me create a study plan to complete TMA-02 for Data Analysis'},
        ),
        const NotificationAction(
          label: 'Remind later',
          action: 'snooze',
          payload: {},
        ),
      ],
    ),
    NotificationModel(
      id: 'notif_002',
      studentId: 28400,
      type: 'reminder',
      title: 'Daily Review',
      body: 'You have 4 flashcards due for review under the SM-2 schedule.',
      read: false,
      createdAt: DateTime.now().subtract(const Duration(hours: 5)),
      actionOptions: [
        const NotificationAction(
          label: 'Ask Assistant',
          action: 'open_chat',
          payload: {'message': 'What should I review today?'},
        ),
      ],
    ),
  ];

  static final List<Map<String, dynamic>> studyPlanSessions = [
    {
      'subject': 'Week 6 Review — Data Analysis',
      'type': 'review',
      'duration': 45,
      'day': 'Mon',
      'time': '19:00',
      'sm2_interval': 3,
    },
    {
      'subject': 'Week 7 Reading Material',
      'type': 'new',
      'duration': 60,
      'day': 'Tue',
      'time': '20:00',
      'sm2_interval': null,
    },
    {
      'subject': 'TMA-02 Practice',
      'type': 'practice',
      'duration': 90,
      'day': 'Wed',
      'time': '19:30',
      'sm2_interval': null,
    },
    {
      'subject': 'Week 5–6 Flashcards',
      'type': 'spaced_rep',
      'duration': 20,
      'day': 'Thu',
      'time': '08:00',
      'sm2_interval': 7,
    },
    {
      'subject': 'Finalize TMA-02',
      'type': 'assignment',
      'duration': 120,
      'day': 'Fri',
      'time': '19:00',
      'sm2_interval': null,
    },
  ];

  static final Map<String, dynamic> knowledgeState = {
    'Basic Statistics': {
      'mastery': 0.35,
      'last_updated': '2025-01-10',
      'evidence_count': 2,
    },
    'Linear Algebra': {
      'mastery': 0.28,
      'last_updated': '2025-01-12',
      'evidence_count': 1,
    },
    'Linear Regression': {
      'mastery': 0.55,
      'last_updated': '2025-01-18',
      'evidence_count': 3,
    },
    'Hypothesis Testing': {
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
        title: 'TMA-02 — Regression Analysis',
        milestones: [
          MilestoneModel(
            id: 'm1',
            title: 'Read prompt & reference materials',
            status: MilestoneStatus.done,
            dueOffsetDays: -14,
          ),
          MilestoneModel(
            id: 'm2',
            title: 'Perform initial data analysis',
            status: MilestoneStatus.inProgress,
            dueOffsetDays: -7,
          ),
          MilestoneModel(
            id: 'm3',
            title: 'Write draft report',
            status: MilestoneStatus.pending,
            dueOffsetDays: -3,
          ),
          MilestoneModel(
            id: 'm4',
            title: 'Final submission',
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
      'title': 'Week 7 Slides — Hypothesis Testing',
      'module': 'DATA201',
      'type': 'slide',
      'url': 'https://example.com/data201-w7-slides.pdf',
      'bookmarked': true,
    },
    {
      'title': 'Supplementary Reading — Linear Regression',
      'module': 'DATA201',
      'type': 'document',
      'url': 'https://example.com/linear-regression.pdf',
      'bookmarked': false,
    },
    {
      'title': 'Python pandas Tutorial Video',
      'module': 'COMP101',
      'type': 'video',
      'url': 'https://example.com/pandas-tutorial',
      'bookmarked': true,
    },
    {
      'title': 'Practice Quiz — Linear Algebra',
      'module': 'MATH102',
      'type': 'quiz',
      'url': 'https://example.com/linear-algebra-quiz',
      'bookmarked': false,
    },
  ];

    // ── Course Communication ──────────────────────────────────────
  static List<CourseModel> get courses {
    final now = DateTime.now();
    return student.enrollments.map((e) {
      return CourseModel(
        id: 'mock_course_${e.codeModule}',
        courseCode: e.codeModule,
        title: e.title,
        presentation: e.codePresentation,
        term: '2024A',
        instructors: const [10001],
        classReps: const [28501],
        members: [student.studentId],
        status: 'active',
        settings: const {},
        createdAt: now,
        updatedAt: now,
      );
    }).toList();
  }

  static List<CourseChannel> channelsFor(String courseCode) {
    final now = DateTime.now();
    return [
      CourseChannel(
        id: 'mock_${courseCode}_announcement',
        courseCode: courseCode,
        type: 'announcement',
        name: 'Class Announcement',
        isReadOnly: true,
        allowedPostRoles: const ['instructor', 'class_rep'],
        status: 'active',
        createdAt: now,
        updatedAt: now,
      ),
      CourseChannel(
        id: 'mock_${courseCode}_discussion',
        courseCode: courseCode,
        type: 'discussion',
        name: 'General Discussion',
        isReadOnly: false,
        allowedPostRoles: const ['student', 'instructor', 'class_rep'],
        status: 'active',
        createdAt: now,
        updatedAt: now,
      ),
    ];
  }

    static List<CourseMessage> seedMessagesFor(String channelId) {
    final now = DateTime.now();
    final courseCode = MockMessageStore.courseCodeFromChannelId(channelId);

    // ── Announcement channel ──
    if (channelId.endsWith('_announcement')) {
      const rootId = 'mock_ann_root_1';
      return [
        CourseMessage(
          id: rootId,
          channelId: channelId,
          courseCode: courseCode,
          senderId: 10001,
          senderRole: 'instructor',
          content: 'Reminder: TMA-02 is due by day 49. Please check the rubric on LMS.',
          createdAt: now.subtract(const Duration(hours: 5)),
        ),
        CourseMessage(
          id: 'mock_ann_reply_1',
          channelId: channelId,
          courseCode: courseCode,
          senderId: 28400,
          senderRole: 'student',
          content: 'May I submit 1 day late?',
          createdAt: now.subtract(const Duration(hours: 4)),
          parentId: rootId,
        ),
        CourseMessage(
          id: 'mock_ann_reply_2',
          channelId: channelId,
          courseCode: courseCode,
          senderId: 28501,
          senderRole: 'class_rep',
          content: 'Per class policy, late submissions are not allowed. If you have special circumstances, email the instructor.',
          createdAt: now.subtract(const Duration(hours: 3)),
          parentId: rootId,
        ),
      ];
    }

    // ── Discussion channel ──
    if (channelId.endsWith('_discussion')) {
      return [
        CourseMessage(
          id: 'mock_disc_1',
          channelId: channelId,
          courseCode: courseCode,
          senderId: 28400,
          senderRole: 'student',
          content: 'Does anyone have the lecture slides for linear regression this week?',
          createdAt: now.subtract(const Duration(hours: 6)),
        ),
        CourseMessage(
          id: 'mock_disc_2',
          channelId: channelId,
          courseCode: courseCode,
          senderId: 28501,
          senderRole: 'class_rep',
          content: 'Week 7 slides are available in the Resource Center under DATA201.',
          createdAt: now.subtract(const Duration(hours: 5)),
        ),
      ];
    }

    return [];
  }
}
