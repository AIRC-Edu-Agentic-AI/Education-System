class ClassComment {
  final int id;
  final int assessmentId;
  final int studentId;
  final String studentName;
  final String content;
  final bool isInstructor;
  final DateTime createdAt;

  const ClassComment({
    required this.id,
    required this.assessmentId,
    required this.studentId,
    required this.studentName,
    required this.content,
    required this.isInstructor,
    required this.createdAt,
  });

  factory ClassComment.fromJson(Map<String, dynamic> json) => ClassComment(
        id: json['id'] ?? 0,
        assessmentId: json['assessment_id'] ?? 0,
        studentId: json['student_id'] ?? 0,
        studentName: json['student_name'] ?? 'Học sinh',
        content: json['content'] ?? '',
        isInstructor: json['is_instructor'] ?? false,
        createdAt: json['created_at'] != null
            ? DateTime.parse(json['created_at'])
            : DateTime.now(),
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'assessment_id': assessmentId,
        'student_id': studentId,
        'student_name': studentName,
        'content': content,
        'is_instructor': isInstructor,
        'created_at': createdAt.toIso8601String(),
      };
}