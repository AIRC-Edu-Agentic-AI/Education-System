enum MilestoneStatus { pending, inProgress, done, skipped }

extension MilestoneStatusX on MilestoneStatus {
  String get label => switch (this) {
        MilestoneStatus.pending => 'Chưa bắt đầu',
        MilestoneStatus.inProgress => 'Đang làm',
        MilestoneStatus.done => 'Hoàn thành',
        MilestoneStatus.skipped => 'Bỏ qua',
      };

  String get apiValue => switch (this) {
        MilestoneStatus.pending => 'pending',
        MilestoneStatus.inProgress => 'in_progress',
        MilestoneStatus.done => 'done',
        MilestoneStatus.skipped => 'skipped',
      };

  MilestoneStatus get next => switch (this) {
        MilestoneStatus.pending => MilestoneStatus.inProgress,
        MilestoneStatus.inProgress => MilestoneStatus.done,
        MilestoneStatus.done => MilestoneStatus.pending,
        MilestoneStatus.skipped => MilestoneStatus.pending,
      };

  static MilestoneStatus fromString(String s) => switch (s) {
        'in_progress' => MilestoneStatus.inProgress,
        'done' => MilestoneStatus.done,
        'skipped' => MilestoneStatus.skipped,
        _ => MilestoneStatus.pending,
      };
}

class MilestoneModel {
  final String id;
  final String title;
  final MilestoneStatus status;
  final int dueOffsetDays;

  const MilestoneModel({
    required this.id,
    required this.title,
    required this.status,
    required this.dueOffsetDays,
  });

  MilestoneModel copyWith({MilestoneStatus? status}) => MilestoneModel(
        id: id,
        title: title,
        status: status ?? this.status,
        dueOffsetDays: dueOffsetDays,
      );

  factory MilestoneModel.fromJson(Map<String, dynamic> json) => MilestoneModel(
        id: json['id'] ?? '',
        title: json['title'] ?? '',
        status: MilestoneStatusX.fromString(json['status'] ?? 'pending'),
        dueOffsetDays: json['due_offset_days'] ?? 0,
      );
}

class AssignmentMilestonesData {
  final int idAssessment;
  final String module;
  final String title;
  final List<MilestoneModel> milestones;

  const AssignmentMilestonesData({
    required this.idAssessment,
    required this.module,
    required this.title,
    required this.milestones,
  });

  factory AssignmentMilestonesData.fromJson(Map<String, dynamic> json) =>
      AssignmentMilestonesData(
        idAssessment: json['id_assessment'] ?? 0,
        module: json['module'] ?? '',
        title: json['title'] ?? '',
        milestones: (json['milestones'] as List? ?? [])
            .map((m) => MilestoneModel.fromJson(m))
            .toList(),
      );

  bool get isEmpty => milestones.isEmpty;

  AssignmentMilestonesData copyWithMilestone(
          String id, MilestoneStatus status) =>
      AssignmentMilestonesData(
        idAssessment: idAssessment,
        module: module,
        title: title,
        milestones: milestones
            .map((m) => m.id == id ? m.copyWith(status: status) : m)
            .toList(),
      );
}
