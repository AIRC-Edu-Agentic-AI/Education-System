class AssignmentSubmission {
  final int studentId;
  final int idAssessment;
  final String courseCode;
  final String content;
  final DateTime submittedAt;
  final int? submittedDay;
  final String status;

  const AssignmentSubmission({
    required this.studentId,
    required this.idAssessment,
    required this.courseCode,
    required this.content,
    required this.submittedAt,
    this.submittedDay,
    required this.status,
  });

  factory AssignmentSubmission.fromJson(Map<String, dynamic> json) =>
      AssignmentSubmission(
        studentId: json['student_id'] ?? 0,
        idAssessment: json['id_assessment'] ?? 0,
        courseCode: json['course_code'] ?? '',
        content: json['content'] ?? '',
        submittedAt: json['submitted_at'] != null
            ? DateTime.parse(json['submitted_at'])
            : DateTime.now(),
        submittedDay: json['submitted_day'],
        status: json['status'] ?? 'submitted',
      );
}
