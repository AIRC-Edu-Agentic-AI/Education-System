import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:student_agent/core/theme/app_theme.dart';
import 'package:student_agent/providers/providers.dart';

class MyClassScreen extends ConsumerWidget {
  const MyClassScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final studentAsync = ref.watch(studentProvider);

    return Scaffold(
      backgroundColor: AppTheme.backgroundDark,
      appBar: AppBar(title: const Text('MyClass')),
      body: studentAsync.when(
        loading: () => const Center(
            child: CircularProgressIndicator(color: AppTheme.primaryBlue)),
        error: (e, _) =>
            Center(child: Text('Lỗi: $e', style: const TextStyle(color: AppTheme.danger))),
        data: (student) {
          final enrollment = student.enrollments.isNotEmpty
              ? student.enrollments.first
              : null;
          if (enrollment == null) {
            return const Center(
                child: Text('Không có lớp học',
                    style: TextStyle(color: AppTheme.textSecondary)));
          }
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              // Class info card
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: AppTheme.surfaceCard,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: AppTheme.cardBorder, width: 1),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Container(
                          width: 48,
                          height: 48,
                          decoration: BoxDecoration(
                            gradient: AppTheme.blueGreenGradient,
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Center(
                            child: Text(enrollment.codeModule,
                                style: const TextStyle(
                                    color: Colors.white,
                                    fontWeight: FontWeight.w600,
                                    fontSize: 12)),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(enrollment.displayName,
                                style: const TextStyle(
                                    fontSize: 15,
                                    fontWeight: FontWeight.w600,
                                    color: AppTheme.textPrimary)),
                            Text('${enrollment.moduleLength} tuần',
                                style: const TextStyle(
                                    fontSize: 12,
                                    color: AppTheme.textSecondary)),
                          ],
                        ),
                      ],
                    ),
                    const SizedBox(height: 14),
                    const Divider(),
                    const SizedBox(height: 10),
                    Text(
                      'Tương tác VLE: ${enrollment.vleSummary.totalClicks} lượt',
                      style: const TextStyle(
                          fontSize: 13, color: AppTheme.textSecondary),
                    ),
                    Text(
                      'Hoạt động gần nhất: Ngày ${enrollment.vleSummary.lastActiveDay}',
                      style: const TextStyle(
                          fontSize: 13, color: AppTheme.textSecondary),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),
              FilledButton.icon(
                icon: const Icon(Icons.forum_outlined, size: 18),
                label: const Text('Mở kênh lớp'),
                onPressed: () {
                  context.go(
                    '/course/${enrollment.codeModule}/channels',
                    extra: {'courseTitle': enrollment.displayName},
                  );
                },
              ),
              const SizedBox(height: 16),
              const Text('Bài kiểm tra & bài nộp',
                  style: TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w500,
                      color: AppTheme.textSecondary)),
              const SizedBox(height: 10),
              ...enrollment.assessments.map((a) => Container(
                    margin: const EdgeInsets.only(bottom: 8),
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: AppTheme.surfaceCard,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(
                          color: a.isSubmitted
                              ? AppTheme.accentGreen.withValues(alpha: 0.3)
                              : AppTheme.cardBorder,
                          width: 1),
                    ),
                    child: Row(
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text('${a.type} — ${a.weight.round()}%',
                                  style: const TextStyle(
                                      fontSize: 13,
                                      fontWeight: FontWeight.w500,
                                      color: AppTheme.textPrimary)),
                              Text('Hạn nộp: Ngày ${a.dueDate}',
                                  style: const TextStyle(
                                      fontSize: 12,
                                      color: AppTheme.textSecondary)),
                            ],
                          ),
                        ),
                        if (a.score != null)
                          Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 10, vertical: 4),
                            decoration: BoxDecoration(
                              color: AppTheme.accentGreenGlow,
                              borderRadius: BorderRadius.circular(20),
                              border: Border.all(
                                  color: AppTheme.accentGreen.withValues(alpha: 0.3),
                                  width: 1),
                            ),
                            child: Text('${a.score!.round()}/100',
                                style: const TextStyle(
                                    fontSize: 12,
                                    fontWeight: FontWeight.w500,
                                    color: AppTheme.accentGreen)),
                          )
                        else
                          Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 10, vertical: 4),
                            decoration: BoxDecoration(
                              color: AppTheme.surfaceDark,
                              borderRadius: BorderRadius.circular(20),
                            ),
                            child: const Text('Chưa nộp',
                                style: TextStyle(
                                    fontSize: 12,
                                    color: AppTheme.textMuted)),
                          ),
                      ],
                    ),
                  )),
            ],
          );
        },
      ),
    );
  }
}
