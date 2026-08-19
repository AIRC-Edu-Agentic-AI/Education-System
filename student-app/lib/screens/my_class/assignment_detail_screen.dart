import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:student_agent/core/theme/app_theme.dart';
import 'package:student_agent/models/assignment_submission_model.dart';
import 'package:student_agent/models/student_model.dart';
import 'package:student_agent/providers/providers.dart';
import 'package:file_picker/file_picker.dart';
import 'dart:io';
import 'package:student_agent/models/instructor_feedback_model.dart';


class AssignmentDetailScreen extends ConsumerStatefulWidget {
  final String courseCode;
  final int assessmentId;

  const AssignmentDetailScreen({
    super.key,
    required this.courseCode,
    required this.assessmentId,
  });

  @override
  ConsumerState<AssignmentDetailScreen> createState() =>
      _AssignmentDetailScreenState();
}

class _AssignmentDetailScreenState extends ConsumerState<AssignmentDetailScreen> {
  File? _selectedFile;
  bool _submitting = false;
  List<AssignmentSubmission> _submissions = [];
  List<InstructorFeedback> _feedbacks = [];

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  @override
  void dispose() {
    super.dispose();
  }

  Future<void> _loadData() async {
    final api = ref.read(apiServiceProvider);
    final studentId = ref.read(activeStudentIdProvider);
    
    // Load submissions
    final submissions = await api.getSubmissions(widget.assessmentId, studentId);
    // Load feedbacks
    final feedbacks = await api.getFeedbacks(widget.assessmentId);
    
    if (!mounted) return;
    setState(() {
      _submissions = submissions;
      _feedbacks = feedbacks;
    });
  }

  Future<void> _pickFile() async {
    FilePickerResult? result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['pdf'],
    );
    
    if (result != null && result.files.single.path != null) {
      setState(() {
        _selectedFile = File(result.files.single.path!);
      });
    }
  }

  Future<void> _submitAssignment() async {
    if (_selectedFile == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Vui lòng chọn file PDF để nộp')),
      );
      return;
    }

    setState(() => _submitting = true);
    try {
      final api = ref.read(apiServiceProvider);
      final studentId = ref.read(activeStudentIdProvider);
      
      final submission = await api.submitAssignment(
        idAssessment: widget.assessmentId,
        studentId: studentId,
        file: _selectedFile!,
      );
      
      ref.invalidate(studentProvider);
      if (!mounted) return;
      
      setState(() {
        _submissions = [submission, ..._submissions];
        _selectedFile = null;
        _submitting = false;
      });
      
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Đã nộp bài thành công'),
          backgroundColor: AppTheme.accentGreen,
        ),
      );
    } catch (e) {
      if (!mounted) return;
      setState(() => _submitting = false);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Không thể nộp bài: $e')),
      );
    }
  }

  Future<void> _unsumbitAssignment(String submissionId) async {
    setState(() => _submitting = true);
    try {
      final api = ref.read(apiServiceProvider);
      await api.unsumbitAssignment(widget.assessmentId, submissionId);
      
      ref.invalidate(studentProvider);
      if (!mounted) return;
      
      setState(() {
        _submissions = _submissions.where((s) => s.id != submissionId).toList();
        _submitting = false;
      });
      
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Đã hủy nộp bài'),
          backgroundColor: AppTheme.warning,
        ),
      );
    } catch (e) {
      if (!mounted) return;
      setState(() => _submitting = false);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Không thể hủy nộp bài: $e')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final studentAsync = ref.watch(studentProvider);

    return Scaffold(
      backgroundColor: AppTheme.backgroundDark,
      appBar: AppBar(
        title: const Text('Chi tiết bài tập'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded, size: 18),
          onPressed: () => context.go('/my-class/${widget.courseCode}/assignments'),
        ),
      ),
      body: studentAsync.when(
        loading: () => const Center(
          child: CircularProgressIndicator(color: AppTheme.primaryBlue),
        ),
        error: (e, _) => Center(
          child: Text('Lỗi: $e', style: const TextStyle(color: AppTheme.danger)),
        ),
        data: (student) {
          final enrollment = student.enrollments
              .where((e) => e.codeModule == widget.courseCode)
              .firstOrNull;
          if (enrollment == null) {
            return const Center(
              child: Text(
                'Không tìm thấy lớp học',
                style: TextStyle(color: AppTheme.textSecondary),
              ),
            );
          }

          final assessment = enrollment.assessments
              .where((a) => a.idAssessment == widget.assessmentId)
              .firstOrNull;
          if (assessment == null) {
            return const Center(
              child: Text(
                'Không tìm thấy bài tập',
                style: TextStyle(color: AppTheme.textSecondary),
              ),
            );
          }

          final isSubmitted = _submissions.isNotEmpty;

          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              _HeaderCard(
                assessment: assessment,
                isSubmitted: isSubmitted,
                onUnsubmit: isSubmitted ? () => _unsumbitAssignment(_submissions.first.id) : null,
                isUnsubmitting: _submitting,
              ),
              const SizedBox(height: 16),
              _buildAssignmentMetadata(assessment),
              const SizedBox(height: 16),
              _buildDescriptionSection(assessment.description),
              const SizedBox(height: 16),
              _buildUploadGuidance(assessment),
              const SizedBox(height: 16),
              if (!isSubmitted) _buildFileUploadSection(),
              if (isSubmitted) ...[
                const Text(
                  'Bài đã nộp',
                  style: TextStyle(
                    color: AppTheme.textPrimary,
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 8),
                ..._submissions.map((submission) => _buildSubmittedFileCard(submission)),
              ],
              const SizedBox(height: 24),
              _buildScoreAndFeedbackSection(assessment),
            ],
          );
        },
      ),
    );
  }

  Widget _buildUploadGuidance(Assessment assessment) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.surfaceCard,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppTheme.cardBorder),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Thông tin nộp bài',
            style: TextStyle(
              color: AppTheme.textPrimary,
              fontSize: 14,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 10),
          Text(
            'Định dạng: ${assessment.allowedFormats.isEmpty ? 'PDF' : assessment.allowedFormats.join(', ').toUpperCase()}',
            style: const TextStyle(color: AppTheme.textSecondary, fontSize: 13),
          ),
          const SizedBox(height: 6),
          Text(
            'Dung lượng tối đa: ${assessment.maxFileSizeMb} MB',
            style: const TextStyle(color: AppTheme.textSecondary, fontSize: 13),
          ),
          const SizedBox(height: 10),
          const Text(
            'Lưu ý: Nộp đúng định dạng và nội dung theo đề bài. File sẽ được ghi nhận vào hệ thống và có thể được chấm điểm bởi giảng viên.',
            style: TextStyle(color: AppTheme.textSecondary, fontSize: 12, height: 1.45),
          ),
        ],
      ),
    );
  }

  Widget _buildAssignmentMetadata(Assessment assessment) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.surfaceCard,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppTheme.cardBorder),
      ),
      child: Column(
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  assessment.title.isNotEmpty ? assessment.title : '${assessment.type} · ${assessment.weight.round()}% weight',
                  style: const TextStyle(
                    color: AppTheme.textPrimary,
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                decoration: BoxDecoration(
                  color: assessment.status.toLowerCase() == 'active'
                      ? AppTheme.accentGreen.withAlpha(30)
                      : AppTheme.warning.withAlpha(30),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  assessment.statusLabel,
                  style: TextStyle(
                    color: assessment.status.toLowerCase() == 'active'
                        ? AppTheme.accentGreen
                        : AppTheme.warning,
                    fontSize: 11,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ],
          ),
          if (assessment.createdAt != null || assessment.updatedAt != null) ...[
            const SizedBox(height: 12),
            if (assessment.createdAt != null)
              _buildInfoLine('Created', _formatTime(assessment.createdAt!)),
            if (assessment.updatedAt != null)
              _buildInfoLine('Updated', _formatTime(assessment.updatedAt!)),
          ],
        ],
      ),
    );
  }

  Widget _buildDescriptionSection(String description) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.surfaceCard,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppTheme.cardBorder),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Mô tả bài tập',
            style: TextStyle(
              color: AppTheme.textPrimary,
              fontSize: 14,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 10),
          Text(
            description.isNotEmpty ? description : 'Chưa có mô tả cho bài tập này.',
            style: const TextStyle(
              color: AppTheme.textSecondary,
              fontSize: 13,
              height: 1.5,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInfoChip(String label, String value) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: AppTheme.backgroundDark,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppTheme.cardBorder),
      ),
      child: Text(
        '$label: $value',
        style: const TextStyle(color: AppTheme.textSecondary, fontSize: 12),
      ),
    );
  }

  Widget _buildInfoLine(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(top: 6),
      child: Row(
        children: [
          Text(
            '$label: ',
            style: const TextStyle(
              color: AppTheme.textPrimary,
              fontSize: 12,
              fontWeight: FontWeight.w600,
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(color: AppTheme.textSecondary, fontSize: 12),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFileUploadSection() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.surfaceCard,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppTheme.cardBorder),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Nộp bài',
            style: TextStyle(
              color: AppTheme.textPrimary,
              fontSize: 14,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  decoration: BoxDecoration(
                    color: AppTheme.backgroundDark,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: AppTheme.cardBorder),
                  ),
                  child: Text(
                    _selectedFile != null
                        ? _selectedFile!.path.split('/').last
                        : 'Chưa có file nào được chọn',
                    style: TextStyle(
                      color: _selectedFile != null
                          ? AppTheme.textPrimary
                          : AppTheme.textMuted,
                      fontSize: 13,
                    ),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ),
              const SizedBox(width: 8),
              ElevatedButton.icon(
                onPressed: _pickFile,
                icon: Container(
                  width: 34,
                  height: 34,
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      colors: [Color(0xFF4CAFEC), Color(0xFF2B6DFF)],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                    borderRadius: BorderRadius.circular(10),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withAlpha(36),
                        blurRadius: 10,
                        offset: const Offset(0, 3),
                      ),
                    ],
                  ),
                  child: const Icon(
                    Icons.attach_file_rounded,
                    size: 18,
                    color: Colors.white,
                  ),
                ),
                label: const Text('Chọn file'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppTheme.primaryBlue,
                  padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(10),
                  ),
                  elevation: 0,
                ),
              ),
            ],
          ),
          if (_selectedFile != null) ...[
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: AppTheme.backgroundDark,
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Row(
                children: [
                  Icon(Icons.picture_as_pdf_rounded,
                      size: 20, color: AppTheme.danger),
                  SizedBox(width: 8),
                  Text(
                    'File PDF sẵn sàng để nộp',
                    style: TextStyle(
                      color: AppTheme.textSecondary,
                      fontSize: 12,
                    ),
                  ),
                ],
              ),
            ),
          ],
          const SizedBox(height: 16),
          SizedBox(
            width: double.infinity,
            child: FilledButton.icon(
              onPressed: _submitting ? null : _submitAssignment,
              icon: _submitting
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: Colors.white,
                      ),
                    )
                  : const Icon(Icons.upload_rounded),
              label: Text(_submitting ? 'Đang nộp...' : 'Thêm bài nộp'),
              style: FilledButton.styleFrom(
                backgroundColor: AppTheme.accentGreen,
                padding: const EdgeInsets.symmetric(vertical: 14),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSubmittedFileCard(AssignmentSubmission submission) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppTheme.surfaceCard,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppTheme.cardBorder),
      ),
      child: Row(
        children: [
          Icon(
            submission.fileType == 'pdf'
                ? Icons.picture_as_pdf_rounded
                : Icons.insert_drive_file_rounded,
            color: submission.fileType == 'pdf' ? AppTheme.danger : AppTheme.primaryBlue,
            size: 32,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  submission.fileName,
                  style: const TextStyle(
                    color: AppTheme.textPrimary,
                    fontSize: 13,
                    fontWeight: FontWeight.w500,
                  ),
                  overflow: TextOverflow.ellipsis,
                ),
                Text(
                  'Nộp lúc: ${_formatTime(submission.submittedAt)}',
                  style: const TextStyle(
                    color: AppTheme.textMuted,
                    fontSize: 11,
                  ),
                ),
              ],
            ),
          ),
          IconButton(
            icon: const Icon(Icons.remove_red_eye_rounded, size: 20),
            onPressed: () => _previewPDF(submission.fileUrl),
            tooltip: 'Xem trước',
            color: AppTheme.primaryBlue,
          ),
        ],
      ),
    );
  }

  Widget _buildFeedbackCard(InstructorFeedback feedback) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppTheme.surfaceCard,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: AppTheme.accentGreen.withValues(alpha: 0.25),
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const CircleAvatar(
            radius: 16,
            backgroundColor: AppTheme.primaryBlue,
            child: Icon(Icons.person, size: 16, color: Colors.white),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Giảng viên',
                  style: TextStyle(
                    color: AppTheme.textPrimary,
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                Text(
                  feedback.content,
                  style: const TextStyle(
                    color: AppTheme.textSecondary,
                    fontSize: 13,
                  ),
                ),
                if (feedback.score != null) ...[
                  const SizedBox(height: 4),
                  Row(
                    children: [
                      const Icon(Icons.star_rounded,
                          size: 16, color: AppTheme.warning),
                      const SizedBox(width: 4),
                      Text(
                        'Điểm: ${feedback.score}',
                        style: const TextStyle(
                          color: AppTheme.textPrimary,
                          fontSize: 12,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ],
                  ),
                ],
                Text(
                  _formatTime(feedback.createdAt),
                  style: const TextStyle(
                    color: AppTheme.textMuted,
                    fontSize: 10,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildScoreAndFeedbackSection(Assessment assessment) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.surfaceCard,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppTheme.cardBorder),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.grade_outlined, color: AppTheme.warning, size: 22),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Score & Instructor Feedback',
                  style: TextStyle(
                    color: AppTheme.textPrimary,
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  assessment.score == null
                      ? 'Score: Not graded yet'
                      : 'Score: ${assessment.score!.toStringAsFixed(1)}%',
                  style: const TextStyle(
                    color: AppTheme.textPrimary,
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 10),
                if (_feedbacks.isEmpty)
                  const Text(
                    'No instructor feedback yet.',
                    style: TextStyle(color: AppTheme.textSecondary, fontSize: 13),
                  )
                else
                  ..._feedbacks.map(_buildFeedbackCard),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _previewPDF(String url) async {
    // TODO: Implement PDF preview with pdfx package
    // Show dialog with PDF viewer
    showDialog(
      context: context,
      builder: (context) => Dialog(
        backgroundColor: AppTheme.backgroundDark,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        child: Container(
          height: MediaQuery.of(context).size.height * 0.8,
          width: MediaQuery.of(context).size.width * 0.9,
          padding: const EdgeInsets.all(16),
          child: Column(
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text(
                    'Xem trước file',
                    style: TextStyle(
                      color: AppTheme.textPrimary,
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close_rounded, color: AppTheme.textPrimary),
                    onPressed: () => Navigator.pop(context),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Expanded(
                child: Container(
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Center(
                    child: Text(
                      'PDF Viewer sẽ được hiển thị ở đây',
                      style: TextStyle(color: Colors.black54),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _formatTime(DateTime t) {
    final local = t.toLocal();
    return '${local.day}/${local.month}/${local.year} '
        '${local.hour.toString().padLeft(2, '0')}:'
        '${local.minute.toString().padLeft(2, '0')}';
  }
}

class _HeaderCard extends StatelessWidget {
  final Assessment assessment;
  final bool isSubmitted;
  final VoidCallback? onUnsubmit;
  final bool isUnsubmitting;

  const _HeaderCard({
    required this.assessment,
    required this.isSubmitted,
    this.onUnsubmit,
    required this.isUnsubmitting,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.surfaceCard,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: isSubmitted
              ? AppTheme.accentGreen.withValues(alpha: 0.35)
              : AppTheme.cardBorder,
        ),
      ),
      child: Row(
        children: [
          Icon(
            isSubmitted
                ? Icons.check_circle_outline_rounded
                : Icons.assignment_outlined,
            color: isSubmitted ? AppTheme.accentGreen : AppTheme.warning,
            size: 28,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '${assessment.type} · ${assessment.weight.round()}% trọng số',
                  style: const TextStyle(
                    color: AppTheme.textPrimary,
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  isSubmitted
                      ? 'Đã nộp · hạn ngày ${assessment.dueDate}'
                      : 'Hạn nộp: ngày ${assessment.dueDate}',
                  style: const TextStyle(
                    color: AppTheme.textSecondary,
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ),
          if (isSubmitted && onUnsubmit != null)
            TextButton.icon(
              onPressed: isUnsubmitting ? null : onUnsubmit,
              icon: isUnsubmitting
                  ? const SizedBox(
                      width: 14,
                      height: 14,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: AppTheme.warning,
                      ),
                    )
                  : const Icon(Icons.undo_rounded, size: 16),
              label: Text(isUnsubmitting ? '' : 'Hủy nộp'),
              style: TextButton.styleFrom(
                foregroundColor: AppTheme.warning,
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                minimumSize: Size.zero,
                tapTargetSize: MaterialTapTargetSize.shrinkWrap,
              ),
            ),
        ],
      ),
    );
  }
}

extension _EnrollmentSearch on Iterable<Enrollment> {
  Enrollment? get firstOrNull => isEmpty ? null : first;
}

extension _AssessmentSearch on Iterable<Assessment> {
  Assessment? get firstOrNull => isEmpty ? null : first;
}
