import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:student_agent/core/theme/app_theme.dart';


import 'package:student_agent/providers/auth_provider.dart';
import 'package:student_agent/providers/providers.dart';

class MoreScreen extends ConsumerWidget {
  const MoreScreen({super.key});

  static const List<_QuickAction> _quickActions = [
    _QuickAction(
      icon: Icons.school_rounded,
      label: 'Study Plan',
      route: '/study-plan',
      color: Color(0xFF3B82F6),
    ),
    _QuickAction(
      icon: Icons.assignment_rounded,
      label: 'My Enrollment',
      route: '/my-enrollment',
      color: Color(0xFF10B981),
    ),
    _QuickAction(
      icon: Icons.library_books_rounded,
      label: 'Resource',
      route: '/resources',
      color: Color(0xFFF59E0B),
    ),
    _QuickAction(
      icon: Icons.group_rounded,
      label: 'Study Groups',
      route: '/study-groups',
      color: Color(0xFF8B5CF6),
    ),
  ];

  static const List<_RecentItem> _recentActivities = [
    _RecentItem(
      icon: Icons.book_rounded,
      title: 'Viewed: Week 7 Slides',
      time: '2 hours ago',
      color: Color(0xFF3B82F6),
      isUrgent: false,
    ),
    _RecentItem(
      icon: Icons.chat_rounded,
      title: 'New message from DATA201 group',
      time: '5 mins ago',
      color: Color(0xFF10B981),
      isUrgent: false,
    ),
    _RecentItem(
      icon: Icons.assignment_rounded,
      title: 'TMA-02 due soon',
      time: 'In 3 days',
      color: Color(0xFFEF4444),
      isUrgent: true,
    ),
  ];

  static const List<_SettingItem> _settings = [
    _SettingItem(
      icon: Icons.language_rounded,
      label: 'Language',
      value: 'English',
      route: null,
    ),
    _SettingItem(
      icon: Icons.dark_mode_rounded,
      label: 'Theme',
      value: 'Dark Mode',
      route: null,
    ),
    _SettingItem(
      icon: Icons.notifications_rounded,
      label: 'Notifications',
      value: 'On',
      route: null,
    ),
  ];

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final studentAsync = ref.watch(studentProvider);

    return Scaffold(
      backgroundColor: AppTheme.backgroundDark,
      appBar: AppBar(
        title: const Text(
          'More',
          style: TextStyle(
            fontSize: 22,
            fontWeight: FontWeight.w700,
            color: AppTheme.textPrimary,
          ),
        ),
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: const SizedBox.shrink(),
        actions: [
          IconButton(
            icon: const Icon(
              Icons.notifications_outlined,
              color: AppTheme.textSecondary,
              size: 24,
            ),
            onPressed: () => context.push('/notifications'),
          ),
        ],
      ),
      body: studentAsync.when(
        loading: () => const Center(
          child: CircularProgressIndicator(color: AppTheme.primaryBlue),
        ),
        error: (_, __) => const Center(
          child: Text(
            'Unable to load profile',
            style: TextStyle(color: AppTheme.danger),
          ),
        ),
        data: (student) => ListView(
          padding: const EdgeInsets.fromLTRB(16, 0, 16, 32),
          children: [
            const SizedBox(height: 8),

            // ── Banner Card ──
            _BannerCard(student: student),

            const SizedBox(height: 24),

            // ── Quick Actions ──
            _QuickActionsSection(actions: _quickActions),

            const SizedBox(height: 24),

            // ── Recent Activity ──
            _RecentActivitySection(activities: _recentActivities),

            const SizedBox(height: 24),

            // ── Settings Section ──
            _SettingsSection(settings: _settings),

            const SizedBox(height: 24),

            // ── Divider ──
            Container(
              height: 1,
              color: AppTheme.divider,
              margin: const EdgeInsets.symmetric(horizontal: 4),
            ),

            const SizedBox(height: 16),

            // ── Logout ──
            _LogoutButton(ref: ref),

            const SizedBox(height: 20),

            // ── Version ──
            Center(
              child: Text(
                'Student Agent v1.0',
                style: TextStyle(
                  fontSize: 11,
                  color: AppTheme.textMuted.withValues(alpha: 0.5),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ═══════════════════════════════════════════════════════════════════
// 1. BANNER CARD
// ═══════════════════════════════════════════════════════════════════

class _BannerCard extends StatelessWidget {
  final dynamic student;

  const _BannerCard({required this.student});

  double _calculateProgress() {
    final total = student.enrollments.length;
    if (total == 0) return 0.0;
    final completed = student.enrollments.where((e) => e.finalResult != null).length;
    return completed / total;
  }

  @override
  Widget build(BuildContext context) {
    final progress = _calculateProgress();
    final progressPercent = (progress * 100).round();

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [
            Color(0xFF1A2A4A),
            Color(0xFF0D1A2D),
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(
          color: AppTheme.primaryBlue.withValues(alpha: 0.2),
          width: 1,
        ),
        boxShadow: [
          BoxShadow(
            color: AppTheme.primaryBlue.withValues(alpha: 0.08),
            blurRadius: 20,
            spreadRadius: 2,
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: AppTheme.primaryBlue.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Icon(
                  Icons.auto_awesome_rounded,
                  color: AppTheme.primaryBlue,
                  size: 18,
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '👋 Welcome back, ${student.shortName}!',
                      style: const TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.w700,
                        color: AppTheme.textPrimary,
                      ),
                    ),
                    Text(
                      'Continue your learning journey',
                      style: TextStyle(
                        fontSize: 13,
                        color: AppTheme.textSecondary.withValues(alpha: 0.8),
                      ),
                    ),
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: AppTheme.accentGreen.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(
                    color: AppTheme.accentGreen.withValues(alpha: 0.2),
                  ),
                ),
                child: Text(
                  '$progressPercent%',
                  style: const TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w700,
                    color: AppTheme.accentGreen,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              _StatItem(
                value: '${student.enrollments.length}',
                label: 'Modules',
                icon: Icons.school_rounded,
                color: AppTheme.primaryBlue,
              ),
              _StatItem(
                value: '${student.demographics.studiedCredits}',
                label: 'Credits',
                icon: Icons.credit_card_rounded,
                color: AppTheme.accentGreen,
              ),
              _StatItem(
                value: '12',
                label: 'Study Days',
                icon: Icons.local_fire_department_rounded,
                color: const Color(0xFFF59E0B),
              ),
            ],
          ),
          const SizedBox(height: 14),
          Row(
            children: [
              const Icon(
                Icons.trending_up_rounded,
                size: 16,
                color: AppTheme.textSecondary,
              ),
              const SizedBox(width: 8),
              Text(
                'Academic Progress',
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w500,
                  color: AppTheme.textSecondary.withValues(alpha: 0.8),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(4),
                  child: LinearProgressIndicator(
                    value: progress,
                    minHeight: 6,
                    backgroundColor: AppTheme.surfaceDark,
                    valueColor: AlwaysStoppedAnimation<Color>(
                      progress >= 0.7
                          ? AppTheme.accentGreen
                          : progress >= 0.4
                              ? AppTheme.warning
                              : AppTheme.danger,
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Text(
                '$progressPercent%',
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  color: progress >= 0.7
                      ? AppTheme.accentGreen
                      : progress >= 0.4
                          ? AppTheme.warning
                          : AppTheme.danger,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

// ── Stat Item ──
class _StatItem extends StatelessWidget {
  final String value;
  final String label;
  final IconData icon;
  final Color color;

  const _StatItem({
    required this.value,
    required this.label,
    required this.icon,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 4),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.06),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: color.withValues(alpha: 0.1),
            width: 1,
          ),
        ),
        
        child: Column(
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(icon, size: 14, color: color),
                const SizedBox(width: 4),
                Text(
                  value,
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w700,
                    color: AppTheme.textPrimary,
                  ),
                ),
              ],
            ),
            Text(
              label,
              style: TextStyle(
                fontSize: 10,
                color: AppTheme.textSecondary.withValues(alpha: 0.7),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ═══════════════════════════════════════════════════════════════════
// 2. QUICK ACTIONS SECTION
// ═══════════════════════════════════════════════════════════════════

class _QuickActionsSection extends StatelessWidget {
  final List<_QuickAction> actions;

  const _QuickActionsSection({required this.actions});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text(
              '⚡ Quick Actions',
              style: TextStyle(
                fontSize: 15,
                fontWeight: FontWeight.w600,
                color: AppTheme.textPrimary,
              ),
            ),
            Text(
              '${actions.length} items',
              style: TextStyle(
                fontSize: 11,
                color: AppTheme.textMuted.withValues(alpha: 0.7),
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        Row(
          children: actions.map((action) {
            return Expanded(
              child: _QuickActionCard(action: action),
            );
          }).toList(),
        ),
      ],
    );
  }
}

// ── Quick Action Card ──
class _QuickActionCard extends StatelessWidget {
  final _QuickAction action;

  const _QuickActionCard({required this.action});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () => context.push(action.route),
      child: Container(
        margin: const EdgeInsets.only(right: 8),
        padding: const EdgeInsets.symmetric(vertical: 14),
        decoration: BoxDecoration(
          color: action.color.withValues(alpha: 0.06),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: action.color.withValues(alpha: 0.1),
            width: 1,
          ),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: action.color.withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(
                action.icon,
                color: action.color,
                size: 22,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              action.label,
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w500,
                color: AppTheme.textPrimary,
              ),
              textAlign: TextAlign.center,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
          ],
        ),
      ),
    );
  }
}

// ═══════════════════════════════════════════════════════════════════
// 3. RECENT ACTIVITY SECTION
// ═══════════════════════════════════════════════════════════════════

class _RecentActivitySection extends StatelessWidget {
  final List<_RecentItem> activities;

  const _RecentActivitySection({required this.activities});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text(
              '📌 Recent Activity',
              style: TextStyle(
                fontSize: 15,
                fontWeight: FontWeight.w600,
                color: AppTheme.textPrimary,
              ),
            ),
            GestureDetector(
              onTap: () {},
              child: Text(
                'View all',
                style: TextStyle(
                  fontSize: 12,
                  color: AppTheme.primaryBlue.withValues(alpha: 0.8),
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        Container(
          decoration: BoxDecoration(
            color: AppTheme.surfaceCard,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(
              color: AppTheme.cardBorder,
              width: 1,
            ),
          ),
          child: Column(
            children: activities.map((activity) {
              return _RecentItemWidget(activity: activity);
            }).toList(),
          ),
        ),
      ],
    );
  }
}

// ── Recent Item Widget ──
class _RecentItemWidget extends StatelessWidget {
  final _RecentItem activity;

  const _RecentItemWidget({required this.activity});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        border: Border(
          bottom: BorderSide(
            color: AppTheme.divider,
            width: 0.5,
          ),
        ),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: activity.color.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(
              activity.icon,
              color: activity.color,
              size: 18,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  activity.title,
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w500,
                    color: AppTheme.textPrimary,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                Row(
                  children: [
                    const Icon(
                      Icons.access_time_rounded,
                      size: 12,
                      color: AppTheme.textMuted,
                    ),
                    const SizedBox(width: 4),
                    Text(
                      activity.time,
                      style: TextStyle(
                        fontSize: 11,
                        color: AppTheme.textMuted.withValues(alpha: 0.8),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          if (activity.isUrgent)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: AppTheme.danger.withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: AppTheme.danger.withValues(alpha: 0.2),
                ),
              ),
              child: const Text(
                '⚠️',
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          const Icon(
            Icons.chevron_right_rounded,
            color: AppTheme.textMuted,
            size: 18,
          ),
        ],
      ),
    );
  }
}

// ═══════════════════════════════════════════════════════════════════
// 4. SETTINGS SECTION
// ═══════════════════════════════════════════════════════════════════

class _SettingsSection extends StatelessWidget {
  final List<_SettingItem> settings;

  const _SettingsSection({required this.settings});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          '⚙️ Settings',
          style: TextStyle(
            fontSize: 15,
            fontWeight: FontWeight.w600,
            color: AppTheme.textPrimary,
          ),
        ),
        const SizedBox(height: 12),
        Container(
          decoration: BoxDecoration(
            color: AppTheme.surfaceCard,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(
              color: AppTheme.cardBorder,
              width: 1,
            ),
          ),
          child: Column(
            children: settings.map((setting) {
              return _SettingRow(setting: setting);
            }).toList(),
          ),
        ),
      ],
    );
  }
}

// ── Setting Row ──
class _SettingRow extends StatelessWidget {
  final _SettingItem setting;

  const _SettingRow({required this.setting});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () {
        if (setting.route != null) {
          context.push(setting.route!);
        }
      },
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        decoration: BoxDecoration(
          border: Border(
            bottom: BorderSide(
              color: AppTheme.divider,
              width: 0.5,
            ),
          ),
        ),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: AppTheme.primaryBlue.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(
                setting.icon,
                color: AppTheme.primaryBlue,
                size: 18,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                setting.label,
                style: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w500,
                  color: AppTheme.textPrimary,
                ),
              ),
            ),
            Text(
              setting.value,
              style: TextStyle(
                fontSize: 13,
                color: AppTheme.textSecondary.withValues(alpha: 0.7),
              ),
            ),
            const SizedBox(width: 4),
            const Icon(
              Icons.chevron_right_rounded,
              color: AppTheme.textMuted,
              size: 18,
            ),
          ],
        ),
      ),
    );
  }
}

// ═══════════════════════════════════════════════════════════════════
// 5. LOGOUT BUTTON
// ═══════════════════════════════════════════════════════════════════

class _LogoutButton extends StatelessWidget {
  final WidgetRef ref;

  const _LogoutButton({required this.ref});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () async {
        final confirm = await showDialog<bool>(
          context: context,
          builder: (ctx) => AlertDialog(
            backgroundColor: AppTheme.surfaceDark,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(16),
              side: const BorderSide(color: AppTheme.cardBorder),
            ),
            title: const Text(
              'Log out',
              style: TextStyle(color: AppTheme.textPrimary),
            ),
            content: const Text(
              'Are you sure you want to log out?',
              style: TextStyle(color: AppTheme.textSecondary),
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(ctx, false),
                child: const Text(
                  'Cancel',
                  style: TextStyle(color: AppTheme.textSecondary),
                ),
              ),
              TextButton(
                onPressed: () => Navigator.pop(ctx, true),
                style: TextButton.styleFrom(
                  foregroundColor: AppTheme.danger,
                ),
                child: const Text('Log out'),
              ),
            ],
          ),
        );
        if (confirm == true) {
          await ref.read(authNotifierProvider).logout();
        }
      },
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12),
        decoration: BoxDecoration(
          color: AppTheme.dangerGlow,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(
            color: AppTheme.danger.withValues(alpha: 0.15),
            width: 1,
          ),
        ),
        child: const Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.logout_rounded,
              color: AppTheme.danger,
              size: 20,
            ),
            SizedBox(width: 10),
            Text(
              'Log out',
              style: TextStyle(
                color: AppTheme.danger,
                fontSize: 14,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ═══════════════════════════════════════════════════════════════════
// MODELS
// ═══════════════════════════════════════════════════════════════════

class _QuickAction {
  final IconData icon;
  final String label;
  final String route;
  final Color color;

  const _QuickAction({
    required this.icon,
    required this.label,
    required this.route,
    required this.color,
  });
}

class _RecentItem {
  final IconData icon;
  final String title;
  final String time;
  final Color color;
  final bool isUrgent;

  const _RecentItem({
    required this.icon,
    required this.title,
    required this.time,
    required this.color,
    required this.isUrgent,
  });
}

class _SettingItem {
  final IconData icon;
  final String label;
  final String value;
  final String? route;

  const _SettingItem({
    required this.icon,
    required this.label,
    required this.value,
    this.route,
  });
}