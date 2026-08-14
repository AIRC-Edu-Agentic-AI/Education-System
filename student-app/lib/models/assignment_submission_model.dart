class AssignmentSubmission {
  final String id;
  final int studentId;
  final int idAssessment;
  final String courseCode;
  final String fileName;
  final String fileUrl;
  final String fileType;
  final DateTime submittedAt;
  final int? submittedDay;
  final String status;
  final double? score;
  final String? feedback;

  const AssignmentSubmission({
    required this.id,
    required this.studentId,
    required this.idAssessment,
    required this.courseCode,
    required this.fileName,
    required this.fileUrl,
    required this.fileType,
    required this.submittedAt,
    this.submittedDay,
    required this.status,
    this.score,
    this.feedback,
  });

  factory AssignmentSubmission.fromJson(Map<String, dynamic> json) =>
      AssignmentSubmission(
        id: (json['_id'] ?? json['id'] ?? '').toString(),
        studentId: json['student_id'] ?? 0,
        idAssessment: json['id_assessment'] ?? 0,
        courseCode: json['course_code'] ?? '',
        fileName: json['file_name'] ?? '',
        fileUrl: json['file_url'] ?? '',
        fileType: json['file_type'] ?? '',  
        submittedAt: json['submitted_at'] != null
            ? DateTime.parse(json['submitted_at'])
            : DateTime.now(),
        submittedDay: json['submitted_day'],
        status: json['status'] ?? 'submitted',
        score: json['score'] != null ? (json['score'] as num).toDouble() : null,
        feedback: json['feedback'],
      );
}
