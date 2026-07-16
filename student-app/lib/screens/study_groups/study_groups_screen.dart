import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:student_agent/core/theme/app_theme.dart';
import 'package:student_agent/models/study_group_model.dart';
import 'package:student_agent/providers/study_group_provider.dart';
import 'package:student_agent/screens/study_groups/dialogs/create_group_dialog.dart';
import 'package:student_agent/screens/study_groups/dialogs/join_group_dialog.dart';
import 'package:student_agent/screens/study_groups/widgets/group_card.dart';

class StudyGroupsScreen extends ConsumerWidget {
  const StudyGroupsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final groupsAsync = ref.watch(myGroupsProvider);

    return Scaffold(
      backgroundColor: AppTheme.backgroundDark,
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded,
              size: 18, color: AppTheme.textSecondary),
          onPressed: () => context.go('/more'),
          tooltip: 'Quay lại',
        ),
        title: const Text('Nhóm học tập'),
        backgroundColor: Colors.transparent,
        actions: [
          IconButton(
            icon: const Icon(Icons.add_rounded, color: AppTheme.primaryBlue),
            onPressed: () => _showCreateGroupDialog(context, ref),
            tooltip: 'Tạo nhóm mới',
          ),
          IconButton(
            icon: const Icon(Icons.login_rounded, color: AppTheme.primaryBlue),
            onPressed: () => _showJoinGroupDialog(context, ref),
            tooltip: 'Tham gia nhóm',
          ),
        ],
      ),
      body: groupsAsync.when(
        loading: () => const Center(
          child: CircularProgressIndicator(color: AppTheme.primaryBlue),
        ),
        error: (e, _) => Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.error_outline_rounded, size: 48, color: AppTheme.danger),
              const SizedBox(height: 12),
              Text(
                e.toString(),
                style: const TextStyle(color: AppTheme.danger),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
        data: (groups) {
          // ⭐ LỌC DỮ LIỆU AN TOÀN
          final validGroups = groups.where((g) {
            try {
              // Kiểm tra members có phải là List không
              return g.members is List;
            } catch (_) {
              return false;
            }
          }).toList();

          if (validGroups.isEmpty) {
            return _EmptyState(
              onCreate: () => _showCreateGroupDialog(context, ref),
              onJoin: () => _showJoinGroupDialog(context, ref),
            );
          }

          return RefreshIndicator(
            onRefresh: () async {
              ref.invalidate(myGroupsProvider);
            },
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: validGroups.length,
              itemBuilder: (_, index) {
                // ⭐ SỬ DỤNG index AN TOÀN
                if (index >= validGroups.length) return const SizedBox.shrink();
                
                final group = validGroups[index];
                
                // ⭐ KIỂM TRA group hợp lệ
                if (group.id.isEmpty) return const SizedBox.shrink();

                return GroupCard(
                  group: group,
                  onTap: () {
                    final groupId = group.id.isNotEmpty ? group.id : 'unknown';
                    context.push('/study-group/$groupId');
                  },
                  onLeave: () => _showLeaveDialog(context, ref, group),
                );
              },
            ),
          );
        },
      ),
    );
  }

  void _showCreateGroupDialog(BuildContext context, WidgetRef ref) {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (_) => CreateGroupDialog(
        onCreated: () {
          ref.invalidate(myGroupsProvider);
        },
      ),
    );
  }

  void _showJoinGroupDialog(BuildContext context, WidgetRef ref) {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (_) => JoinGroupDialog(
        onJoined: () {
          ref.invalidate(myGroupsProvider);
        },
      ),
    );
  }

  void _showLeaveDialog(BuildContext context, WidgetRef ref, StudyGroup group) {
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        backgroundColor: AppTheme.surfaceDark,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
          side: const BorderSide(color: AppTheme.cardBorder),
        ),
        title: const Text(
          'Rời nhóm?',
          style: TextStyle(color: AppTheme.textPrimary),
        ),
        content: Text(
          'Bạn có chắc chắn muốn rời nhóm "${group.name}"?',
          style: const TextStyle(color: AppTheme.textSecondary),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Hủy'),
          ),
          ElevatedButton(
            onPressed: () async {
              Navigator.pop(context);
              try {
                await ref.read(leaveGroupProvider(group.id).future);
                ref.invalidate(myGroupsProvider);
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Đã rời nhóm')),
                  );
                }
              } catch (e) {
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text('Lỗi: $e'),
                      backgroundColor: AppTheme.danger,
                    ),
                  );
                }
              }
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.danger,
              foregroundColor: Colors.white,
            ),
            child: const Text('Rời nhóm'),
          ),
        ],
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  final VoidCallback onCreate;
  final VoidCallback onJoin;

  const _EmptyState({required this.onCreate, required this.onJoin});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 80,
              height: 80,
              decoration: BoxDecoration(
                gradient: AppTheme.blueGreenGradient,
                borderRadius: BorderRadius.circular(20),
              ),
              child: const Icon(
                Icons.group_outlined,
                color: Colors.white,
                size: 40,
              ),
            ),
            const SizedBox(height: 16),
            const Text(
              'Chưa có nhóm học tập',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w600,
                color: AppTheme.textPrimary,
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'Tạo nhóm mới hoặc tham gia bằng mã',
              style: TextStyle(
                fontSize: 14,
                color: AppTheme.textSecondary,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                ElevatedButton.icon(
                  onPressed: onCreate,
                  icon: const Icon(Icons.add_rounded),
                  label: const Text('Tạo nhóm'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppTheme.primaryBlue,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(
                      horizontal: 20,
                      vertical: 12,
                    ),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                OutlinedButton.icon(
                  onPressed: onJoin,
                  icon: const Icon(Icons.login_rounded),
                  label: const Text('Tham gia'),
                  style: OutlinedButton.styleFrom(
                    foregroundColor: AppTheme.textPrimary,
                    side: const BorderSide(color: AppTheme.cardBorder),
                    padding: const EdgeInsets.symmetric(
                      horizontal: 20,
                      vertical: 12,
                    ),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}