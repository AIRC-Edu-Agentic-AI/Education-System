import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:student_agent/core/theme/app_theme.dart';
import 'package:student_agent/models/student_model.dart';
import 'package:student_agent/providers/providers.dart';

class AnalyticsScreen extends ConsumerWidget {
  const AnalyticsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final studentAsync = ref.watch(studentProvider);
    final riskHistoryAsync = ref.watch(riskHistoryProvider);

    return Scaffold(
      backgroundColor: AppTheme.backgroundDark,
      appBar: AppBar(title: const Text('Analytics & Insights')),
      body: studentAsync.when(
        loading: () => const Center(
            child: CircularProgressIndicator(color: AppTheme.primaryBlue)),
        error: (e, _) => Center(
            child:
                Text('Lỗi: $e', style: const TextStyle(color: AppTheme.danger))),
        data: (student) {
          final enrollment =
              student.enrollments.isNotEmpty ? student.enrollments.first : null;
          final vle = enrollment?.vleSummary;

          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              // ── Overview metric cards ──────────────────────────────────
              Row(
                children: [
                  _MetricCard(
                    label: 'Tổng lượt xem',
                    value: '${vle?.totalClicks ?? 0}',
                    icon: Icons.mouse_outlined,
                    color: AppTheme.primaryBlue,
                  ),
                  const SizedBox(width: 8),
                  _MetricCard(
                    label: 'Điểm rủi ro',
                    value: '${(student.risk.score * 100).round()}%',
                    icon: Icons.warning_amber_rounded,
                    color: student.risk.score > 0.7
                        ? AppTheme.danger
                        : student.risk.score > 0.4
                            ? AppTheme.warning
                            : AppTheme.accentGreen,
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  _MetricCard(
                    label: 'Tỉ lệ nộp bài',
                    value: enrollment != null && enrollment.assessments.isNotEmpty
                        ? '${((enrollment.assessments.where((a) => a.isSubmitted).length / enrollment.assessments.length) * 100).round()}%'
                        : '—',
                    icon: Icons.assignment_turned_in_outlined,
                    color: AppTheme.warning,
                  ),
                  const SizedBox(width: 8),
                  _MetricCard(
                    label: 'Ngày học gần nhất',
                    value: 'N${vle?.lastActiveDay ?? 0}',
                    icon: Icons.calendar_today_outlined,
                    color: AppTheme.accentGreen,
                  ),
                ],
              ),
              const SizedBox(height: 20),

              // ── Combined: Risk score vs VLE engagement ─────────────────
              riskHistoryAsync.when(
                loading: () => const SizedBox(
                    height: 220,
                    child: Center(
                        child: CircularProgressIndicator(
                            color: AppTheme.primaryBlue))),
                error: (_, __) => const SizedBox.shrink(),
                data: (history) => _RiskEngagementChart(
                  history: history,
                  weeklyClicks: vle?.weeklyClicks ?? const [],
                ),
              ),
              const SizedBox(height: 20),

              // ── Assessment grades per module ───────────────────────────
              const _SectionHeader('Điểm thành phần'),
              const SizedBox(height: 10),
              ...student.enrollments.map((e) => _ModuleGrades(enrollment: e)),
              const SizedBox(height: 8),

              // ── VLE activity by type (existing) ────────────────────────
              if (vle != null && vle.byActivityType.isNotEmpty) ...[
                const _SectionHeader('Hoạt động theo loại'),
                const SizedBox(height: 10),
                _ActivityByType(byType: vle.byActivityType),
              ],
            ],
          );
        },
      ),
    );
  }
}

// ── Combined Risk + Engagement chart ──────────────────────────────────────────

class _RiskEngagementChart extends StatelessWidget {
  final List<RiskPoint> history;
  final List<int> weeklyClicks;
  const _RiskEngagementChart(
      {required this.history, required this.weeklyClicks});

  @override
  Widget build(BuildContext context) {
    if (history.isEmpty) return const SizedBox.shrink();

    final weeks = history.map((h) => h.week).toList();
    final minWeek = weeks.first.toDouble();
    final maxWeek = weeks.last.toDouble();

    // Clicks for the weeks we have risk data, normalised to 0..1 for overlay.
    final clicksByWeek = <int, int>{};
    for (final h in history) {
      final idx = h.week - 1;
      clicksByWeek[h.week] =
          (idx >= 0 && idx < weeklyClicks.length) ? weeklyClicks[idx] : 0;
    }
    final maxClicks = clicksByWeek.values.isEmpty
        ? 1
        : clicksByWeek.values.reduce((a, b) => a > b ? a : b).clamp(1, 1 << 30);

    final riskSpots = [
      for (final h in history) FlSpot(h.week.toDouble(), h.score),
    ];
    final clickSpots = [
      for (final h in history)
        FlSpot(h.week.toDouble(), clicksByWeek[h.week]! / maxClicks),
    ];

    return Container(
      padding: const EdgeInsets.fromLTRB(8, 16, 16, 8),
      decoration: BoxDecoration(
        color: AppTheme.surfaceCard,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppTheme.cardBorder, width: 1),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Padding(
            padding: EdgeInsets.only(left: 8),
            child: Text('Rủi ro & Tương tác (theo tuần)',
                style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w500,
                    color: AppTheme.textPrimary)),
          ),
          const SizedBox(height: 4),
          const Padding(
            padding: EdgeInsets.only(left: 8),
            child: Text('Tương tác giảm → rủi ro tăng',
                style: TextStyle(fontSize: 11, color: AppTheme.textMuted)),
          ),
          const SizedBox(height: 16),
          SizedBox(
            height: 200,
            child: LineChart(
              LineChartData(
                minX: minWeek,
                maxX: maxWeek,
                minY: 0,
                maxY: 1,
                rangeAnnotations: RangeAnnotations(
                  horizontalRangeAnnotations: [
                    HorizontalRangeAnnotation(
                        y1: 0,
                        y2: 0.4,
                        color: AppTheme.accentGreen.withValues(alpha: 0.06)),
                    HorizontalRangeAnnotation(
                        y1: 0.4,
                        y2: 0.7,
                        color: AppTheme.warning.withValues(alpha: 0.06)),
                    HorizontalRangeAnnotation(
                        y1: 0.7,
                        y2: 1.0,
                        color: AppTheme.danger.withValues(alpha: 0.08)),
                  ],
                ),
                gridData: FlGridData(
                  show: true,
                  drawVerticalLine: false,
                  horizontalInterval: 0.25,
                  getDrawingHorizontalLine: (_) =>
                      const FlLine(color: AppTheme.divider, strokeWidth: 0.5),
                ),
                titlesData: FlTitlesData(
                  topTitles: const AxisTitles(
                      sideTitles: SideTitles(showTitles: false)),
                  leftTitles: AxisTitles(
                    sideTitles: SideTitles(
                      showTitles: true,
                      reservedSize: 30,
                      interval: 0.25,
                      getTitlesWidget: (value, _) => Text(
                        value.toStringAsFixed(1),
                        style: const TextStyle(
                            fontSize: 9, color: AppTheme.textMuted),
                      ),
                    ),
                  ),
                  rightTitles: AxisTitles(
                    sideTitles: SideTitles(
                      showTitles: true,
                      reservedSize: 34,
                      interval: 0.25,
                      getTitlesWidget: (value, _) => Text(
                        '${(value * maxClicks).round()}',
                        style: const TextStyle(
                            fontSize: 9, color: AppTheme.textMuted),
                      ),
                    ),
                  ),
                  bottomTitles: AxisTitles(
                    sideTitles: SideTitles(
                      showTitles: true,
                      interval: 1,
                      getTitlesWidget: (value, _) => Padding(
                        padding: const EdgeInsets.only(top: 6),
                        child: Text('T${value.toInt()}',
                            style: const TextStyle(
                                fontSize: 10, color: AppTheme.textMuted)),
                      ),
                    ),
                  ),
                ),
                borderData: FlBorderData(show: false),
                lineTouchData: const LineTouchData(enabled: false),
                lineBarsData: [
                  // VLE engagement (normalised) — area
                  LineChartBarData(
                    spots: clickSpots,
                    isCurved: true,
                    barWidth: 2,
                    color: AppTheme.primaryBlue,
                    dotData: const FlDotData(show: false),
                    belowBarData: BarAreaData(
                      show: true,
                      color: AppTheme.primaryBlue.withValues(alpha: 0.12),
                    ),
                  ),
                  // Risk score — line
                  LineChartBarData(
                    spots: riskSpots,
                    isCurved: true,
                    barWidth: 3,
                    color: AppTheme.danger,
                    dotData: FlDotData(
                      show: true,
                      getDotPainter: (spot, _, __, ___) =>
                          FlDotCirclePainter(
                        radius: 3,
                        color: AppTheme.danger,
                        strokeWidth: 0,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 12),
          const Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              _LegendDot(color: AppTheme.danger, label: 'Điểm rủi ro (trái)'),
              SizedBox(width: 16),
              _LegendDot(
                  color: AppTheme.primaryBlue, label: 'Lượt xem VLE (phải)'),
            ],
          ),
        ],
      ),
    );
  }
}

class _LegendDot extends StatelessWidget {
  final Color color;
  final String label;
  const _LegendDot({required this.color, required this.label});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 10,
          height: 10,
          decoration: BoxDecoration(color: color, shape: BoxShape.circle),
        ),
        const SizedBox(width: 6),
        Text(label,
            style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
      ],
    );
  }
}

// ── Assessment grades per module ──────────────────────────────────────────────

class _ModuleGrades extends StatelessWidget {
  final Enrollment enrollment;
  const _ModuleGrades({required this.enrollment});

  static const _passMark = 40.0;

  @override
  Widget build(BuildContext context) {
    final graded =
        enrollment.assessments.where((a) => a.score != null).toList();

    // Weighted progress among graded assessments.
    double gradedWeight = 0, achievedWeighted = 0;
    for (final a in graded) {
      gradedWeight += a.weight;
      achievedWeighted += (a.score! / 100.0) * a.weight;
    }
    final currentAvg =
        gradedWeight > 0 ? (achievedWeighted / gradedWeight) * 100 : 0.0;

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppTheme.surfaceCard,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppTheme.cardBorder, width: 1),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(enrollment.displayName,
              style: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  color: AppTheme.textPrimary)),
          const SizedBox(height: 14),
          SizedBox(
            height: 160,
            child: BarChart(
              BarChartData(
                maxY: 100,
                alignment: BarChartAlignment.spaceAround,
                gridData: FlGridData(
                  show: true,
                  drawVerticalLine: false,
                  horizontalInterval: 25,
                  getDrawingHorizontalLine: (v) => FlLine(
                    color: v == _passMark
                        ? AppTheme.warning.withValues(alpha: 0.5)
                        : AppTheme.divider,
                    strokeWidth: v == _passMark ? 1.5 : 0.5,
                    dashArray: v == _passMark ? [4, 3] : null,
                  ),
                ),
                titlesData: FlTitlesData(
                  topTitles: const AxisTitles(
                      sideTitles: SideTitles(showTitles: false)),
                  rightTitles: const AxisTitles(
                      sideTitles: SideTitles(showTitles: false)),
                  leftTitles: AxisTitles(
                    sideTitles: SideTitles(
                      showTitles: true,
                      reservedSize: 28,
                      interval: 25,
                      getTitlesWidget: (v, _) => Text('${v.toInt()}',
                          style: const TextStyle(
                              fontSize: 9, color: AppTheme.textMuted)),
                    ),
                  ),
                  bottomTitles: AxisTitles(
                    sideTitles: SideTitles(
                      showTitles: true,
                      reservedSize: 32,
                      getTitlesWidget: (value, _) {
                        final i = value.toInt();
                        if (i < 0 || i >= enrollment.assessments.length) {
                          return const SizedBox.shrink();
                        }
                        final a = enrollment.assessments[i];
                        return Padding(
                          padding: const EdgeInsets.only(top: 6),
                          child: Column(
                            children: [
                              Text(a.type,
                                  style: const TextStyle(
                                      fontSize: 9,
                                      color: AppTheme.textSecondary)),
                              Text('${a.weight.toInt()}%',
                                  style: const TextStyle(
                                      fontSize: 8, color: AppTheme.textMuted)),
                            ],
                          ),
                        );
                      },
                    ),
                  ),
                ),
                borderData: FlBorderData(show: false),
                barGroups: [
                  for (int i = 0; i < enrollment.assessments.length; i++)
                    _barGroup(i, enrollment.assessments[i]),
                ],
              ),
            ),
          ),
          const SizedBox(height: 12),
          // Weighted summary
          Row(
            children: [
              Expanded(
                child: _SummaryStat(
                  label: 'Điểm TB hiện tại',
                  value: gradedWeight > 0
                      ? '${currentAvg.round()}%'
                      : '—',
                  color: currentAvg >= _passMark
                      ? AppTheme.accentGreen
                      : AppTheme.danger,
                ),
              ),
              Expanded(
                child: _SummaryStat(
                  label: 'Đã chấm',
                  value: '${gradedWeight.toInt()}% trọng số',
                  color: AppTheme.textSecondary,
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          const Text('Đường nét đứt = vạch qua môn (40%)',
              style: TextStyle(fontSize: 10, color: AppTheme.textMuted)),
        ],
      ),
    );
  }

  BarChartGroupData _barGroup(int x, Assessment a) {
    final score = a.score ?? 0;
    final submitted = a.isSubmitted;
    final Color color = !submitted
        ? AppTheme.textMuted.withValues(alpha: 0.3)
        : score >= _passMark
            ? AppTheme.accentGreen
            : AppTheme.danger;
    return BarChartGroupData(
      x: x,
      barRods: [
        BarChartRodData(
          toY: submitted ? score.toDouble() : 4, // stub bar if unsubmitted
          color: color,
          width: 22,
          borderRadius: const BorderRadius.vertical(top: Radius.circular(4)),
        ),
      ],
    );
  }
}

class _SummaryStat extends StatelessWidget {
  final String label;
  final String value;
  final Color color;
  const _SummaryStat(
      {required this.label, required this.value, required this.color});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(value,
            style: TextStyle(
                fontSize: 18, fontWeight: FontWeight.w600, color: color)),
        Text(label,
            style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
      ],
    );
  }
}

// ── VLE activity by type ──────────────────────────────────────────────────────

class _ActivityByType extends StatelessWidget {
  final Map<String, int> byType;
  const _ActivityByType({required this.byType});

  @override
  Widget build(BuildContext context) {
    final maxVal = byType.values.reduce((a, b) => a > b ? a : b);
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppTheme.surfaceCard,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppTheme.cardBorder, width: 1),
      ),
      child: Column(
        children: byType.entries.map((entry) {
          final fraction = entry.value / maxVal;
          return Padding(
            padding: const EdgeInsets.only(bottom: 10),
            child: Row(
              children: [
                SizedBox(
                  width: 70,
                  child: Text(entry.key,
                      style: const TextStyle(
                          fontSize: 12, color: AppTheme.textSecondary)),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(4),
                    child: LinearProgressIndicator(
                      value: fraction,
                      minHeight: 8,
                      backgroundColor: AppTheme.surfaceDark,
                      valueColor: const AlwaysStoppedAnimation<Color>(
                          AppTheme.primaryBlue),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                Text('${entry.value}',
                    style: const TextStyle(
                        fontSize: 11, color: AppTheme.textSecondary)),
              ],
            ),
          );
        }).toList(),
      ),
    );
  }
}

// ── Shared ────────────────────────────────────────────────────────────────────

class _SectionHeader extends StatelessWidget {
  final String title;
  const _SectionHeader(this.title);

  @override
  Widget build(BuildContext context) {
    return Text(title,
        style: const TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w500,
            color: AppTheme.textPrimary));
  }
}

class _MetricCard extends StatelessWidget {
  final String label;
  final String value;
  final IconData icon;
  final Color color;

  const _MetricCard({
    required this.label,
    required this.value,
    required this.icon,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.08),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: color.withValues(alpha: 0.25), width: 1),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, size: 18, color: color),
            const SizedBox(height: 8),
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
