import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:student_agent/core/theme/app_theme.dart';
import 'package:student_agent/models/assignment_milestone_model.dart';
import 'package:student_agent/models/student_model.dart';
import 'package:student_agent/providers/providers.dart';

class MyEnrollmentScreen extends ConsumerWidget {
  const MyEnrollmentScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final studentAsync = ref.watch(studentProvider);

    return Scaffold(
      backgroundColor: AppTheme.backgroundDark,
      appBar: AppBar(title: const Text('MyEnrollment')),
      body: studentAsync.when(
        loading: () => const Center(
            child: CircularProgressIndicator(color: AppTheme.primaryBlue)),
        error: (e, _) =>
            Center(child: Text('Lỗi: $e', style: const TextStyle(color: AppTheme.danger))),
        data: (student) => ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Row(
              children: [
                _StatChip(
                    label: 'Môn đang học',
                    value: '${student.enrollments.length}',
                    color: AppTheme.primaryBlue),
                const SizedBox(width: 8),
                _StatChip(
                    label: 'Tín chỉ',
                    value: '${student.demographics.studiedCredits}',
                    color: AppTheme.accentGreen),
              ],
            ),
            const SizedBox(height: 16),
            ...student.enrollments.map((e) => _EnrollmentCard(enrollment: e)),
          ],
        ),
      ),
    );
  }
}

// ── Enrollment card with expandable assessments ───────────────────────────────

class _EnrollmentCard extends ConsumerStatefulWidget {
  final Enrollment enrollment;
  const _EnrollmentCard({required this.enrollment});

  @override
  ConsumerState<_EnrollmentCard> createState() => _EnrollmentCardState();
}

class _EnrollmentCardState extends ConsumerState<_EnrollmentCard> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    final e = widget.enrollment;
    final submitted = e.assessments.where((a) => a.isSubmitted).length;
    final total = e.assessments.length;
    final progress = total > 0 ? submitted / total : 0.0;

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: AppTheme.surfaceCard,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppTheme.cardBorder, width: 1),
      ),
      child: Column(
        children: [
          // ── Header ────────────────────────────────────────────────────────
          InkWell(
            borderRadius: BorderRadius.circular(14),
            onTap: () => setState(() => _expanded = !_expanded),
            child: Padding(
              padding: const EdgeInsets.all(14),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(e.displayName,
                          style: const TextStyle(
                              fontSize: 14,
                              fontWeight: FontWeight.w500,
                              color: AppTheme.textPrimary)),
                      Row(
                        children: [
                          if (e.finalResult != null)
                            Container(
                              margin: const EdgeInsets.only(right: 6),
                              padding: const EdgeInsets.symmetric(
                                  horizontal: 8, vertical: 3),
                              decoration: BoxDecoration(
                                color: AppTheme.accentGreenGlow,
                                borderRadius: BorderRadius.circular(20),
                                border: Border.all(
                                    color: AppTheme.accentGreen
                                        .withValues(alpha: 0.3),
                                    width: 1),
                              ),
                              child: Text(e.finalResult!,
                                  style: const TextStyle(
                                      fontSize: 11,
                                      color: AppTheme.accentGreen)),
                            ),
                          Icon(
                            _expanded
                                ? Icons.keyboard_arrow_up_rounded
                                : Icons.keyboard_arrow_down_rounded,
                            color: AppTheme.textMuted,
                            size: 20,
                          ),
                        ],
                      ),
                    ],
                  ),
                  const SizedBox(height: 10),
                  ClipRRect(
                    borderRadius: BorderRadius.circular(4),
                    child: LinearProgressIndicator(
                      value: progress,
                      minHeight: 6,
                      backgroundColor: AppTheme.surfaceDark,
                      valueColor: const AlwaysStoppedAnimation<Color>(
                          AppTheme.accentGreen),
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    '$submitted/$total bài đã nộp · ${e.moduleLength} tuần',
                    style: const TextStyle(
                        fontSize: 12, color: AppTheme.textSecondary),
                  ),
                ],
              ),
            ),
          ),

          // ── Expanded: assessments with milestones ─────────────────────────
          if (_expanded) ...[
            const Divider(height: 0, color: AppTheme.cardBorder),
            ...e.assessments.map((a) => _AssessmentRow(
                  assessment: a,
                  module: e.codeModule,
                )),
          ],
        ],
      ),
    );
  }
}

// ── Single assessment row with milestone card ─────────────────────────────────

class _AssessmentRow extends ConsumerWidget {
  final Assessment assessment;
  final String module;
  const _AssessmentRow({required this.assessment, required this.module});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final msAsync =
        ref.watch(assignmentMilestonesProvider(assessment.idAssessment));
    final studentId = ref.read(activeStudentIdProvider);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(14, 10, 14, 6),
          child: Row(
            children: [
              _statusDot(assessment),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  '${assessment.type} · ${assessment.weight.toInt()}%',
                  style: const TextStyle(
                      fontSize: 13, color: AppTheme.textPrimary),
                ),
              ),
              Text(
                assessment.isSubmitted
                    ? 'Đã nộp'
                    : 'Ngày ${assessment.dueDate}',
                style: TextStyle(
                  fontSize: 12,
                  color: assessment.isSubmitted
                      ? AppTheme.accentGreen
                      : AppTheme.textSecondary,
                ),
              ),
            ],
          ),
        ),

        // Milestone section
        msAsync.when(
          loading: () => const Padding(
            padding: EdgeInsets.symmetric(horizontal: 14, vertical: 4),
            child: LinearProgressIndicator(minHeight: 2),
          ),
          error: (_, __) => const SizedBox.shrink(),
          data: (ms) {
            if (ms.isEmpty && !assessment.isSubmitted) {
              return Padding(
                padding: const EdgeInsets.fromLTRB(14, 0, 14, 10),
                child: GestureDetector(
                  onTap: () async {
                    final api = ref.read(apiServiceProvider);
                    await api.triggerBreakdown(
                        assessment.idAssessment, studentId);
                    ref.invalidate(assignmentMilestonesProvider(
                        assessment.idAssessment));
                  },
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 12, vertical: 6),
                    decoration: BoxDecoration(
                      color: AppTheme.primaryBlue.withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(
                          color: AppTheme.primaryBlue.withValues(alpha: 0.3),
                          width: 1),
                    ),
                    child: const Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.auto_awesome_rounded,
                            size: 14, color: AppTheme.primaryBlue),
                        SizedBox(width: 6),
                        Text('Lên kế hoạch chi tiết',
                            style: TextStyle(
                                fontSize: 12, color: AppTheme.primaryBlue)),
                      ],
                    ),
                  ),
                ),
              );
            }
            if (ms.isEmpty) return const SizedBox.shrink();
            return _MilestoneCard(
              data: ms,
              studentId: studentId,
            );
          },
        ),

        const Divider(height: 0, indent: 14, endIndent: 14),
      ],
    );
  }

  Widget _statusDot(Assessment a) {
    final color = a.isSubmitted
        ? AppTheme.accentGreen
        : AppTheme.textMuted;
    return Container(
      width: 8,
      height: 8,
      decoration: BoxDecoration(color: color, shape: BoxShape.circle),
    );
  }
}

// ── Milestone card ────────────────────────────────────────────────────────────

class _MilestoneCard extends ConsumerStatefulWidget {
  final AssignmentMilestonesData data;
  final int studentId;
  const _MilestoneCard({required this.data, required this.studentId});

  @override
  ConsumerState<_MilestoneCard> createState() => _MilestoneCardState();
}

class _MilestoneCardState extends ConsumerState<_MilestoneCard> {
  late List<MilestoneModel> _milestones;

  @override
  void initState() {
    super.initState();
    _milestones = List.from(widget.data.milestones);
  }

  Color _statusColor(MilestoneStatus s) => switch (s) {
        MilestoneStatus.done => AppTheme.accentGreen,
        MilestoneStatus.inProgress => AppTheme.primaryBlue,
        MilestoneStatus.skipped => AppTheme.textMuted,
        MilestoneStatus.pending => AppTheme.textMuted,
      };

  IconData _statusIcon(MilestoneStatus s) => switch (s) {
        MilestoneStatus.done => Icons.check_circle_rounded,
        MilestoneStatus.inProgress => Icons.radio_button_checked_rounded,
        MilestoneStatus.skipped => Icons.remove_circle_outline_rounded,
        MilestoneStatus.pending => Icons.radio_button_unchecked_rounded,
      };

  Future<void> _cycleStatus(MilestoneModel ms) async {
    final next = ms.status.next;
    setState(() {
      _milestones = _milestones
          .map((m) => m.id == ms.id ? m.copyWith(status: next) : m)
          .toList();
    });
    final api = ref.read(apiServiceProvider);
    await api.updateMilestoneStatus(
      studentId: widget.studentId,
      idAssessment: widget.data.idAssessment,
      milestoneId: ms.id,
      status: next.apiValue,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(14, 0, 14, 10),
      child: Column(
        children: _milestones.map((ms) {
          final color = _statusColor(ms.status);
          return Padding(
            padding: const EdgeInsets.symmetric(vertical: 4),
            child: Row(
              children: [
                GestureDetector(
                  onTap: () => _cycleStatus(ms),
                  child: Icon(_statusIcon(ms.status), size: 18, color: color),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    ms.title,
                    style: TextStyle(
                      fontSize: 12,
                      color: ms.status == MilestoneStatus.done ||
                              ms.status == MilestoneStatus.skipped
                          ? AppTheme.textMuted
                          : AppTheme.textPrimary,
                      decoration: ms.status == MilestoneStatus.skipped
                          ? TextDecoration.lineThrough
                          : null,
                    ),
                  ),
                ),
                GestureDetector(
                  onTap: () => _cycleStatus(ms),
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: color.withValues(alpha: 0.12),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(
                          color: color.withValues(alpha: 0.3), width: 1),
                    ),
                    child: Text(ms.status.label,
                        style: TextStyle(fontSize: 10, color: color)),
                  ),
                ),
              ],
            ),
          );
        }).toList(),
      ),
    );
  }
}

// ── Stat chip ─────────────────────────────────────────────────────────────────

class _StatChip extends StatelessWidget {
  final String label;
  final String value;
  final Color color;
  const _StatChip(
      {required this.label, required this.value, required this.color});

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.08),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: color.withValues(alpha: 0.25), width: 1),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(value,
                style: TextStyle(
                    fontSize: 22, fontWeight: FontWeight.w600, color: color)),
            Text(label,
                style: const TextStyle(
                    fontSize: 11, color: AppTheme.textSecondary)),
          ],
        ),
      ),
    );
  }
}
