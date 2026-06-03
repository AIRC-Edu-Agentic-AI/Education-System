import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:student_agent/core/theme/app_theme.dart';
import 'package:student_agent/models/student_model.dart';
import 'package:student_agent/providers/providers.dart';

// Default block lengths (minutes) when the source has no explicit duration.
const _kLectureMin = 120;
const _kClassMin = 90;

const _days = ['Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7', 'CN'];

enum BlockKind { lecture, classes, study, exam }

class _Block {
  final String day;
  final int startMin;
  final int endMin;
  final String title;
  final String sub; // room / duration / study type
  final BlockKind kind;

  const _Block({
    required this.day,
    required this.startMin,
    required this.endMin,
    required this.title,
    required this.sub,
    required this.kind,
  });

  String get timeLabel => '${_fmt(startMin)}–${_fmt(endMin)}';
}

String _fmt(int min) {
  final h = (min ~/ 60).toString().padLeft(2, '0');
  final m = (min % 60).toString().padLeft(2, '0');
  return '$h:$m';
}

String? _matchDay(String s) => RegExp(r'(Thứ [2-7]|CN)').firstMatch(s)?.group(1);
int? _matchTime(String s) {
  final m = RegExp(r'(\d{1,2}):(\d{2})').firstMatch(s);
  if (m == null) return null;
  return int.parse(m.group(1)!) * 60 + int.parse(m.group(2)!);
}

String _roomOf(String subtitle) {
  final i = subtitle.indexOf('·');
  return i >= 0 ? subtitle.substring(i + 1).trim() : '';
}

Color _kindColor(BlockKind k) => switch (k) {
      BlockKind.lecture => AppTheme.primaryBlue,
      BlockKind.classes => AppTheme.teal,
      BlockKind.study => AppTheme.accentGreen,
      BlockKind.exam => AppTheme.danger,
    };

IconData _kindIcon(BlockKind k) => switch (k) {
      BlockKind.lecture => Icons.cast_for_education_rounded,
      BlockKind.classes => Icons.groups_2_outlined,
      BlockKind.study => Icons.menu_book_rounded,
      BlockKind.exam => Icons.assignment_late_outlined,
    };

String _kindLabel(BlockKind k) => switch (k) {
      BlockKind.lecture => 'Bài giảng',
      BlockKind.classes => 'Lớp / Lab',
      BlockKind.study => 'Tự học',
      BlockKind.exam => 'Thi',
    };

class TimetableScreen extends ConsumerWidget {
  const TimetableScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final scheduleAsync = ref.watch(weeklyScheduleProvider);
    final planAsync = ref.watch(studyPlanProvider);

    return Scaffold(
      backgroundColor: AppTheme.backgroundDark,
      appBar: AppBar(
        title: scheduleAsync.maybeWhen(
          data: (s) => Text('Tuần ${s.currentWeek} / ${s.totalWeeks}'),
          orElse: () => const Text('Thời khoá biểu'),
        ),
      ),
      body: scheduleAsync.when(
        loading: () => const Center(
            child: CircularProgressIndicator(color: AppTheme.primaryBlue)),
        error: (e, _) => Center(
            child: Text('Lỗi: $e',
                style: const TextStyle(color: AppTheme.danger))),
        data: (schedule) {
          final sessions = planAsync.asData?.value ?? const [];
          final blocks = _buildBlocks(schedule, sessions);
          final byDay = <String, List<_Block>>{for (final d in _days) d: []};
          for (final b in blocks) {
            (byDay[b.day] ??= []).add(b);
          }
          for (final list in byDay.values) {
            list.sort((a, b) => a.startMin.compareTo(b.startMin));
          }

          return ListView(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 32),
            children: [
              const _Legend(),
              const SizedBox(height: 14),
              for (final d in _days)
                if ((byDay[d] ?? []).isNotEmpty) _DaySection(day: d, blocks: byDay[d]!),
            ],
          );
        },
      ),
    );
  }

  List<_Block> _buildBlocks(
      WeeklySchedule schedule, List<Map<String, dynamic>> sessions) {
    final blocks = <_Block>[];

    void addTimed(WeekItem it, BlockKind kind, int defaultMin) {
      final day = _matchDay(it.subtitle);
      final start = _matchTime(it.subtitle);
      if (day == null || start == null) return; // not a timed item
      blocks.add(_Block(
        day: day,
        startMin: start,
        endMin: start + defaultMin,
        title: it.title,
        sub: _roomOf(it.subtitle),
        kind: kind,
      ));
    }

    for (final l in schedule.lectures) {
      addTimed(l, BlockKind.lecture, _kLectureMin);
    }
    for (final c in schedule.classes) {
      addTimed(c, BlockKind.classes, _kClassMin);
    }

    // Study-plan sessions already carry day / time / duration.
    for (final s in sessions) {
      final day = (s['day'] ?? '').toString();
      final start = _matchTime((s['time'] ?? '').toString());
      if (start == null || !_days.contains(day)) continue;
      final dur = (s['duration'] is num) ? (s['duration'] as num).toInt() : 45;
      final type = (s['type'] ?? '').toString();
      blocks.add(_Block(
        day: day,
        startMin: start,
        endMin: start + dur,
        title: (s['subject'] ?? '').toString(),
        sub: '$dur phút${type.isNotEmpty ? ' · $type' : ''}',
        kind: BlockKind.study,
      ));
    }
    return blocks;
  }
}

class _DaySection extends StatelessWidget {
  final String day;
  final List<_Block> blocks;
  const _DaySection({required this.day, required this.blocks});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.only(top: 6, bottom: 8),
          child: Text(day,
              style: const TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w700,
                  color: AppTheme.textPrimary)),
        ),
        ...blocks.map((b) => _BlockCard(block: b)),
        const SizedBox(height: 8),
      ],
    );
  }
}

class _BlockCard extends StatelessWidget {
  final _Block block;
  const _BlockCard({required this.block});

  @override
  Widget build(BuildContext context) {
    final color = _kindColor(block.kind);
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        color: AppTheme.surfaceCard,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppTheme.cardBorder, width: 1),
      ),
      child: IntrinsicHeight(
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Colored time rail
            Container(
              width: 64,
              padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 8),
              decoration: BoxDecoration(
                color: color.withValues(alpha: 0.12),
                borderRadius: const BorderRadius.horizontal(
                    left: Radius.circular(12)),
              ),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(_fmt(block.startMin),
                      style: TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w700,
                          color: color)),
                  Text(_fmt(block.endMin),
                      style: const TextStyle(
                          fontSize: 11, color: AppTheme.textMuted)),
                ],
              ),
            ),
            Expanded(
              child: Padding(
                padding: const EdgeInsets.all(11),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Row(
                      children: [
                        Icon(_kindIcon(block.kind), size: 14, color: color),
                        const SizedBox(width: 6),
                        Expanded(
                          child: Text(block.title,
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: const TextStyle(
                                  fontSize: 13,
                                  fontWeight: FontWeight.w500,
                                  color: AppTheme.textPrimary)),
                        ),
                      ],
                    ),
                    const SizedBox(height: 3),
                    Text(
                      [
                        _kindLabel(block.kind),
                        if (block.sub.isNotEmpty) block.sub,
                      ].join(' · '),
                      style: const TextStyle(
                          fontSize: 11, color: AppTheme.textSecondary),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _Legend extends StatelessWidget {
  const _Legend();

  @override
  Widget build(BuildContext context) {
    Widget dot(BlockKind k) => Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
                width: 9,
                height: 9,
                decoration: BoxDecoration(
                    color: _kindColor(k), shape: BoxShape.circle)),
            const SizedBox(width: 5),
            Text(_kindLabel(k),
                style:
                    const TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
          ],
        );
    return Wrap(
      spacing: 16,
      runSpacing: 6,
      children: [
        dot(BlockKind.lecture),
        dot(BlockKind.classes),
        dot(BlockKind.study),
      ],
    );
  }
}
