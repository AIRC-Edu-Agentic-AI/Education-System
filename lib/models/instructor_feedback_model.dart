class InstructorFeedback {
  final int id;
  final int assessmentId;
  final String content;
  final double? score;
  final DateTime createdAt;
  final String instructorName;

  const InstructorFeedback({
    required this.id,
    required this.assessmentId,
    required this.content,
    this.score,
    required this.createdAt,
    required this.instructorName,
  });

  factory InstructorFeedback.fromJson(Map<String, dynamic> json) =>
      InstructorFeedback(
        id: json['id'] ?? 0,
        assessmentId: json['assessment_id'] ?? 0,
        content: json['content'] ?? '',
        score: json['score']?.toDouble(),
        createdAt: json['created_at'] != null
            ? DateTime.parse(json['created_at'])
            : DateTime.now(),
        instructorName: json['instructor_name'] ?? 'Giảng viên',
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'assessment_id': assessmentId,
        'content': content,
        'score': score,
        'created_at': createdAt.toIso8601String(),
        'instructor_name': instructorName,
      };
}