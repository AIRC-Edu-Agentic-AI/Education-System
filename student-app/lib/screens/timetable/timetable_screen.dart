import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:student_agent/core/theme/app_theme.dart';
import 'package:student_agent/models/student_model.dart';
import 'package:student_agent/providers/providers.dart';

const _kLectureMin = 120;
const _kClassMin = 90;

const _days = ['Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7', 'CN'];

enum BlockKind { lecture, classes, study, exam }

class _Block {
  final String day;
  final int startMin;
  final int endMin;
  final String title;
  final String sub;
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

class _MiniCalendar extends StatefulWidget {
  final void Function(DateTime date)? onDaySelected;
  const _MiniCalendar({this.onDaySelected, super.key});

  @override
  State<_MiniCalendar> createState() => _MiniCalendarState();
}

class _MiniCalendarState extends State<_MiniCalendar> {
  DateTime _visible = DateTime.now();

  void _prevMonth() {
    setState(() {
      _visible = DateTime(_visible.year, _visible.month - 1, 1);
    });
  }

  void _nextMonth() {
    setState(() {
      _visible = DateTime(_visible.year, _visible.month + 1, 1);
    });
  }

  @override
  Widget build(BuildContext context) {
    final first = DateTime(_visible.year, _visible.month, 1);
    final last = DateTime(_visible.year, _visible.month + 1, 0);
    final startWeekday = first.weekday % 7; // convert Mon(1)..Sun(7) to 1..0
    final totalDays = last.day;
    final today = DateTime.now();

    final dayLabels = ['Cn', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7'];

    final cells = <int?>[];
    for (int i = 0; i < startWeekday; i++) cells.add(null);
    for (int d = 1; d <= totalDays; d++) cells.add(d);

    return Container(
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: AppTheme.surfaceCard,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppTheme.cardBorder, width: 1),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  'Tháng ${_visible.month}, ${_visible.year}',
                  style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700),
                ),
              ),
              IconButton(onPressed: _prevMonth, icon: const Icon(Icons.chevron_left)),
              IconButton(onPressed: _nextMonth, icon: const Icon(Icons.chevron_right)),
            ],
          ),
          const SizedBox(height: 4),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: dayLabels
                .map((l) => Expanded(
                      child: Center(
                        child: Text(l, style: TextStyle(fontSize: 12, color: AppTheme.textMuted)),
                      ),
                    ))
                .toList(),
          ),
          const SizedBox(height: 6),
          GridView.builder(
            physics: const NeverScrollableScrollPhysics(),
            shrinkWrap: true,
            itemCount: ((cells.length / 7).ceil()) * 7,
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 7,
              childAspectRatio: 1.2,
            ),
            itemBuilder: (context, index) {
              final v = index < cells.length ? cells[index] : null;
              final isToday = v != null && _visible.month == today.month && _visible.year == today.year && v == today.day;
              return Center(
                child: v == null
                    ? const SizedBox.shrink()
                    : InkWell(
                        onTap: () {
                          final dt = DateTime(_visible.year, _visible.month, v);
                          widget.onDaySelected?.call(dt);
                        },
                        borderRadius: BorderRadius.circular(20),
                        child: Container(
                          width: 30,
                          height: 30,
                          decoration: BoxDecoration(
                            color: isToday ? AppTheme.primaryBlue : Colors.grey.withOpacity(0.08),
                            shape: BoxShape.circle,
                          ),
                          child: Center(
                            child: Text(
                              '$v',
                              style: TextStyle(
                                color: isToday ? Colors.white : AppTheme.textPrimary,
                                fontSize: 12,
                              ),
                            ),
                          ),
                        ),
                      ),
              );
            },
          ),
        ],
      ),
    );
  }
}

// WeeklyTimeGrid removed per user request.

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
      BlockKind.classes => AppTheme.accentGreen,
      BlockKind.study => AppTheme.warning,
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

String _todayLabel() {
  final now = DateTime.now();
  final weekday = now.weekday;
  final index = switch (weekday) {
    2 => 0,
    3 => 1,
    4 => 2,
    5 => 3,
    6 => 4,
    7 => 5,
    1 => 6,
    _ => 6,
  };
  return _days[index];
}

class TimetableScreen extends ConsumerStatefulWidget {
  const TimetableScreen({super.key});

  @override
  ConsumerState<TimetableScreen> createState() => _TimetableScreenState();
}

class _TimetableScreenState extends ConsumerState<TimetableScreen> {
  final List<_Block> _addedBlocks = [];

  @override
  Widget build(BuildContext context) {
    final scheduleAsync = ref.watch(weeklyScheduleProvider);
    final planAsync = ref.watch(studyPlanProvider);

    return Scaffold(
      backgroundColor: AppTheme.backgroundDark,
      appBar: AppBar(
        title: scheduleAsync.maybeWhen(
          data: (s) => Text('Tuần ${s.currentWeek} / ${s.totalWeeks}'),
          orElse: () => const Text('Lịch học'),
        ),
        actions: [
          IconButton(
            onPressed: _showAddEventDialog,
            icon: const Icon(Icons.add_circle_outline_rounded),
          ),
        ],
      ),
      body: scheduleAsync.when(
        loading: () => const Center(
            child: CircularProgressIndicator(color: AppTheme.primaryBlue)),
        error: (e, _) => Center(
            child: Text('Lỗi: $e',
                style: const TextStyle(color: AppTheme.danger))),
        data: (schedule) {
          final sessions = planAsync.asData?.value ?? const [];
          final blocks = [..._buildBlocks(schedule, sessions), ..._addedBlocks];
          final byDay = <String, List<_Block>>{for (final d in _days) d: []};
          for (final b in blocks) {
            (byDay[b.day] ??= []).add(b);
          }
          for (final list in byDay.values) {
            list.sort((a, b) => a.startMin.compareTo(b.startMin));
          }

          final today = _todayLabel();
          return LayoutBuilder(
            builder: (context, constraints) {
              final isWide = constraints.maxWidth >= 760;
              final dayWidgets = _days
                  .map((day) => _DayColumn(
                        day: day,
                        blocks: byDay[day] ?? const [],
                        isToday: day == today,
                      ))
                  .toList();

              return SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(16, 8, 16, 28),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _WeekHeader(currentDay: today, onAdd: _showAddEventDialog),
                    const SizedBox(height: 12),
                    _MiniCalendar(onDaySelected: (d) => _showDayQuickView(d, blocks)),
                    const SizedBox(height: 12),
                    if (isWide)
                      Wrap(
                        spacing: 12,
                        runSpacing: 12,
                        children: dayWidgets
                            .map((widget) => ConstrainedBox(
                                  constraints: BoxConstraints(
                                    maxWidth: (constraints.maxWidth - 28) / 2,
                                  ),
                                  child: widget,
                                ))
                            .toList(),
                      )
                    else
                      ...dayWidgets,
                  ],
                ),
              );
            },
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
      if (day == null || start == null) return;
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

  Future<void> _showAddEventDialog([DateTime? preselect]) async {
    final titleController = TextEditingController();
    String selectedDay = preselect != null ? _labelFromDate(preselect) : _days[0];
    TimeOfDay selectedTime = preselect != null ? TimeOfDay(hour: preselect.hour, minute: preselect.minute) : const TimeOfDay(hour: 9, minute: 0);

    final result = await showDialog<Map<String, dynamic>>(
      context: context,
      builder: (dialogContext) {
        return StatefulBuilder(
          builder: (context, setDialogState) {
            return AlertDialog(
              backgroundColor: AppTheme.surfaceCard,
              title: const Text('Tạo lịch mới'),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  TextField(
                    controller: titleController,
                    decoration: const InputDecoration(
                      labelText: 'Tên lịch',
                      border: OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 12),
                  DropdownButtonFormField<String>(
                    value: selectedDay,
                    decoration: const InputDecoration(
                      labelText: 'Ngày',
                      border: OutlineInputBorder(),
                    ),
                    items: _days
                        .map((day) => DropdownMenuItem(value: day, child: Text(day)))
                        .toList(),
                    onChanged: (value) {
                      if (value != null) {
                        setDialogState(() => selectedDay = value);
                      }
                    },
                  ),
                  const SizedBox(height: 12),
                  ListTile(
                    contentPadding: EdgeInsets.zero,
                    title: const Text('Thời gian bắt đầu'),
                    subtitle: Text(selectedTime.format(context)),
                    trailing: const Icon(Icons.access_time),
                    onTap: () async {
                      final chosen = await showTimePicker(
                        context: context,
                        initialTime: selectedTime,
                      );
                      if (chosen != null) {
                        setDialogState(() => selectedTime = chosen);
                      }
                    },
                  ),
                ],
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.of(dialogContext).pop(),
                  child: const Text('Huỷ'),
                ),
                FilledButton(
                  onPressed: () {
                    final title = titleController.text.trim();
                    if (title.isEmpty) return;
                    Navigator.of(dialogContext).pop({
                      'title': title,
                      'day': selectedDay,
                      'time': selectedTime,
                    });
                  },
                  child: const Text('Thêm lịch'),
                ),
              ],
            );
          },
        );
      },
    );

    if (result != null) {
      final startMin = result['time'].hour * 60 + result['time'].minute;
      setState(() {
        _addedBlocks.add(_Block(
          day: result['day'] as String,
          startMin: startMin,
          endMin: startMin + 60,
          title: result['title'] as String,
          sub: 'Lịch mới · ${result['time'].format(context)}',
          kind: BlockKind.study,
        ));
      });
    }
  }

  String _labelFromDate(DateTime d) {
    switch (d.weekday) {
      case DateTime.monday:
        return 'Thứ 2';
      case DateTime.tuesday:
        return 'Thứ 3';
      case DateTime.wednesday:
        return 'Thứ 4';
      case DateTime.thursday:
        return 'Thứ 5';
      case DateTime.friday:
        return 'Thứ 6';
      case DateTime.saturday:
        return 'Thứ 7';
      case DateTime.sunday:
      default:
        return 'CN';
    }
  }

  Future<void> _showDayQuickView(DateTime date, List<_Block> blocks) async {
    final label = _labelFromDate(date);
    final dayBlocks = blocks.where((b) => b.day == label).toList();
    await showModalBottomSheet(
      context: context,
      backgroundColor: AppTheme.surfaceCard,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(12)),
      ),
      builder: (ctx) {
        return SizedBox(
          height: 360,
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(child: Text('Công việc ${label} — ${date.day}/${date.month}/${date.year}', style: const TextStyle(fontWeight: FontWeight.w700))),
                    IconButton(onPressed: () => Navigator.of(ctx).pop(), icon: const Icon(Icons.close)),
                  ],
                ),
                const SizedBox(height: 8),
                Expanded(
                  child: dayBlocks.isEmpty
                      ? Center(
                          child: Column(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              const Text('Không có công việc cho ngày này'),
                              const SizedBox(height: 12),
                              FilledButton(
                                onPressed: () {
                                  Navigator.of(ctx).pop();
                                  _showAddEventDialog();
                                },
                                child: const Text('Tạo lịch mới'),
                              ),
                            ],
                          ),
                        )
                      : ListView.builder(
                          itemCount: dayBlocks.length,
                          itemBuilder: (context, i) {
                            final b = dayBlocks[i];
                            return ListTile(
                              title: Text(b.title),
                              subtitle: Text('${b.timeLabel}${b.sub.isNotEmpty ? ' · ${b.sub}' : ''}'),
                              leading: CircleAvatar(backgroundColor: _kindColor(b.kind)),
                            );
                          },
                        ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}

class _WeekHeader extends StatelessWidget {
  final String currentDay;
  final VoidCallback onAdd;
  const _WeekHeader({required this.currentDay, required this.onAdd, super.key});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            const Expanded(
              child: Text(
                'Lịch học tuần này',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w700,
                  color: AppTheme.textPrimary,
                ),
              ),
            ),
            TextButton.icon(
              onPressed: onAdd,
              icon: const Icon(Icons.add, size: 18),
              label: const Text('Tạo lịch'),
            ),
          ],
        ),
        const SizedBox(height: 8),
        Container(
          width: double.infinity,
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
          decoration: BoxDecoration(
            color: AppTheme.surfaceCard,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: AppTheme.cardBorder, width: 1),
          ),
          child: Row(
            children: [
              Text(
                'Hôm nay · $currentDay',
                style: const TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  color: AppTheme.primaryBlue,
                ),
              ),
              const Spacer(),
              Text(
                'Giao diện dạng lịch tổng quan',
                style: TextStyle(
                  fontSize: 12,
                  color: AppTheme.textMuted,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _DayColumn extends StatelessWidget {
  final String day;
  final List<_Block> blocks;
  final bool isToday;

  const _DayColumn({
    required this.day,
    required this.blocks,
    required this.isToday,
    super.key,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppTheme.surfaceCard,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(
          color: isToday ? AppTheme.primaryBlue.withOpacity(0.45) : AppTheme.cardBorder,
          width: 1,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(
                day,
                style: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w700,
                  color: AppTheme.textPrimary,
                ),
              ),
              const Spacer(),
              if (isToday)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: AppTheme.primaryBlueGlow,
                    borderRadius: BorderRadius.circular(999),
                  ),
                  child: const Text(
                    'Today',
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w600,
                      color: AppTheme.primaryBlue,
                    ),
                  ),
                ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            '${blocks.length} lịch',
            style: TextStyle(
              fontSize: 12,
              color: AppTheme.textMuted,
            ),
          ),
          const SizedBox(height: 8),
          if (blocks.isEmpty)
            Padding(
              padding: const EdgeInsets.only(top: 4, bottom: 4),
              child: Text(
                'Không có lịch trong ngày',
                style: TextStyle(
                  fontSize: 12,
                  color: AppTheme.textMuted,
                ),
              ),
            )
          else
            ...blocks.map((block) => _MiniEventCard(block: block)),
        ],
      ),
    );
  }
}

class _MiniEventCard extends StatelessWidget {
  final _Block block;
  const _MiniEventCard({required this.block, super.key});

  @override
  Widget build(BuildContext context) {
    final color = _kindColor(block.kind);
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: color.withOpacity(0.12),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: color.withOpacity(0.24), width: 1),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(_kindIcon(block.kind), size: 14, color: color),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  block.title,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                    color: AppTheme.textPrimary,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            '${block.timeLabel} · ${_kindLabel(block.kind)}',
            style: const TextStyle(
              fontSize: 11,
              color: AppTheme.textSecondary,
            ),
          ),
          if (block.sub.isNotEmpty) ...[
            const SizedBox(height: 3),
            Text(
              block.sub,
              style: const TextStyle(
                fontSize: 11,
                color: AppTheme.textMuted,
              ),
            ),
          ],
        ],
      ),
    );
  }
}
