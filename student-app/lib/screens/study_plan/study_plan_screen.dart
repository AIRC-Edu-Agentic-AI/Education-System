import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:student_agent/core/theme/app_theme.dart';
import 'package:student_agent/providers/providers.dart';

class StudyPlanScreen extends ConsumerWidget {
  const StudyPlanScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final planAsync = ref.watch(studyPlanProvider);

    return Scaffold(
      backgroundColor: AppTheme.backgroundDark,
      appBar: AppBar(title: const Text('Study Plan & Roadmaps')),
      body: planAsync.when(
        loading: () => const Center(
            child: CircularProgressIndicator(color: AppTheme.primaryBlue)),
        error: (e, _) =>
            Center(child: Text('Lỗi: $e', style: const TextStyle(color: AppTheme.danger))),
        data: (sessions) => ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // SM-2 banner
            Container(
              padding: const EdgeInsets.all(14),
              margin: const EdgeInsets.only(bottom: 16),
              decoration: BoxDecoration(
                color: AppTheme.accentGreenGlow,
                borderRadius: BorderRadius.circular(14),
                border: Border.all(
                    color: AppTheme.accentGreen.withValues(alpha: 0.35), width: 1),
              ),
              child: const Row(
                children: [
                  Icon(Icons.psychology_outlined,
                      color: AppTheme.accentGreen, size: 20),
                  SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Lịch SM-2 đang hoạt động',
                            style: TextStyle(
                                fontSize: 13,
                                fontWeight: FontWeight.w500,
                                color: AppTheme.accentGreen)),
                        Text('4 thẻ flashcard cần ôn hôm nay',
                            style: TextStyle(
                                fontSize: 12, color: AppTheme.textSecondary)),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const Text('Kế hoạch tuần này',
                style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w500,
                    color: AppTheme.textPrimary)),
            const SizedBox(height: 12),
            ...sessions.asMap().entries.map((entry) {
              final s = entry.value;
              final typeColor = switch (s['type']) {
                'review' => AppTheme.primaryBlue,
                'spaced_rep' => AppTheme.accentGreen,
                'assignment' => AppTheme.danger,
                'practice' => AppTheme.warning,
                _ => AppTheme.textSecondary,
              };
              final typeIcon = switch (s['type']) {
                'review' => Icons.replay_rounded,
                'spaced_rep' => Icons.psychology_rounded,
                'assignment' => Icons.assignment_outlined,
                'practice' => Icons.edit_note_rounded,
                _ => Icons.book_outlined,
              };
              return Container(
                margin: const EdgeInsets.only(bottom: 10),
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: AppTheme.surfaceCard,
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: AppTheme.cardBorder, width: 1),
                ),
                child: Row(
                  children: [
                    Container(
                      width: 38,
                      height: 38,
                      decoration: BoxDecoration(
                        color: typeColor.withValues(alpha: 0.12),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Icon(typeIcon, size: 18, color: typeColor),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(s['subject'],
                              style: const TextStyle(
                                  fontSize: 13,
                                  fontWeight: FontWeight.w500,
                                  color: AppTheme.textPrimary)),
                          Text(
                              '${s['day']} · ${s['time']} · ${s['duration']} phút',
                              style: const TextStyle(
                                  fontSize: 12,
                                  color: AppTheme.textSecondary)),
                        ],
                      ),
                    ),
                    if (s['sm2_interval'] != null)
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 8, vertical: 3),
                        decoration: BoxDecoration(
                          color: AppTheme.accentGreenGlow,
                          borderRadius: BorderRadius.circular(20),
                          border: Border.all(
                              color: AppTheme.accentGreen.withValues(alpha: 0.3),
                              width: 1),
                        ),
                        child: Text('↩ ${s['sm2_interval']}d',
                            style: const TextStyle(
                                fontSize: 10, color: AppTheme.accentGreen)),
                      ),
                  ],
                ),
              );
            }),
          ],
        ),
      ),
    );
  }
}
