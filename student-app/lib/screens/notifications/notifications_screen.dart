import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:student_agent/core/theme/app_theme.dart';
import 'package:student_agent/models/student_model.dart';
import 'package:student_agent/providers/providers.dart';
import 'package:student_agent/widgets/formatted_text.dart';

Color notificationColor(String type) => switch (type) {
      'deadline_critical' => AppTheme.danger,
      'deadline_warning' => AppTheme.warning,
      'risk_intervention' => AppTheme.danger,
      'assessment_shock' => AppTheme.danger,
      'wellbeing' => AppTheme.accentGreen,
      'milestone_check' => AppTheme.warning,
      'course_guidance' => AppTheme.primaryBlue,
      _ => AppTheme.primaryBlue,
    };

IconData notificationIcon(String type) => switch (type) {
      'deadline_critical' || 'deadline_warning' => Icons.schedule_rounded,
      'risk_intervention' || 'intervention' => Icons.warning_amber_rounded,
      'assessment_shock' => Icons.trending_down_rounded,
      'wellbeing' => Icons.favorite_outline_rounded,
      'milestone_check' => Icons.flag_outlined,
      'course_guidance' => Icons.school_outlined,
      'vle_inactivity' => Icons.visibility_off_outlined,
      _ => Icons.notifications_outlined,
    };

String relativeTime(DateTime t) {
  final d = DateTime.now().difference(t);
  if (d.inMinutes < 1) return 'Just now';
  if (d.inMinutes < 60) return '${d.inMinutes} mins ago';
  if (d.inHours < 24) return '${d.inHours} hrs ago';
  return '${d.inDays} days ago';
}

/// Shared action handler used by both the list detail sheet and the dashboard.
void handleNotificationAction(
  BuildContext context,
  WidgetRef ref,
  NotificationModel notif,
  NotificationAction action,
) {
  ref.read(notificationProvider.notifier).markRead(notif.id);
  switch (action.action) {
    case 'open_chat':
      context.push('/chat');
    case 'update_milestone':
      final p = action.payload;
      final idAssessment = p['id_assessment'] as int?;
      final milestoneId = p['milestone_id'] as String? ?? '';
      final status = p['status'] as String? ?? 'done';
      if (idAssessment != null) {
        final api = ref.read(apiServiceProvider);
        final studentId = ref.read(activeStudentIdProvider);
        api.updateMilestoneStatus(
          studentId: studentId,
          idAssessment: idAssessment,
          milestoneId: milestoneId,
          status: status,
        );
        ref.invalidate(assignmentMilestonesProvider(idAssessment));
        final msg = status == 'done'
            ? 'Marked as completed ✓'
            : status == 'in_progress'
                ? 'In progress ▶'
                : status == 'pending'
                    ? 'Set to not started'
                    : 'Updated progress';
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(msg), duration: const Duration(seconds: 2)),
        );
      }
    case 'snooze':
      break;
  }
}

class NotificationsScreen extends ConsumerWidget {
  const NotificationsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final notifAsync = ref.watch(notificationProvider);

    return Scaffold(
      backgroundColor: AppTheme.backgroundDark,
      appBar: AppBar(
        title: const Text('Notifications'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded,
              size: 18, color: AppTheme.textSecondary),
          onPressed: () =>
              context.canPop() ? context.pop() : context.go('/'),
        ),
        actions: [
          if (ref.watch(unreadCountProvider) > 0)
            TextButton.icon(
              onPressed: () {
                ref.read(notificationProvider.notifier).markAllRead();
              },
              icon: const Icon(Icons.done_all_rounded, size: 16, color: AppTheme.primaryBlue),
              label: const Text(
                'Mark all read',
                style: TextStyle(color: AppTheme.primaryBlue, fontSize: 12, fontWeight: FontWeight.w600),
              ),
            ),
        ],
      ),
      body: notifAsync.when(
        loading: () => const Center(
            child: CircularProgressIndicator(color: AppTheme.primaryBlue)),
        error: (e, _) => Center(
            child: Text('Error: $e',
                style: const TextStyle(color: AppTheme.danger))),
        data: (notifs) {
          if (notifs.isEmpty) {
            return const Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.notifications_none_rounded,
                      size: 48, color: AppTheme.textMuted),
                  SizedBox(height: 12),
                  Text('No notifications',
                      style: TextStyle(color: AppTheme.textSecondary)),
                ],
              ),
            );
          }
          return ListView.separated(
            padding: const EdgeInsets.all(12),
            itemCount: notifs.length,
            separatorBuilder: (_, __) => const SizedBox(height: 8),
            itemBuilder: (_, i) => _NotificationTile(notification: notifs[i]),
          );
        },
      ),
    );
  }
}

class _NotificationTile extends ConsumerWidget {
  final NotificationModel notification;
  const _NotificationTile({required this.notification});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final color = notificationColor(notification.type);
    final isUnread = !notification.read;

    return GestureDetector(
      onTap: () {
        if (isUnread) {
          ref.read(notificationProvider.notifier).markRead(notification.id);
        }
        _showDetail(context, ref, notification);
      },
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: isUnread ? const Color(0xFF1E293B) : AppTheme.surfaceCard,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(
            color: isUnread
                ? AppTheme.danger.withValues(alpha: 0.7)
                : AppTheme.cardBorder,
            width: isUnread ? 1.5 : 1,
          ),
          boxShadow: isUnread
              ? [
                  BoxShadow(
                    color: AppTheme.danger.withValues(alpha: 0.15),
                    blurRadius: 10,
                    offset: const Offset(0, 4),
                  ),
                ]
              : null,
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Stack(
              children: [
                Container(
                  width: 40,
                  height: 40,
                  decoration: BoxDecoration(
                    color: color.withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Icon(notificationIcon(notification.type),
                      size: 20, color: color),
                ),
                if (isUnread)
                  Positioned(
                    right: 0,
                    top: 0,
                    child: Container(
                      width: 12,
                      height: 12,
                      decoration: BoxDecoration(
                        color: AppTheme.danger,
                        shape: BoxShape.circle,
                        border: Border.all(color: AppTheme.surfaceCard, width: 2),
                      ),
                    ),
                  ),
              ],
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          notification.title,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: TextStyle(
                            fontSize: 14,
                            fontWeight: isUnread
                                ? FontWeight.bold
                                : FontWeight.w500,
                            color: AppTheme.textPrimary,
                          ),
                        ),
                      ),
                      if (isUnread) ...[
                        const SizedBox(width: 8),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
                          decoration: BoxDecoration(
                            color: AppTheme.danger,
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: const Text(
                            'UNREAD',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 9,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ],
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text(
                    notification.body,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      fontSize: 12,
                      color: isUnread ? Colors.white70 : AppTheme.textSecondary,
                      height: 1.3,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    relativeTime(notification.createdAt),
                    style: const TextStyle(
                        fontSize: 11, color: AppTheme.textMuted),
                  ),
                ],
              ),
            ),
            const Icon(Icons.chevron_right_rounded,
                color: AppTheme.textMuted, size: 18),
          ],
        ),
      ),
    );
  }
}

void _showDetail(
    BuildContext context, WidgetRef ref, NotificationModel notif) {
  showModalBottomSheet(
    context: context,
    backgroundColor: AppTheme.surfaceCard,
    isScrollControlled: true,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
    ),
    builder: (sheetContext) {
      final color = notificationColor(notif.type);
      return DraggableScrollableSheet(
        expand: false,
        initialChildSize: 0.5,
        minChildSize: 0.3,
        maxChildSize: 0.9,
        builder: (_, scrollController) => SingleChildScrollView(
          controller: scrollController,
          padding: const EdgeInsets.fromLTRB(20, 12, 20, 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Center(
                child: Container(
                  width: 40,
                  height: 4,
                  margin: const EdgeInsets.only(bottom: 16),
                  decoration: BoxDecoration(
                    color: AppTheme.textMuted,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
              Row(
                children: [
                  Container(
                    width: 40,
                    height: 40,
                    decoration: BoxDecoration(
                      color: color.withValues(alpha: 0.12),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Icon(notificationIcon(notif.type),
                        size: 20, color: color),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      notif.title,
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                        color: AppTheme.textPrimary,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                relativeTime(notif.createdAt),
                style: const TextStyle(fontSize: 12, color: AppTheme.textMuted),
              ),
              const SizedBox(height: 16),
              FormattedText(
                notif.body,
                baseStyle: const TextStyle(
                    fontSize: 14, color: AppTheme.textSecondary, height: 1.5),
              ),
              if (notif.actionOptions.isNotEmpty) ...[
                const SizedBox(height: 20),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: notif.actionOptions
                      .map((action) => _DetailActionChip(
                            action: action,
                            onTap: () {
                              Navigator.of(sheetContext).pop();
                              handleNotificationAction(
                                  context, ref, notif, action);
                            },
                          ))
                      .toList(),
                ),
              ],
            ],
          ),
        ),
      );
    },
  );
}

class _DetailActionChip extends StatelessWidget {
  final NotificationAction action;
  final VoidCallback onTap;
  const _DetailActionChip({required this.action, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final isPrimary = action.action == 'open_chat';
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        decoration: BoxDecoration(
          color: isPrimary
              ? AppTheme.primaryBlue.withValues(alpha: 0.15)
              : AppTheme.surfaceDark,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: isPrimary
                ? AppTheme.primaryBlue.withValues(alpha: 0.4)
                : AppTheme.cardBorder,
            width: 1,
          ),
        ),
        child: Text(
          action.label,
          style: TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.w500,
            color: isPrimary ? AppTheme.primaryBlue : AppTheme.textSecondary,
          ),
        ),
      ),
    );
  }
}
