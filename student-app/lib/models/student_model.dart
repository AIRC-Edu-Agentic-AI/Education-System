/// Parse a server timestamp. The backend writes naive UTC (no timezone suffix),
/// so we append 'Z' when absent and convert to local — otherwise DateTime.parse
/// treats it as local and times are off by the timezone offset.
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

class StudentModel {
  final String id;
  final String auth0Id;
  final int studentId;
  final String fullName;
  final String shortName;
  final Demographics demographics;
  final List<Enrollment> enrollments;
  final RiskProfile risk;
  final List<String> prerequisiteGaps;

  const StudentModel({
    required this.id,
    required this.auth0Id,
    required this.studentId,
    required this.fullName,
    required this.shortName,
    required this.demographics,
    required this.enrollments,
    required this.risk,
    required this.prerequisiteGaps,
  });

  factory StudentModel.fromJson(Map<String, dynamic> json) => StudentModel(
        id: json['_id'] ?? '',
        auth0Id: json['auth0_id'] ?? '',
        studentId: json['student_id'] ?? 0,
        fullName: json['full_name'] ?? '',
        shortName: json['short_name'] ?? '',
        demographics: Demographics.fromJson(json['demographics'] ?? {}),
        enrollments: (json['enrollments'] as List? ?? [])
            .map((e) => Enrollment.fromJson(e))
            .toList(),
        risk: RiskProfile.fromJson(json['risk'] ?? {}),
        prerequisiteGaps:
            List<String>.from(json['prerequisite_gaps'] ?? []),
      );
}

class Demographics {
  final String gender;
  final String ageBand;
  final String region;
  final String highestEducation;
  final String imdBand;
  final bool disability;
  final int numPrevAttempts;
  final int studiedCredits;

  const Demographics({
    required this.gender,
    required this.ageBand,
    required this.region,
    required this.highestEducation,
    required this.imdBand,
    required this.disability,
    required this.numPrevAttempts,
    required this.studiedCredits,
  });

  factory Demographics.fromJson(Map<String, dynamic> json) => Demographics(
        gender: json['gender'] ?? '',
        ageBand: json['age_band'] ?? '',
        region: json['region'] ?? '',
        highestEducation: json['highest_education'] ?? '',
        imdBand: json['imd_band'] ?? '',
        disability: json['disability'] ?? false,
        numPrevAttempts: json['num_prev_attempts'] ?? 0,
        studiedCredits: json['studied_credits'] ?? 0,
      );
}

class Enrollment {
  final String codeModule;
  final String codePresentation;
  final String title;
  final int moduleLength;
  final String? finalResult;
  final List<Assessment> assessments;
  final VleSummary vleSummary;

  const Enrollment({
    required this.codeModule,
    required this.codePresentation,
    this.title = '',
    required this.moduleLength,
    this.finalResult,
    required this.assessments,
    required this.vleSummary,
  });

  factory Enrollment.fromJson(Map<String, dynamic> json) => Enrollment(
        codeModule: json['code_module'] ?? '',
        codePresentation: json['code_presentation'] ?? '',
        title: json['title'] ?? '',
        moduleLength: json['module_length'] ?? 30,
        finalResult: json['final_result'],
        assessments: (json['assessments'] as List? ?? [])
            .map((a) => Assessment.fromJson(a))
            .toList(),
        vleSummary: VleSummary.fromJson(json['vle_summary'] ?? {}),
      );

  String get displayName =>
      title.isNotEmpty ? title : '$codeModule ($codePresentation)';
  String get codeLabel => '$codeModule · $codePresentation';
}

class Assessment {
  final int idAssessment;
  final String type;
  final int dueDate;
  final double weight;
  final double? score;
  final int? submittedDate;
  final bool isBanked;

  const Assessment({
    required this.idAssessment,
    required this.type,
    required this.dueDate,
    required this.weight,
    this.score,
    this.submittedDate,
    required this.isBanked,
  });

  bool get isSubmitted => submittedDate != null;
  bool get isLate => submittedDate != null && submittedDate! > dueDate;

  factory Assessment.fromJson(Map<String, dynamic> json) => Assessment(
        idAssessment: json['id_assessment'] ?? 0,
        type: json['type'] ?? '',
        dueDate: json['due_date'] ?? 0,
        weight: (json['weight'] ?? 0).toDouble(),
        score: json['score']?.toDouble(),
        submittedDate: json['submitted_date'],
        isBanked: json['is_banked'] ?? false,
      );
}

class VleSummary {
  final int totalClicks;
  final int lastActiveDay;
  final Map<String, int> byActivityType;
  final List<int> weeklyClicks;

  const VleSummary({
    required this.totalClicks,
    required this.lastActiveDay,
    required this.byActivityType,
    required this.weeklyClicks,
  });

  factory VleSummary.fromJson(Map<String, dynamic> json) => VleSummary(
        totalClicks: json['total_clicks'] ?? 0,
        lastActiveDay: json['last_active_day'] ?? 0,
        byActivityType: Map<String, int>.from(json['by_activity_type'] ?? {}),
        weeklyClicks: List<int>.from(json['weekly_clicks'] ?? []),
      );
}

class RiskProfile {
  final int tier;
  final double score;
  final List<String> flags;
  final DateTime computedAt;

  const RiskProfile({
    required this.tier,
    required this.score,
    required this.flags,
    required this.computedAt,
  });

  factory RiskProfile.fromJson(Map<String, dynamic> json) => RiskProfile(
        tier: json['tier'] ?? 1,
        score: (json['score'] ?? 0.0).toDouble(),
        flags: List<String>.from(json['flags'] ?? []),
        computedAt: parseServerTime(json['computed_at']),
      );

  String get tierLabel => switch (tier) {
        1 => 'Tier 1 — Đúng tiến độ',
        2 => 'Tier 2 — Cần hỗ trợ',
        3 => 'Tier 3 — Can thiệp ngay',
        _ => 'Không xác định',
      };
}

class RiskPoint {
  final int week;
  final double score;
  final int tier;

  const RiskPoint({required this.week, required this.score, required this.tier});

  factory RiskPoint.fromJson(Map<String, dynamic> json) => RiskPoint(
        week: json['week'] ?? 0,
        score: (json['score'] ?? 0.0).toDouble(),
        tier: json['tier'] ?? 1,
      );
}

class NotificationAction {
  final String label;
  final String action;
  final Map<String, dynamic> payload;

  const NotificationAction({
    required this.label,
    required this.action,
    required this.payload,
  });

  factory NotificationAction.fromJson(Map<String, dynamic> json) =>
      NotificationAction(
        label: json['label'] ?? '',
        action: json['action'] ?? '',
        payload: Map<String, dynamic>.from(json['payload'] ?? {}),
      );
}

class NotificationModel {
  final String id;
  final int studentId;
  final String type;
  final String title;
  final String body;
  final bool read;
  final DateTime createdAt;
  final List<NotificationAction> actionOptions;

  const NotificationModel({
    required this.id,
    required this.studentId,
    required this.type,
    required this.title,
    required this.body,
    required this.read,
    required this.createdAt,
    this.actionOptions = const [],
  });

  factory NotificationModel.fromJson(Map<String, dynamic> json) {
    final payload = json['payload'] is Map ? json['payload'] as Map<String, dynamic> : <String, dynamic>{};
    final title = payload['title'] ?? json['title'] ?? '';
    final body = payload['body'] ?? json['content'] ?? json['body'] ?? '';
    final createdAtValue = json['created_at'] ?? json['createdAt'];

    return NotificationModel(
      id: json['_id']?.toString() ?? json['id'] ?? '',
      studentId: json['student_id'] ?? json['receiverId'] ?? json['studentId'] ?? 0,
      type: json['type'] ?? 'reminder',
      title: title.toString(),
      body: body.toString(),
      read: json['read'] ?? json['is_read'] ?? false,
      createdAt: parseServerTime(createdAtValue),
      actionOptions: (json['action_options'] as List? ?? [])
          .map((a) => NotificationAction.fromJson(a))
          .toList(),
    );
  }

  NotificationModel copyWith({bool? read}) => NotificationModel(
        id: id,
        studentId: studentId,
        type: type,
        title: title,
        body: body,
        read: read ?? this.read,
        createdAt: createdAt,
        actionOptions: actionOptions,
      );
}

class WeeklySchedule {
  final int currentWeek;
  final int totalWeeks;
  final int streakDays;
  final List<WeekItem> lectures;
  final List<WeekItem> classes;
  final List<WeekItem> assignments;
  final List<WeekItem> exams;

  const WeeklySchedule({
    required this.currentWeek,
    required this.totalWeeks,
    required this.streakDays,
    required this.lectures,
    required this.classes,
    required this.assignments,
    required this.exams,
  });

  factory WeeklySchedule.fromJson(Map<String, dynamic> json) => WeeklySchedule(
        currentWeek: json['current_week'] ?? 1,
        totalWeeks: json['total_weeks'] ?? 30,
        streakDays: json['streak_days'] ?? 0,
        lectures: (json['lectures'] as List? ?? [])
            .map((i) => WeekItem.fromJson(i))
            .toList(),
        classes: (json['classes'] as List? ?? [])
            .map((i) => WeekItem.fromJson(i))
            .toList(),
        assignments: (json['assignments'] as List? ?? [])
            .map((i) => WeekItem.fromJson(i))
            .toList(),
        exams: (json['exams'] as List? ?? [])
            .map((i) => WeekItem.fromJson(i))
            .toList(),
      );
}

class WeekItem {
  final String title;
  final String subtitle;
  final DateTime dateTime;
  final bool isCompleted;
  final bool isUrgent;

  const WeekItem({
    required this.title,
    required this.subtitle,
    required this.dateTime,
    this.isCompleted = false,
    this.isUrgent = false,
  });

  factory WeekItem.fromJson(Map<String, dynamic> json) => WeekItem(
        title: json['title'] ?? '',
        subtitle: json['subtitle'] ?? '',
        dateTime: json['date_time'] != null
            ? DateTime.parse(json['date_time'])
            : DateTime.now(),
        isCompleted: json['is_completed'] ?? false,
        isUrgent: json['is_urgent'] ?? false,
      );
}
