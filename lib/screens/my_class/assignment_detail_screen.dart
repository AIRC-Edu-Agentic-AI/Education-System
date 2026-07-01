import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:student_agent/core/theme/app_theme.dart';
import 'package:student_agent/models/assignment_submission_model.dart';
import 'package:student_agent/models/student_model.dart';
import 'package:student_agent/providers/providers.dart';

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
  final _contentController = TextEditingController();
  bool _submitting = false;
  AssignmentSubmission? _submission;

  @override
  void initState() {
    super.initState();
    _loadSubmission();
  }

  @override
  void dispose() {
    _contentController.dispose();
    super.dispose();
  }

  Future<void> _loadSubmission() async {
    final api = ref.read(apiServiceProvider);
    final studentId = ref.read(activeStudentIdProvider);
    final sub = await api.getSubmission(widget.assessmentId, studentId);
    if (!mounted) return;
    setState(() {
      _submission = sub;
      if (sub != null) _contentController.text = sub.content;
    });
  }

  Future<void> _submit(Assessment assessment) async {
    final content = _contentController.text.trim();
    if (content.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Vui lòng nhập nội dung hoặc link bài làm')),
      );
      return;
    }

    setState(() => _submitting = true);
    try {
      final api = ref.read(apiServiceProvider);
      final studentId = ref.read(activeStudentIdProvider);
      final sub = await api.submitAssignment(
        idAssessment: widget.assessmentId,
        studentId: studentId,
        content: content,
      );
      ref.invalidate(studentProvider);
      if (!mounted) return;
      setState(() {
        _submission = sub;
        _submitting = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Đã nộp bài thành công'),
          backgroundColor: AppTheme.accentGreen,
        ),
      );
    } catch (e) {
      if (!mounted) return;
      setState(() => _submitting = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Không thể nộp bài: $e')),
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

          final isSubmitted =
              assessment.isSubmitted || _submission != null;
          final isLate = assessment.isLate;

          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              _HeaderCard(assessment: assessment, isSubmitted: isSubmitted),
              const SizedBox(height: 16),
              const Text(
                'Hướng dẫn',
                style: TextStyle(
                  color: AppTheme.textPrimary,
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 8),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: AppTheme.surfaceCard,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: AppTheme.cardBorder),
                ),
                child: Text(
                  'Nộp bài bằng cách dán link Google Drive, GitHub, hoặc mô tả ngắn '
                  'về bài làm của bạn (giống Google Classroom).',
                  style: const TextStyle(
                    color: AppTheme.textSecondary,
                    fontSize: 13,
                    height: 1.45,
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Text(
                isSubmitted ? 'Bài đã nộp' : 'Nội dung bài làm',
                style: const TextStyle(
                  color: AppTheme.textPrimary,
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 8),
              TextField(
                controller: _contentController,
                readOnly: isSubmitted,
                maxLines: 6,
                decoration: InputDecoration(
                  hintText: 'https://drive.google.com/... hoặc mô tả bài làm',
                  filled: true,
                  fillColor: AppTheme.surfaceCard,
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                    borderSide: const BorderSide(color: AppTheme.cardBorder),
                  ),
                  enabledBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                    borderSide: const BorderSide(color: AppTheme.cardBorder),
                  ),
                ),
              ),
              if (isLate && isSubmitted) ...[
                const SizedBox(height: 10),
                const Row(
                  children: [
                    Icon(Icons.schedule_rounded,
                        size: 16, color: AppTheme.warning),
                    SizedBox(width: 6),
                    Text(
                      'Bài nộp sau hạn — có thể bị trừ điểm',
                      style: TextStyle(color: AppTheme.warning, fontSize: 12),
                    ),
                  ],
                ),
              ],
              if (_submission != null) ...[
                const SizedBox(height: 8),
                Text(
                  'Nộp lúc: ${_formatTime(_submission!.submittedAt)}',
                  style: const TextStyle(
                    color: AppTheme.textMuted,
                    fontSize: 11,
                  ),
                ),
              ],
              if (!isSubmitted) ...[
                const SizedBox(height: 20),
                SizedBox(
                  width: double.infinity,
                  child: FilledButton.icon(
                    onPressed: _submitting ? null : () => _submit(assessment),
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
                    label: Text(_submitting ? 'Đang nộp...' : 'Nộp bài'),
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
            ],
          );
        },
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

  const _HeaderCard({
    required this.assessment,
    required this.isSubmitted,
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
