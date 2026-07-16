import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:student_agent/core/theme/app_theme.dart';
import 'package:student_agent/models/student_model.dart';

enum _EventType { lecture, klass, assignment, exam }

extension _EventTypeMeta on _EventType {
  String get label => switch (this) {
        _EventType.lecture => 'Bài giảng',
        _EventType.klass => 'Lớp học',
        _EventType.assignment => 'Bài nộp',
        _EventType.exam => 'Thi',
      };

  Color get color => switch (this) {
        _EventType.lecture => AppTheme.primaryBlue,
        _EventType.klass => AppTheme.accentGreen,
        _EventType.assignment => AppTheme.warning,
        _EventType.exam => AppTheme.danger,
      };

  Color get bg => switch (this) {
        _EventType.lecture => AppTheme.primaryBlueGlow,
        _EventType.klass => AppTheme.accentGreenGlow,
        _EventType.assignment => AppTheme.warningGlow,
        _EventType.exam => AppTheme.dangerGlow,
      };
}

class _TaggedEvent {
  final WeekItem item;
  final _EventType type;
  const _TaggedEvent(this.item, this.type);
}

class ThisWeekSection extends StatelessWidget {
  final WeeklySchedule schedule;
  const ThisWeekSection({super.key, required this.schedule});

  List<_TaggedEvent> get _sortedEvents {
    final events = [
      ...schedule.lectures.map((i) => _TaggedEvent(i, _EventType.lecture)),
      ...schedule.classes.map((i) => _TaggedEvent(i, _EventType.klass)),
      ...schedule.assignments.map((i) => _TaggedEvent(i, _EventType.assignment)),
      ...schedule.exams.map((i) => _TaggedEvent(i, _EventType.exam)),
    ];
    events.sort((a, b) => a.item.dateTime.compareTo(b.item.dateTime));
    return events;
  }

  @override
  Widget build(BuildContext context) {
    final events = _sortedEvents;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text(
              'Tuần này',
              style: TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.w500,
                  color: AppTheme.textPrimary),
            ),
            GestureDetector(
              onTap: () => context.go('/timetable'),
              child: const Text(
                'Xem lịch đầy đủ',
                style: TextStyle(fontSize: 12, color: AppTheme.primaryBlue),
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        if (events.isEmpty)
          const _EmptyWeek()
        else
          Container(
            decoration: BoxDecoration(
              color: AppTheme.surfaceCard,
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: AppTheme.cardBorder, width: 1),
            ),
            child: ListView.separated(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: events.length,
              separatorBuilder: (_, __) => const Divider(
                height: 0,
                indent: 16,
                endIndent: 16,
              ),
              itemBuilder: (_, i) => _EventRow(event: events[i]),
            ),
          ),
      ],
    );
  }
}

class _EventRow extends StatelessWidget {
  final _TaggedEvent event;
  const _EventRow({required this.event});

  (String time, String? location) get _timeParts {
    final parts = event.item.subtitle.split('·');
    final time = parts[0].trim();
    final location = parts.length > 1 ? parts[1].trim() : null;
    return (time, location);
  }

  @override
  Widget build(BuildContext context) {
    final type = event.type;
    final item = event.item;
    final (time, location) = _timeParts;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Colored left accent bar
          Container(
            width: 3,
            height: location != null ? 38 : 24,
            decoration: BoxDecoration(
              color: type.color,
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          const SizedBox(width: 10),

          // Type badge
          Padding(
            padding: const EdgeInsets.only(top: 1),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              decoration: BoxDecoration(
                color: type.bg,
                borderRadius: BorderRadius.circular(4),
              ),
              child: Text(
                type.label,
                style: TextStyle(
                  fontSize: 10,
                  fontWeight: FontWeight.w500,
                  color: type.color,
                ),
              ),
            ),
          ),
          const SizedBox(width: 8),

          // Title + location
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  item.title,
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight:
                        item.isUrgent ? FontWeight.w500 : FontWeight.normal,
                    color: item.isCompleted
                        ? AppTheme.textMuted
                        : AppTheme.textPrimary,
                    decoration: item.isCompleted
                        ? TextDecoration.lineThrough
                        : null,
                    decorationColor: AppTheme.textMuted,
                  ),
                ),
                if (location != null)
                  Padding(
                    padding: const EdgeInsets.only(top: 2),
                    child: Row(
                      children: [
                        const Icon(Icons.location_on_outlined,
                            size: 11, color: AppTheme.textSecondary),
                        const SizedBox(width: 2),
                        Text(
                          location,
                          style: const TextStyle(
                              fontSize: 11,
                              color: AppTheme.textSecondary),
                        ),
                      ],
                    ),
                  ),
              ],
            ),
          ),
          const SizedBox(width: 8),

          // Time + urgent flag
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                time,
                style: TextStyle(
                  fontSize: 11,
                  color: item.isUrgent ? AppTheme.danger : AppTheme.textSecondary,
                  fontWeight:
                      item.isUrgent ? FontWeight.w500 : FontWeight.normal,
                ),
              ),
              if (item.isUrgent)
                const Padding(
                  padding: EdgeInsets.only(top: 2),
                  child: Icon(Icons.warning_amber_rounded,
                      size: 12, color: AppTheme.danger),
                ),
            ],
          ),
        ],
      ),
    );
  }
}

class _EmptyWeek extends StatelessWidget {
  const _EmptyWeek();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 20),
      alignment: Alignment.center,
      decoration: BoxDecoration(
        color: AppTheme.surfaceCard,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppTheme.cardBorder, width: 1),
      ),
      child: const Text(
        'Tuần này không có sự kiện',
        style: TextStyle(fontSize: 13, color: AppTheme.textSecondary),
      ),
    );
  }
}
