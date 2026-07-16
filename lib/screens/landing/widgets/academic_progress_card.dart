import 'package:flutter/material.dart';
import 'package:student_agent/core/theme/app_theme.dart';
import 'package:student_agent/models/student_model.dart';

class AcademicProgressCard extends StatelessWidget {
  final WeeklySchedule? schedule;
  final bool _isLoading;

  const AcademicProgressCard({super.key, required this.schedule})
      : _isLoading = false;

  const AcademicProgressCard.loading({super.key})
      : schedule = null,
        _isLoading = true;

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Container(
        height: 90,
        decoration: BoxDecoration(
          color: AppTheme.surfaceCard,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: AppTheme.cardBorder, width: 1),
        ),
        child: const Center(
            child: CircularProgressIndicator(
                strokeWidth: 2, color: AppTheme.primaryBlue)),
      );
    }

    final s = schedule!;
    final progress = s.currentWeek / s.totalWeeks;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.surfaceCard,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppTheme.cardBorder, width: 1),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'Tiến độ học kỳ',
                style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w500,
                    color: AppTheme.textPrimary),
              ),
              // Streak badge
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: AppTheme.warningGlow,
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(
                      color: AppTheme.warning.withValues(alpha: 0.4),
                      width: 1),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.local_fire_department_rounded,
                        size: 14, color: AppTheme.warning),
                    const SizedBox(width: 4),
                    Text(
                      '${s.streakDays} ngày',
                      style: const TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w500,
                          color: AppTheme.warning),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          // Progress bar
          ClipRRect(
            borderRadius: BorderRadius.circular(6),
            child: LinearProgressIndicator(
              value: progress,
              minHeight: 8,
              backgroundColor: AppTheme.surfaceDark,
              valueColor:
                  const AlwaysStoppedAnimation<Color>(AppTheme.primaryBlue),
            ),
          ),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              RichText(
                text: TextSpan(
                  style: const TextStyle(
                      fontSize: 13, color: AppTheme.textSecondary),
                  children: [
                    const TextSpan(text: 'Tuần '),
                    TextSpan(
                      text: '${s.currentWeek}',
                      style: const TextStyle(
                          color: AppTheme.primaryBlue,
                          fontWeight: FontWeight.w600,
                          fontSize: 15),
                    ),
                    TextSpan(text: ' / ${s.totalWeeks}'),
                  ],
                ),
              ),
              Text(
                '${(progress * 100).round()}% hoàn thành',
                style: const TextStyle(
                    fontSize: 12, color: AppTheme.textSecondary),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
