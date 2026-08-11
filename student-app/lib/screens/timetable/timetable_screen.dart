import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:student_agent/core/theme/app_theme.dart';
import 'package:student_agent/models/student_model.dart';
import 'package:student_agent/providers/providers.dart';

const _kLectureMin = 120;
const _kClassMin = 90;

const _days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

enum BlockKind { lecture, classes, study, exam }

class _Block {
  final String id;
  final String day;
  final int startMin;
  final int endMin;
  final String title;
  final String sub;
  final BlockKind kind;
  final DateTime? date;
  final bool isCustom;

  const _Block({
    required this.id,
    required this.day,
    required this.startMin,
    required this.endMin,
    required this.title,
    required this.sub,
    required this.kind,
    this.date,
    this.isCustom = false,
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
    final dayLabels = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

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
                  'Month ${_visible.month}, ${_visible.year}',
                  style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700),
                ),
              ),
              IconButton(onPressed: _prevMonth, icon: const Icon(Icons.chevron_left)),
              IconButton(onPressed: _nextMonth, icon: const Icon(Icons.chevron_right)),
            ],
          ),
          const SizedBox(height: 4),
          Row(
            children: dayLabels
                .map(
                  (lbl) => Expanded(
                    child: Center(
                      child: Text(
                        lbl,
                        style: const TextStyle(fontSize: 11, color: AppTheme.textMuted),
                      ),
                    ),
                  ),
                )
                .toList(),
          ),
          const SizedBox(height: 4),
          GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: cells.length,
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 7,
              childAspectRatio: 1.2,
            ),
            itemBuilder: (context, idx) {
              final val = cells[idx];
              if (val == null) return const SizedBox.shrink();
              final isToday = today.year == _visible.year &&
                  today.month == _visible.month &&
                  today.day == val;
              return InkWell(
                onTap: () {
                  if (widget.onDaySelected != null) {
                    widget.onDaySelected!(
                      DateTime(_visible.year, _visible.month, val),
                    );
                  }
                },
                child: Container(
                  margin: const EdgeInsets.all(2),
                  decoration: BoxDecoration(
                    color: isToday ? AppTheme.primaryBlueGlow : Colors.transparent,
                    borderRadius: BorderRadius.circular(6),
                    border: isToday
                        ? Border.all(color: AppTheme.primaryBlue, width: 1)
                        : null,
                  ),
                  child: Center(
                    child: Text(
                      '$val',
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: isToday ? FontWeight.w700 : FontWeight.w500,
                        color: isToday ? AppTheme.primaryBlue : AppTheme.textPrimary,
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

String? _matchDay(String s) => RegExp(r'(Mon|Tue|Wed|Thu|Fri|Sat|Sun|Thứ [2-7]|CN)').firstMatch(s)?.group(1);
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
      BlockKind.lecture => Icons.school_outlined,
      BlockKind.classes => Icons.groups_2_outlined,
      BlockKind.study => Icons.menu_book_rounded,
      BlockKind.exam => Icons.assignment_late_outlined,
    };

String _kindLabel(BlockKind k) => switch (k) {
      BlockKind.lecture => 'Lecture',
      BlockKind.classes => 'Class / Lab',
      BlockKind.study => 'Self-study',
      BlockKind.exam => 'Exam',
    };

String _todayLabel() {
  final now = DateTime.now();
  final index = (now.weekday - 1) % 7;
  return _days[index];
}

class TimetableScreen extends ConsumerStatefulWidget {
  const TimetableScreen({super.key});

  @override
  ConsumerState<TimetableScreen> createState() => _TimetableScreenState();
}

class _TimetableScreenState extends ConsumerState<TimetableScreen> {
  final List<_Block> _addedBlocks = [];
  final Set<String> _removedStdIds = {};

  @override
  Widget build(BuildContext context) {
    final scheduleAsync = ref.watch(weeklyScheduleProvider);
    final planAsync = ref.watch(studyPlanProvider);

    return Scaffold(
      backgroundColor: AppTheme.backgroundDark,
      appBar: AppBar(
        title: scheduleAsync.maybeWhen(
          data: (s) => Text('Week ${s.currentWeek} / ${s.totalWeeks}'),
          orElse: () => const Text('Timetable'),
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
            child: Text('Error: $e',
                style: const TextStyle(color: AppTheme.danger))),
        data: (schedule) {
          final sessions = planAsync.asData?.value ?? const [];
          final stdBlocks = _buildBlocks(schedule, sessions).where((b) => !_removedStdIds.contains(b.id)).toList();
          final blocks = [...stdBlocks, ..._addedBlocks];
          final byDay = <String, List<_Block>>{for (final d in _days) d: []};
          final byDate = <String, List<_Block>>{};
          for (final b in blocks) {
            (byDay[b.day] ??= []).add(b);
            if (b.date != null) {
              final key = '${b.date!.year}-${b.date!.month.toString().padLeft(2, '0')}-${b.date!.day.toString().padLeft(2, '0')}';
              (byDate[key] ??= []).add(b);
            }
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
        id: 'std-${kind.name}-${day}-${start}-${it.title}',
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
        id: 'std-study-${day}-${start}-${dur}-${(s['subject'] ?? '').toString()}',
        day: day,
        startMin: start,
        endMin: start + dur,
        title: (s['subject'] ?? '').toString(),
        sub: '$dur mins${type.isNotEmpty ? ' · $type' : ''}',
        kind: BlockKind.study,
      ));
    }
    return blocks;
  }

  Future<void> _showAddEventDialog([DateTime? preselect, _Block? editingBlock]) async {
    final titleController = TextEditingController(text: editingBlock?.title ?? '');
    DateTime selectedDate = preselect ?? editingBlock?.date ?? DateTime.now();
    String selectedDay = _labelFromDate(selectedDate);
    TimeOfDay selectedTime = editingBlock != null
        ? TimeOfDay(hour: editingBlock.startMin ~/ 60, minute: editingBlock.startMin % 60)
        : TimeOfDay(hour: selectedDate.hour == 0 && selectedDate.minute == 0 ? 9 : selectedDate.hour, minute: selectedDate.minute);
    if (selectedTime.hour == 0 && selectedTime.minute == 0) {
      selectedTime = const TimeOfDay(hour: 9, minute: 0);
    }

    final result = await showDialog<Map<String, dynamic>>(
      context: context,
      builder: (dialogContext) {
        return StatefulBuilder(
          builder: (context, setDialogState) {
            return AlertDialog(
              backgroundColor: AppTheme.surfaceDark,
              title: const Text('Create New Schedule'),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  TextField(
                    controller: titleController,
                    decoration: const InputDecoration(
                      labelText: 'Schedule Title',
                      border: OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 12),
                  ListTile(
                    contentPadding: EdgeInsets.zero,
                    title: const Text('Date'),
                    subtitle: Text('${selectedDate.day}/${selectedDate.month}/${selectedDate.year} ($selectedDay)'),
                    trailing: const Icon(Icons.calendar_month),
                    onTap: () async {
                      final picked = await showDatePicker(
                        context: context,
                        initialDate: selectedDate,
                        firstDate: DateTime.now().subtract(const Duration(days: 365)),
                        lastDate: DateTime.now().add(const Duration(days: 365)),
                      );
                      if (picked != null) {
                        setDialogState(() {
                          selectedDate = picked;
                          selectedDay = _labelFromDate(picked);
                        });
                      }
                    },
                  ),
                  const SizedBox(height: 12),
                  DropdownButtonFormField<String>(
                    value: selectedDay,
                    decoration: const InputDecoration(
                      labelText: 'Day of week',
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
                    title: const Text('Start time'),
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
                  child: const Text('Cancel'),
                ),
                FilledButton(
                  onPressed: () {
                    final title = titleController.text.trim();
                    if (title.isEmpty) return;
                    Navigator.of(dialogContext).pop({
                      'title': title,
                      'day': selectedDay,
                      'time': selectedTime,
                      'date': selectedDate,
                      'editingId': editingBlock?.id,
                    });
                  },
                  child: Text(editingBlock == null ? 'Add Schedule' : 'Update'),
                ),
              ],
            );
          },
        );
      },
    );

    if (result != null) {
      final startMin = result['time'].hour * 60 + result['time'].minute;
      final eventDate = result['date'] as DateTime;
      final existingId = result['editingId'] as String?;
      setState(() {
        if (existingId != null) {
          final index = _addedBlocks.indexWhere((b) => b.id == existingId);
          if (index >= 0) {
            _addedBlocks[index] = _Block(
              id: existingId,
              day: result['day'] as String,
              startMin: startMin,
              endMin: startMin + 60,
              title: result['title'] as String,
              sub: 'New Schedule · ${result['time'].format(context)}',
              kind: BlockKind.study,
              date: eventDate,
              isCustom: true,
            );
            return;
          }
          _removedStdIds.add(existingId);
        }
        _addedBlocks.add(_Block(
          id: 'custom-${DateTime.now().millisecondsSinceEpoch}',
          day: result['day'] as String,
          startMin: startMin,
          endMin: startMin + 60,
          title: result['title'] as String,
          sub: 'New Schedule · ${result['time'].format(context)}',
          kind: BlockKind.study,
          date: eventDate,
          isCustom: true,
        ));
      });
      _syncStudyPlanWithBackend();
    }
  }

  Future<void> _syncStudyPlanWithBackend() async {
    try {
      final api = ref.read(apiServiceProvider);
      final studentId = ref.read(activeStudentIdProvider);

      final current = await api.getStudyPlan(studentId);
      final mutable = List<Map<String, dynamic>>.from(current);

      for (final rid in _removedStdIds) {
        final m = RegExp(r'std-study-(.+?)-(\d+)-(\d+)-(.+)').firstMatch(rid);
        if (m != null) {
          final day = m.group(1) ?? '';
          final start = int.tryParse(m.group(2) ?? '0') ?? 0;
          final dur = int.tryParse(m.group(3) ?? '0') ?? 0;
          final subj = (m.group(4) ?? '').replaceAll('%', '-');
          mutable.removeWhere((s) =>
              (s['day'] ?? '') == day &&
              (s['time'] ?? '') == _fmt(start) &&
              ((s['duration'] ?? 0) == dur || (s['duration'] ?? 0) == dur) &&
              ((s['subject'] ?? '') == subj || (s['subject'] ?? '') == subj));
        }
      }

      for (final b in _addedBlocks.where((b) => b.isCustom && b.kind == BlockKind.study)) {
        mutable.add({
          'subject': b.title,
          'type': 'manual',
          'duration': b.endMin - b.startMin,
          'day': b.day,
          'time': _fmt(b.startMin),
          'sm2_interval': 1,
        });
      }

      final ok = await api.updateStudyPlan(studentId, mutable);
      if (!ok) {
        print('Failed to sync study plan');
      }
    } catch (e, s) {
      print('sync error: $e');
      print(s);
    }
  }

  String _labelFromDate(DateTime d) {
    switch (d.weekday) {
      case DateTime.monday:
        return 'Mon';
      case DateTime.tuesday:
        return 'Tue';
      case DateTime.wednesday:
        return 'Wed';
      case DateTime.thursday:
        return 'Thu';
      case DateTime.friday:
        return 'Fri';
      case DateTime.saturday:
        return 'Sat';
      case DateTime.sunday:
      default:
        return 'Sun';
    }
  }

  Future<void> _showDayQuickView(DateTime date, List<_Block> blocks) async {
    final label = _labelFromDate(date);
    final dayBlocks = blocks.where((b) => b.day == label).toList();
    await showModalBottomSheet(
      context: context,
      backgroundColor: AppTheme.surfaceDark,
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
                    Expanded(child: Text('Tasks ${label} — ${date.day}/${date.month}/${date.year}', style: const TextStyle(fontWeight: FontWeight.w700))),
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
                              const Text('No tasks for this day'),
                              const SizedBox(height: 12),
                              FilledButton(
                                onPressed: () {
                                  Navigator.of(ctx).pop();
                                  _showAddEventDialog(date);
                                },
                                child: const Text('Create New Schedule'),
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
                              onTap: () {
                                Navigator.of(ctx).pop();
                                _showEventActions(b);
                              },
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
  
  void _showEventActions(_Block block) {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppTheme.surfaceDark,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (ctx) {
        final allowEdit = block.isCustom || block.kind == BlockKind.study;
        return Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(block.title, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
              const SizedBox(height: 8),
              Text('${block.timeLabel} · ${_kindLabel(block.kind)}', style: const TextStyle(color: AppTheme.textSecondary)),
              if (block.sub.isNotEmpty) ...[
                const SizedBox(height: 8),
                Text(block.sub, style: const TextStyle(color: AppTheme.textMuted)),
              ],
              if (block.date != null) ...[
                const SizedBox(height: 8),
                Text('Date: ${block.date!.day}/${block.date!.month}/${block.date!.year}', style: const TextStyle(color: AppTheme.textMuted)),
              ],
              const SizedBox(height: 16),
              Row(
                children: [
                  if (allowEdit)
                    Expanded(
                      child: FilledButton(
                        onPressed: () {
                          Navigator.of(ctx).pop();
                          final pre = block.date ?? _dateForBlock(block);
                          _showAddEventDialog(pre, block);
                        },
                        child: const Text('Edit'),
                      ),
                    ),
                  if (allowEdit) const SizedBox(width: 12),
                  Expanded(
                    child: FilledButton(
                      onPressed: () {
                        Navigator.of(ctx).pop();
                        if (block.isCustom) {
                          setState(() {
                            _addedBlocks.removeWhere((b) => b.id == block.id);
                          });
                          _syncStudyPlanWithBackend();
                        } else if (block.kind == BlockKind.study) {
                          setState(() {
                            _removedStdIds.add(block.id);
                          });
                          _syncStudyPlanWithBackend();
                        }
                      },
                      style: FilledButton.styleFrom(backgroundColor: (block.isCustom || block.kind == BlockKind.study) ? AppTheme.danger : AppTheme.surfaceCard),
                      child: Text((block.isCustom || block.kind == BlockKind.study) ? 'Delete' : 'Close'),
                    ),
                  ),
                ],
              ),
            ],
          ),
        );
      },
    );
  }

  DateTime _dateForBlock(_Block b) {
    final now = DateTime.now();
    int targetWeekday;
    switch (b.day) {
      case 'Mon':
        targetWeekday = DateTime.monday;
        break;
      case 'Tue':
        targetWeekday = DateTime.tuesday;
        break;
      case 'Wed':
        targetWeekday = DateTime.wednesday;
        break;
      case 'Thu':
        targetWeekday = DateTime.thursday;
        break;
      case 'Fri':
        targetWeekday = DateTime.friday;
        break;
      case 'Sat':
        targetWeekday = DateTime.saturday;
        break;
      case 'Sun':
      default:
        targetWeekday = DateTime.sunday;
    }
    final delta = (targetWeekday - now.weekday + 7) % 7;
    final date = DateTime(now.year, now.month, now.day).add(Duration(days: delta));
    final hour = b.startMin ~/ 60;
    final minute = b.startMin % 60;
    return DateTime(date.year, date.month, date.day, hour, minute);
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
                'Weekly Timetable',
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
              label: const Text('Create Schedule'),
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
                'Today · $currentDay',
                style: const TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  color: AppTheme.primaryBlue,
                ),
              ),
              const Spacer(),
              Text(
                'Weekly Overview Calendar',
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
            '${blocks.length} events',
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
                'No schedule for this day',
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
    return InkWell(
      borderRadius: BorderRadius.circular(14),
      onTap: () {
        final state = context.findAncestorStateOfType<_TimetableScreenState>();
        state?._showEventActions(block);
      },
      child: Container(
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
      ),
    );
  }
}
