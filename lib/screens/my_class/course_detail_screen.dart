import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:student_agent/core/theme/app_theme.dart';
import 'package:student_agent/models/assignment_milestone_model.dart';
import 'package:student_agent/models/student_model.dart';
import 'package:student_agent/providers/providers.dart';

class CourseDetailScreen extends ConsumerWidget {
  final String courseCode;

  const CourseDetailScreen({
    super.key,
    required this.courseCode,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final studentAsync = ref.watch(studentProvider);
    final channelsAsync = ref.watch(courseChannelsProvider(courseCode));

    return Scaffold(
      backgroundColor: AppTheme.backgroundDark,
      appBar: AppBar(
        title: Text(courseCode),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded, size: 18),
          onPressed: () => context.go('/my-class'),
        ),
      ),
      body: studentAsync.when(
        loading: () => const Center(
          child: CircularProgressIndicator(color: AppTheme.primaryBlue),
        ),
        error: (e, _) => Center(
          child: Text(
            'Lỗi tại lớp học: $e',
            style: const TextStyle(color: AppTheme.danger),
          ),
        ),
        data: (student) {
          final enrollment = student.enrollments
              .where((e) => e.codeModule == courseCode)
              .firstOrNull;

          if (enrollment == null) {
            return const Center(
              child: Text(
                'Không tìm thấy lớp học',
                style: TextStyle(color: AppTheme.textSecondary),
              ),
            );
          }

          return ListView(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 28),
            children: [
              _Header(enrollment: enrollment, student: student),
              const SizedBox(height: 16),
              _SectionTitle(title: 'Không gian lớp học'),
              const SizedBox(height: 10),
              channelsAsync.when(
                loading: () => const LinearProgressIndicator(minHeight: 2),
                error: (_, __) => _FeatureGrid(
                  enrollment: enrollment,
                  channels: const [],
                ),
                data: (channels) => _FeatureGrid(
                  enrollment: enrollment,
                  channels: channels,
                ),
              ),
              const SizedBox(height: 18),
              _SectionTitle(title: 'Bài tập gần đây'),
              const SizedBox(height: 10),
              ..._pendingAssessments(enrollment)
                  .take(3)
                  .map((a) => _AssessmentTile(
                        assessment: a,
                        courseCode: enrollment.codeModule,
                      )),
              if (_pendingAssessments(enrollment).isEmpty)
                const _EmptyPanel(text: 'Không có bài tập đang chờ nộp'),
              const SizedBox(height: 18),
              _SectionTitle(title: 'Điểm môn học'),
              const SizedBox(height: 10),
              _GradesPreview(enrollment: enrollment),
            ],
          );
        },
      ),
    );
  }

  List<Assessment> _pendingAssessments(Enrollment enrollment) {
    return enrollment.assessments.where((a) => !a.isSubmitted).toList()
      ..sort((a, b) => a.dueDate.compareTo(b.dueDate));
  }
}

class CourseAssignmentsScreen extends ConsumerWidget {
  final String courseCode;

  const CourseAssignmentsScreen({
    super.key,
    required this.courseCode,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return _CourseDataScaffold(
      courseCode: courseCode,
      title: 'Assignments',
      builder: (enrollment, _) => ListView(
        padding: const EdgeInsets.all(16),
        children: [
          ...enrollment.assessments.map(
            (a) => _AssignmentCard(
              assessment: a,
              courseCode: courseCode,
            ),
          ),
        ],
      ),
    );
  }
}

class CourseGradesScreen extends ConsumerWidget {
  final String courseCode;

  const CourseGradesScreen({
    super.key,
    required this.courseCode,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return _CourseDataScaffold(
      courseCode: courseCode,
      title: 'Điểm môn học',
      builder: (enrollment, _) => ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _GradesSummary(enrollment: enrollment),
          const SizedBox(height: 14),
          _GradesPreview(enrollment: enrollment),
        ],
      ),
    );
  }
}

class CourseProgressScreen extends ConsumerWidget {
  final String courseCode;

  const CourseProgressScreen({
    super.key,
    required this.courseCode,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return _CourseDataScaffold(
      courseCode: courseCode,
      title: 'Tiến độ học tập',
      builder: (enrollment, student) {
        final submitted =
            enrollment.assessments.where((a) => a.isSubmitted).length;
        final total = enrollment.assessments.length;
        final progress = total == 0 ? 0.0 : submitted / total;

        return ListView(
          padding: const EdgeInsets.all(16),
          children: [
            _Header(enrollment: enrollment, student: student),
            const SizedBox(height: 16),
            _ProgressTile(
              icon: Icons.assignment_turned_in_outlined,
              label: 'Tiến độ nộp bài',
              value: '${(progress * 100).round()}%',
              color: AppTheme.accentGreen,
            ),
            _ProgressTile(
              icon: Icons.touch_app_outlined,
              label: 'Tổng tương tác VLE',
              value: '${enrollment.vleSummary.totalClicks}',
              color: AppTheme.primaryBlue,
            ),
            _ProgressTile(
              icon: Icons.warning_amber_outlined,
              label: 'Điểm rủi ro tổng quan',
              value: '${(student.risk.score * 100).round()}%',
              color: student.risk.tier >= 3
                  ? AppTheme.danger
                  : student.risk.tier == 2
                      ? AppTheme.warning
                      : AppTheme.accentGreen,
            ),
          ],
        );
      },
    );
  }
}

class CourseExamsScreen extends ConsumerWidget {
  final String courseCode;

  const CourseExamsScreen({
    super.key,
    required this.courseCode,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return _CourseDataScaffold(
      courseCode: courseCode,
      title: 'Lich thi',
      builder: (enrollment, _) {
        final exams = enrollment.assessments
            .where((a) => a.type.toLowerCase().contains('exam'))
            .toList();
        final fallback = exams.isEmpty ? enrollment.assessments : exams;

        return ListView(
          padding: const EdgeInsets.all(16),
          children: [
            ...fallback.map(
              (a) => _AssessmentTile(
                assessment: a,
                courseCode: courseCode,
              ),
            ),
            if (fallback.isEmpty)
              const _EmptyPanel(text: 'Chưa có lịch thi cho môn này'),
          ],
        );
      },
    );
  }
}

class _CourseDataScaffold extends ConsumerWidget {
  final String courseCode;
  final String title;
  final Widget Function(Enrollment enrollment, StudentModel student) builder;

  const _CourseDataScaffold({
    required this.courseCode,
    required this.title,
    required this.builder,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final studentAsync = ref.watch(studentProvider);

    return Scaffold(
      backgroundColor: AppTheme.backgroundDark,
      appBar: AppBar(
        title: Text(title),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded, size: 18),
          onPressed: () => context.go('/my-class/$courseCode'),
        ),
      ),
      body: studentAsync.when(
        loading: () => const Center(
          child: CircularProgressIndicator(color: AppTheme.primaryBlue),
        ),
        error: (e, _) => Center(
          child: Text(
            'Loi tai du lieu: $e',
            style: const TextStyle(color: AppTheme.danger),
          ),
        ),
        data: (student) {
          final enrollment = student.enrollments
              .where((e) => e.codeModule == courseCode)
              .firstOrNull;
          if (enrollment == null) {
            return const Center(
              child: Text(
                'Không tim thấy lớp học',
                style: TextStyle(color: AppTheme.textSecondary),
              ),
            );
          }
          return builder(enrollment, student);
        },
      ),
    );
  }
}

class _Header extends StatelessWidget {
  final Enrollment enrollment;
  final StudentModel student;

  const _Header({
    required this.enrollment,
    required this.student,
  });

  @override
  Widget build(BuildContext context) {
    final submitted = enrollment.assessments.where((a) => a.isSubmitted).length;
    final total = enrollment.assessments.length;
    final progress = total == 0 ? 0.0 : submitted / total;
    final tierColor = switch (student.risk.tier) {
      1 => AppTheme.accentGreen,
      2 => AppTheme.warning,
      _ => AppTheme.danger,
    };

    return Container(
      decoration: BoxDecoration(
        color: AppTheme.surfaceCard,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppTheme.cardBorder, width: 1),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(18),
            decoration: const BoxDecoration(
              gradient: AppTheme.blueGreenGradientDiagonal,
              borderRadius: BorderRadius.vertical(top: Radius.circular(14)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  enrollment.codeModule,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 24,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  enrollment.displayName,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 15,
                    fontWeight: FontWeight.w500,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  '${enrollment.codePresentation} - ${enrollment.moduleLength} tuan',
                  style: TextStyle(
                    color: Colors.white.withValues(alpha: 0.82),
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(14),
            child: Column(
              children: [
                Row(
                  children: [
                    Expanded(
                      child: _Metric(
                        label: 'Đã nộp',
                        value: '$submitted/$total',
                        color: AppTheme.accentGreen,
                      ),
                    ),
                    Expanded(
                      child: _Metric(
                        label: 'Rủi ro',
                        value: '${(student.risk.score * 100).round()}%',
                        color: tierColor,
                      ),
                    ),
                    Expanded(
                      child: _Metric(
                        label: 'Hoạt động',
                        value: 'N${enrollment.vleSummary.lastActiveDay}',
                        color: AppTheme.primaryBlue,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                ClipRRect(
                  borderRadius: BorderRadius.circular(4),
                  child: LinearProgressIndicator(
                    value: progress,
                    minHeight: 7,
                    backgroundColor: AppTheme.surfaceDark,
                    valueColor: const AlwaysStoppedAnimation<Color>(
                      AppTheme.accentGreen,
                    ),
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

class _FeatureGrid extends StatelessWidget {
  final Enrollment enrollment;
  final List<dynamic> channels;

  const _FeatureGrid({
    required this.enrollment,
    required this.channels,
  });

  @override
  Widget build(BuildContext context) {
    String? channelId(String type) {
      for (final channel in channels) {
        if (channel.type == type) return channel.id;
      }
      return null;
    }

    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      mainAxisSpacing: 10,
      crossAxisSpacing: 10,
      childAspectRatio: 1.55,
      children: [
        _FeatureTile(
          icon: Icons.campaign_outlined,
          title: 'Thông báo',
          subtitle: 'Cập nhật từ lớp',
          color: AppTheme.warning,
          onTap: () => _openChannel(
            context,
            enrollment,
            channelId('announcement'),
            'Thông báo lớp',
            'announcement',
          ),
        ),
        _FeatureTile(
          icon: Icons.forum_outlined,
          title: 'Thảo luận',
          subtitle: 'Nhắn tin với lớp',
          color: AppTheme.primaryBlue,
          onTap: () => _openChannel(
            context,
            enrollment,
            channelId('discussion'),
            'Thảo luận',
            'discussion',
          ),
        ),
        _FeatureTile(
          icon: Icons.assignment_outlined,
          title: 'Assignments',
          subtitle: '${enrollment.assessments.length} bài đánh giá',
          color: AppTheme.accentGreen,
          onTap: () => context.go('/my-class/${enrollment.codeModule}/assignments'),
        ),
        _FeatureTile(
          icon: Icons.grade_outlined,
          title: 'Điểm',
          subtitle: 'Điểm thành phần',
          color: AppTheme.warning,
          onTap: () => context.go('/my-class/${enrollment.codeModule}/grades'),
        ),
        _FeatureTile(
          icon: Icons.trending_up_rounded,
          title: 'Tiến độ',
          subtitle: 'Hoạt động học tập',
          color: AppTheme.primaryBlue,
          onTap: () => context.go('/my-class/${enrollment.codeModule}/progress'),
        ),
        _FeatureTile(
          icon: Icons.event_note_outlined,
          title: 'Lịch thi',
          subtitle: 'Exam va deadline',
          color: AppTheme.danger,
          onTap: () => context.go('/my-class/${enrollment.codeModule}/exams'),
        ),
      ],
    );
  }

  void _openChannel(
    BuildContext context,
    Enrollment enrollment,
    String? channelId,
    String name,
    String type,
  ) {
    if (channelId == null) {
      context.go('/course/${enrollment.codeModule}/channels');
      return;
    }
    context.go(
      '/course/${enrollment.codeModule}/channels/$channelId/messages'
      '?name=${Uri.encodeComponent(name)}'
      '&type=${Uri.encodeComponent(type)}'
      '&returnTo=${Uri.encodeComponent('/my-class/${enrollment.codeModule}')}',
    );
  }
}

class _FeatureTile extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final Color color;
  final VoidCallback onTap;

  const _FeatureTile({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      borderRadius: BorderRadius.circular(12),
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: AppTheme.surfaceCard,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AppTheme.cardBorder, width: 1),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, color: color, size: 22),
            const SizedBox(height: 8),
            Text(
              title,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(
                color: AppTheme.textPrimary,
                fontSize: 13,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 2),
            Text(
              subtitle,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(
                color: AppTheme.textSecondary,
                fontSize: 11,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _AssessmentTile extends StatelessWidget {
  final Assessment assessment;
  final String courseCode;

  const _AssessmentTile({
    required this.assessment,
    required this.courseCode,
  });

  void _openDetail(BuildContext context) {
    context.go(
      '/my-class/$courseCode/assignments/${assessment.idAssessment}',
    );
  }

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: () => _openDetail(context),
      borderRadius: BorderRadius.circular(12),
      child: Container(
        margin: const EdgeInsets.only(bottom: 8),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: AppTheme.surfaceCard,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AppTheme.cardBorder, width: 1),
        ),
        child: Row(
          children: [
            const Icon(Icons.assignment_late_outlined, color: AppTheme.warning),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '${assessment.type} - ${assessment.weight.round()}%',
                    style: const TextStyle(
                      color: AppTheme.textPrimary,
                      fontSize: 13,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  Text(
                    'Hạn nộp: ngày ${assessment.dueDate}',
                    style: const TextStyle(
                      color: AppTheme.textSecondary,
                      fontSize: 12,
                    ),
                  ),
                ],
              ),
            ),
            const Icon(Icons.chevron_right_rounded, color: AppTheme.textMuted),
          ],
        ),
      ),
    );
  }
}

class _GradesPreview extends StatelessWidget {
  final Enrollment enrollment;

  const _GradesPreview({required this.enrollment});

  @override
  Widget build(BuildContext context) {
    final graded = enrollment.assessments.where((a) => a.score != null).toList();
    if (graded.isEmpty) {
      return const _EmptyPanel(text: 'Chưa có điểm thành phần');
    }

    return Column(
      children: graded
          .map(
            (a) => Container(
              margin: const EdgeInsets.only(bottom: 8),
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppTheme.surfaceCard,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppTheme.cardBorder, width: 1),
              ),
              child: Row(
                children: [
                  Expanded(
                    child: Text(
                      '${a.type} - ${a.weight.round()}%',
                      style: const TextStyle(
                        color: AppTheme.textPrimary,
                        fontSize: 13,
                      ),
                    ),
                  ),
                  Text(
                    '${a.score!.round()}/100',
                    style: const TextStyle(
                      color: AppTheme.accentGreen,
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
            ),
          )
          .toList(),
    );
  }
}

class _AssignmentCard extends ConsumerWidget {
  final Assessment assessment;
  final String courseCode;

  const _AssignmentCard({
    required this.assessment,
    required this.courseCode,
  });

  void _openDetail(BuildContext context) {
    context.go(
      '/my-class/$courseCode/assignments/${assessment.idAssessment}',
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final studentId = ref.read(activeStudentIdProvider);
    final milestonesAsync =
        ref.watch(assignmentMilestonesProvider(assessment.idAssessment));

    return InkWell(
      onTap: () => _openDetail(context),
      borderRadius: BorderRadius.circular(12),
      child: Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppTheme.surfaceCard,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: assessment.isSubmitted
              ? AppTheme.accentGreen.withValues(alpha: 0.3)
              : AppTheme.cardBorder,
          width: 1,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                assessment.isSubmitted
                    ? Icons.check_circle_outline_rounded
                    : Icons.assignment_outlined,
                color: assessment.isSubmitted
                    ? AppTheme.accentGreen
                    : AppTheme.warning,
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '${assessment.type} - ${assessment.weight.round()}%',
                      style: const TextStyle(
                        color: AppTheme.textPrimary,
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    Text(
                      assessment.isSubmitted
                          ? 'Đã nộp: ngày ${assessment.submittedDate}'
                          : 'Hạn nộp: ngày ${assessment.dueDate}',
                      style: const TextStyle(
                        color: AppTheme.textSecondary,
                        fontSize: 12,
                      ),
                    ),
                  ],
                ),
              ),
              if (assessment.score != null)
                Text(
                  '${assessment.score!.round()}/100',
                  style: const TextStyle(
                    color: AppTheme.accentGreen,
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                  ),
                ),
            ],
          ),
          if (!assessment.isSubmitted) ...[
            const SizedBox(height: 10),
            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                onPressed: () => _openDetail(context),
                icon: const Icon(Icons.upload_rounded, size: 16),
                label: const Text('Nộp bài'),
              ),
            ),
            const SizedBox(height: 6),
            milestonesAsync.when(
              loading: () => const LinearProgressIndicator(minHeight: 2),
              error: (_, __) => const SizedBox.shrink(),
              data: (data) {
                if (data.isEmpty) {
                  return OutlinedButton.icon(
                    icon: const Icon(Icons.auto_awesome_rounded, size: 16),
                    label: const Text('Lên kế hoạch chi tiết'),
                    onPressed: () async {
                      final api = ref.read(apiServiceProvider);
                      await api.triggerBreakdown(
                        assessment.idAssessment,
                        studentId,
                      );
                      ref.invalidate(
                        assignmentMilestonesProvider(assessment.idAssessment),
                      );
                    },
                  );
                }
                return Column(
                  children: data.milestones
                      .map(
                        (m) => Padding(
                          padding: const EdgeInsets.only(top: 6),
                          child: Row(
                            children: [
                              Icon(
                                m.status == MilestoneStatus.done
                                    ? Icons.check_circle_rounded
                                    : Icons.radio_button_unchecked_rounded,
                                size: 16,
                                color: m.status == MilestoneStatus.done
                                    ? AppTheme.accentGreen
                                    : AppTheme.textMuted,
                              ),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Text(
                                  m.title,
                                  style: const TextStyle(
                                    color: AppTheme.textSecondary,
                                    fontSize: 12,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      )
                      .toList(),
                );
              },
            ),
          ],
        ],
      ),
    ),
    );
  }
}

class _GradesSummary extends StatelessWidget {
  final Enrollment enrollment;

  const _GradesSummary({required this.enrollment});

  @override
  Widget build(BuildContext context) {
    final graded = enrollment.assessments.where((a) => a.score != null);
    var gradedWeight = 0.0;
    var achieved = 0.0;
    for (final a in graded) {
      gradedWeight += a.weight;
      achieved += (a.score! / 100) * a.weight;
    }
    final average = gradedWeight == 0 ? null : (achieved / gradedWeight) * 100;

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppTheme.surfaceCard,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppTheme.cardBorder, width: 1),
      ),
      child: Row(
        children: [
          Expanded(
            child: _Metric(
              label: 'Điểm hiện tại',
              value: average == null ? '--' : '${average.round()}%',
              color: average == null || average >= 40
                  ? AppTheme.accentGreen
                  : AppTheme.danger,
            ),
          ),
          Expanded(
            child: _Metric(
              label: 'Trong số đã chấm',
              value: '${gradedWeight.round()}%',
              color: AppTheme.primaryBlue,
            ),
          ),
        ],
      ),
    );
  }
}

class _ProgressTile extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final Color color;

  const _ProgressTile({
    required this.icon,
    required this.label,
    required this.value,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppTheme.surfaceCard,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppTheme.cardBorder, width: 1),
      ),
      child: Row(
        children: [
          Icon(icon, color: color),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              label,
              style: const TextStyle(
                color: AppTheme.textPrimary,
                fontSize: 13,
              ),
            ),
          ),
          Text(
            value,
            style: TextStyle(
              color: color,
              fontSize: 15,
              fontWeight: FontWeight.w700,
            ),
          ),
        ],
      ),
    );
  }
}

class _Metric extends StatelessWidget {
  final String label;
  final String value;
  final Color color;

  const _Metric({
    required this.label,
    required this.value,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          value,
          style: TextStyle(
            color: color,
            fontSize: 18,
            fontWeight: FontWeight.w700,
          ),
        ),
        Text(
          label,
          style: const TextStyle(
            color: AppTheme.textSecondary,
            fontSize: 11,
          ),
        ),
      ],
    );
  }
}

class _SectionTitle extends StatelessWidget {
  final String title;

  const _SectionTitle({required this.title});

  @override
  Widget build(BuildContext context) {
    return Text(
      title,
      style: const TextStyle(
        color: AppTheme.textPrimary,
        fontSize: 14,
        fontWeight: FontWeight.w600,
      ),
    );
  }
}

class _EmptyPanel extends StatelessWidget {
  final String text;

  const _EmptyPanel({required this.text});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppTheme.surfaceCard,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppTheme.cardBorder, width: 1),
      ),
      child: Text(
        text,
        style: const TextStyle(
          color: AppTheme.textSecondary,
          fontSize: 12,
        ),
      ),
    );
  }
}

extension _EnrollmentSearch on Iterable<Enrollment> {
  Enrollment? get firstOrNull => isEmpty ? null : first;
}
