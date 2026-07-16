import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:student_agent/core/theme/app_theme.dart';
import 'package:student_agent/providers/study_group_provider.dart';

class GroupDetailScreen extends ConsumerWidget {
  final String groupId;

  const GroupDetailScreen({super.key, required this.groupId});

  // ⭐ Hàm lấy tên giả theo memberId
  String _getMemberName(String memberId) {
    // Tạo tên giả dựa trên ID
    final names = {
      '28400': 'Nguyễn Văn An',
      '28401': 'Trần Thị Bình',
      '28402': 'Lê Văn Cường',
      '28405': 'Phạm Thị Dung',
      '28410': 'Hoàng Văn Em',
      '28411': 'Ngô Thị Phương',
      '28412': 'Đỗ Văn Giang',
    };
    return names[memberId] ?? 'Thành viên ${memberId.substring(memberId.length - 3)}';
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final groupAsync = ref.watch(groupDetailProvider(groupId));

    return Scaffold(
      backgroundColor: AppTheme.backgroundDark,
      appBar: AppBar(
        title: const Text('Chi tiết nhóm'),
        backgroundColor: Colors.transparent,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded,
              size: 18, color: AppTheme.textSecondary),
          onPressed: () => context.pop(),
        ),
      ),
      body: groupAsync.when(
        loading: () => const Center(
          child: CircularProgressIndicator(color: AppTheme.primaryBlue),
        ),
        error: (e, _) => Center(
          child: Text(
            'Lỗi: $e',
            style: const TextStyle(color: AppTheme.danger),
          ),
        ),
        data: (group) => ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // Group info
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppTheme.surfaceCard,
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: AppTheme.cardBorder, width: 1),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    group.name,
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.w600,
                      color: AppTheme.textPrimary,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Mã: ${group.groupCode}',
                    style: const TextStyle(
                      fontSize: 13,
                      color: AppTheme.textSecondary,
                    ),
                  ),
                  if (group.description.isNotEmpty) ...[
                    const SizedBox(height: 8),
                    Text(
                      group.description,
                      style: const TextStyle(
                        fontSize: 14,
                        color: AppTheme.textSecondary,
                      ),
                    ),
                  ],
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      const Icon(
                        Icons.group_outlined,
                        size: 14,
                        color: AppTheme.textSecondary,
                      ),
                      const SizedBox(width: 4),
                      Text(
                        '${group.totalMembers} thành viên',
                        style: const TextStyle(
                          fontSize: 13,
                          color: AppTheme.textSecondary,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Members list
            const Text(
              'Thành viên',
              style: TextStyle(
                fontSize: 15,
                fontWeight: FontWeight.w500,
                color: AppTheme.textPrimary,
              ),
            ),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppTheme.surfaceCard,
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: AppTheme.cardBorder, width: 1),
              ),
              child: ListView.builder(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: group.members.length,
                itemBuilder: (_, i) {
                  final memberId = group.members[i];
                  final isCreator = group.createdBy == memberId;
                  final memberName = _getMemberName(memberId);
                  
                  return ListTile(
                    leading: CircleAvatar(
                      radius: 18,
                      backgroundColor: isCreator 
                          ? AppTheme.primaryBlueGlow 
                          : AppTheme.surfaceDark,
                      child: Text(
                        memberName.isNotEmpty ? memberName[0].toUpperCase() : '?',
                        style: TextStyle(
                          color: isCreator 
                              ? AppTheme.primaryBlue 
                              : AppTheme.textSecondary,
                          fontSize: 14,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                    title: Text(
                      memberName,
                      style: const TextStyle(
                        fontSize: 14,
                        color: AppTheme.textPrimary,
                      ),
                    ),
                    subtitle: Text(
                      'ID: $memberId',
                      style: const TextStyle(
                        fontSize: 11,
                        color: AppTheme.textMuted,
                      ),
                    ),
                    trailing: isCreator
                        ? Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 8,
                              vertical: 2,
                            ),
                            decoration: BoxDecoration(
                              color: AppTheme.primaryBlueGlow,
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: const Text(
                              'Chủ nhóm',
                              style: TextStyle(
                                fontSize: 10,
                                color: AppTheme.primaryBlue,
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                          )
                        : null,
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}