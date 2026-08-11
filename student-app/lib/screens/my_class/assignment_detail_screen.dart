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
import 'package:student_agent/models/class_comment_model.dart';


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
  List<ClassComment> _classComments = [];
  final TextEditingController _commentController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  @override
  void dispose() {
    _commentController.dispose();
    super.dispose();
  }

  Future<void> _loadData() async {
    final api = ref.read(apiServiceProvider);
    final studentId = ref.read(activeStudentIdProvider);
    
    // Load submissions
    final submissions = await api.getSubmissions(widget.assessmentId, studentId);
    // Load feedbacks
    final feedbacks = await api.getFeedbacks(widget.assessmentId);
    // Load class comments
    final comments = await api.getClassComments(widget.assessmentId);
    
    if (!mounted) return;
    setState(() {
      _submissions = submissions;
      _feedbacks = feedbacks;
      _classComments = comments;
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
        const SnackBar(content: Text('Please select a PDF file to submit')),
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
          content: Text('Assignment submitted successfully'),
          backgroundColor: AppTheme.accentGreen,
        ),
      );
    } catch (e) {
      if (!mounted) return;
      setState(() => _submitting = false);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Unable to submit assignment: $e')),
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
          content: Text('Submission cancelled'),
          backgroundColor: AppTheme.warning,
        ),
      );
    } catch (e) {
      if (!mounted) return;
      setState(() => _submitting = false);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Unable to cancel submission: $e')),
      );
    }
  }

  Future<void> _addClassComment() async {
    final comment = _commentController.text.trim();
    if (comment.isEmpty) return;
    
    try {
      final api = ref.read(apiServiceProvider);
      final studentId = ref.read(activeStudentIdProvider);
      
      final newComment = await api.addClassComment(
        assessmentId: widget.assessmentId,
        studentId: studentId,
        content: comment,
      );
      
      if (!mounted) return;
      setState(() {
        _classComments = [newComment, ..._classComments];
        _commentController.clear();
      });
      
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Comment added'),
          backgroundColor: AppTheme.accentGreen,
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: $e')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final studentAsync = ref.watch(studentProvider);

    return Scaffold(
      backgroundColor: AppTheme.backgroundDark,
      appBar: AppBar(
        title: const Text('Assignment Details'),
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
          child: Text('Error: $e', style: const TextStyle(color: AppTheme.danger)),
        ),
        data: (student) {
          final enrollment = student.enrollments
              .where((e) => e.codeModule == widget.courseCode)
              .firstOrNull;
          if (enrollment == null) {
            return const Center(
              child: Text(
                'Class not found',
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
                'Assignment not found',
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
                  'Submitted Files',
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
              if (_feedbacks.isNotEmpty) ...[
                const Text(
                  'Instructor Feedback',
                  style: TextStyle(
                    color: AppTheme.textPrimary,
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 8),
                ..._feedbacks.map((feedback) => _buildFeedbackCard(feedback)),
                const SizedBox(height: 16),
              ],
              const Text(
                'Class Discussion',
                style: TextStyle(
                  color: AppTheme.textPrimary,
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 8),
              _buildClassCommentInput(),
              const SizedBox(height: 8),
              if (_classComments.isNotEmpty)
                ..._classComments.map((comment) => _buildClassCommentCard(comment)),
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
            'Submission Info',
            style: TextStyle(
              color: AppTheme.textPrimary,
              fontSize: 14,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 10),
          Text(
            'Format: ${assessment.allowedFormats.isEmpty ? 'PDF' : assessment.allowedFormats.join(', ').toUpperCase()}',
            style: const TextStyle(color: AppTheme.textSecondary, fontSize: 13),
          ),
          const SizedBox(height: 6),
          Text(
            'Max file size: ${assessment.maxFileSizeMb} MB',
            style: const TextStyle(color: AppTheme.textSecondary, fontSize: 13),
          ),
          const SizedBox(height: 10),
          const Text(
            'Note: Please submit in the correct format and content as instructed. The file will be recorded in the system for instructor grading.',
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
          const SizedBox(height: 12),
          Wrap(
            runSpacing: 10,
            spacing: 10,
            children: [
              _buildInfoChip('Type', assessment.type),
              _buildInfoChip('Weight', '${assessment.weight.round()}%'),
              _buildInfoChip('Due Date', assessment.dueDateLabel),
              if (assessment.teacherId.isNotEmpty) _buildInfoChip('Instructor', assessment.teacherId),
            ],
          ),
          if (assessment.createdAt != null || assessment.updatedAt != null) ...[
            const SizedBox(height: 12),
            if (assessment.createdAt != null)
              _buildInfoLine('Created at', _formatTime(assessment.createdAt!)),
            if (assessment.updatedAt != null)
              _buildInfoLine('Updated at', _formatTime(assessment.updatedAt!)),
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
            'Assignment Description',
            style: TextStyle(
              color: AppTheme.textPrimary,
              fontSize: 14,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 10),
          Text(
            description.isNotEmpty ? description : 'No description available for this assignment.',
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
            'Submit Assignment',
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
                        : 'No file selected',
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
                label: const Text('Select File'),
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
                    'PDF file ready for submission',
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
              label: Text(_submitting ? 'Submitting...' : 'Submit File'),
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
                  'Submitted at: ${_formatTime(submission.submittedAt)}',
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
            tooltip: 'Preview',
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
                  'Instructor',
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
                        'Score: ${feedback.score}',
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

  Widget _buildClassCommentInput() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: AppTheme.surfaceCard,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppTheme.cardBorder),
      ),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: _commentController,
              style: const TextStyle(color: AppTheme.textPrimary),
              decoration: const InputDecoration(
                hintText: 'Write a comment...',
                hintStyle: TextStyle(color: AppTheme.textMuted),
                border: InputBorder.none,
                isDense: true,
              ),
            ),
          ),
          IconButton(
            icon: const Icon(Icons.send_rounded,
                color: AppTheme.primaryBlue),
            onPressed: _addClassComment,
          ),
        ],
      ),
    );
  }

  Widget _buildClassCommentCard(ClassComment comment) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppTheme.surfaceCard,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: comment.isInstructor
              ? AppTheme.primaryBlue.withValues(alpha: 0.25)
              : AppTheme.cardBorder,
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          CircleAvatar(
            radius: 14,
            backgroundColor: comment.isInstructor
                ? AppTheme.primaryBlue
                : AppTheme.textMuted,
            child: Icon(
              comment.isInstructor ? Icons.school : Icons.person,
              size: 14,
              color: Colors.white,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  comment.studentName,
                  style: const TextStyle(
                    color: AppTheme.textPrimary,
                    fontSize: 13,
                    fontWeight: FontWeight.w500,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  comment.content,
                  style: const TextStyle(
                    color: AppTheme.textSecondary,
                    fontSize: 13,
                  ),
                ),
                Text(
                  _formatTime(comment.createdAt),
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

  Future<void> _previewPDF(String url) async {
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
                    'File Preview',
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
                      'PDF Viewer will be displayed here',
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
                  '${assessment.type} · ${assessment.weight.round()}% weight',
                  style: const TextStyle(
                    color: AppTheme.textPrimary,
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  isSubmitted
                      ? 'Submitted · Due Day ${assessment.dueDate}'
                      : 'Due: Day ${assessment.dueDate}',
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
              label: Text(isUnsubmitting ? '' : 'Unsubmit'),
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
