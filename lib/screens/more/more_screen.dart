import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:student_agent/core/theme/app_theme.dart';
import 'package:student_agent/providers/auth_provider.dart';
import 'package:student_agent/providers/providers.dart';
import 'package:student_agent/widgets/glass_card.dart';

class MoreScreen extends ConsumerWidget {
  const MoreScreen({super.key});


  static const _items = [
     _MoreItem(
    icon: Icons.map_outlined,
    label: 'Study Plan',
    route: '/study-plan',
    color: AppTheme.accentGreen,
    ),
    _MoreItem(
      icon: Icons.book_outlined,
      label: 'MyEnrollment',
      route: '/my-enrollment',
      color: AppTheme.accentGreen,
    ),
    _MoreItem(
      icon: Icons.library_books_outlined,
      label: 'Resource Center',
      route: '/resources',
      color: AppTheme.primaryBlue,
    ),

    _MoreItem(
      icon: Icons.group_outlined,
      label: 'Nhóm học tập',
      route: '/study-groups',
      color: AppTheme.primaryBlue,
    ),
    _MoreItem(
      icon: Icons.person_outline_rounded,
      label: 'Profile',
      route: '/profile',
      color: AppTheme.accentGreen,
    ),
  ];

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final studentAsync = ref.watch(studentProvider);

    return Scaffold(
      backgroundColor: AppTheme.backgroundDark,
      appBar: AppBar(
        title: const Text('More'),
        backgroundColor: Colors.transparent,
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
        children: [
          // Profile summary
          studentAsync.when(
            loading: () => const _ProfileSkeleton(),
            error: (_, __) => const SizedBox.shrink(),
            data: (student) => GlassCard(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  Container(
                    width: 52,
                    height: 52,
                    decoration: const BoxDecoration(
                      gradient: AppTheme.blueGreenGradient,
                      shape: BoxShape.circle,
                    ),
                    child: Center(
                      child: Text(
                        student.shortName.isNotEmpty
                            ? student.shortName[0].toUpperCase()
                            : 'S',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 20,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          student.fullName,
                          style: const TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w600,
                            color: AppTheme.textPrimary,
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          'MSV ${student.studentId}',
                          style: const TextStyle(
                            fontSize: 13,
                            color: AppTheme.textSecondary,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const Icon(
                    Icons.chevron_right_rounded,
                    color: AppTheme.textMuted,
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 24),

          // ── Navigation grid ──
          const Text(
            'Quick Access',
            style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w500,
              color: AppTheme.textSecondary,
            ),
          ),
          const SizedBox(height: 12),
          GridView.count(
            crossAxisCount: 2,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            crossAxisSpacing: 12,
            mainAxisSpacing: 12,
            childAspectRatio: 1.5,
            children: _items
                .map((item) => _MoreCard(item: item))
                .toList(),
          ),

          const SizedBox(height: 32),

          // ── Logout ──
          GestureDetector(
            onTap: () async {
              await ref.read(authNotifierProvider).logout();
            },
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
              decoration: BoxDecoration(
                color: AppTheme.dangerGlow,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: AppTheme.danger.withValues(alpha: 0.3),
                  width: 1,
                ),
              ),
              child: const Row(
                children: [
                  Icon(
                    Icons.logout_rounded,
                    color: AppTheme.danger,
                    size: 20,
                  ),
                  SizedBox(width: 12),
                  Text(
                    'Đăng xuất',
                    style: TextStyle(
                      color: AppTheme.danger,
                      fontSize: 14,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ],
              ),
            ),
          ),

          const SizedBox(height: 16),
          const Center(
            child: Text(
              'Student Agent v1.0',
              style: TextStyle(fontSize: 11, color: AppTheme.textMuted),
            ),
          ),
        ],
      ),
    );
  }
}

class _MoreCard extends StatelessWidget {
  const _MoreCard({required this.item});
  final _MoreItem item;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () => context.go(item.route),
      child: Container(
        decoration: BoxDecoration(
          color: item.color.withValues(alpha: 0.08),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(
            color: item.color.withValues(alpha: 0.25),
            width: 1,
          ),
        ),
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Icon(item.icon, color: item.color, size: 24),
            Text(
              item.label,
              style: const TextStyle(
                color: AppTheme.textPrimary,
                fontSize: 13,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ProfileSkeleton extends StatelessWidget {
  const _ProfileSkeleton();

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      padding: const EdgeInsets.all(16),
      child: Row(
        children: [
          Container(
            width: 52,
            height: 52,
            decoration: const BoxDecoration(
              color: AppTheme.surfaceDark,
              shape: BoxShape.circle,
            ),
          ),
          const SizedBox(width: 14),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 120,
                height: 14,
                color: AppTheme.surfaceDark,
              ),
              const SizedBox(height: 6),
              Container(
                width: 80,
                height: 12,
                color: AppTheme.surfaceDark,
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _MoreItem {
  final IconData icon;
  final String label;
  final String route;
  final Color color;

  const _MoreItem({
    required this.icon,
    required this.label,
    required this.route,
    required this.color,
  });
}