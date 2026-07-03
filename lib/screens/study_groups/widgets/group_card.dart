// lib/screens/study_groups/widgets/group_card.dart
import 'package:flutter/material.dart';
import 'package:student_agent/core/theme/app_theme.dart';
import 'package:student_agent/models/study_group_model.dart';

class GroupCard extends StatelessWidget {
  final StudyGroup group;
  final VoidCallback onTap;
  final VoidCallback onLeave;

  const GroupCard({
    super.key,
    required this.group,
    required this.onTap,
    required this.onLeave,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: AppTheme.surfaceCard,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: AppTheme.cardBorder, width: 1),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 44,
                  height: 44,
                  decoration: BoxDecoration(
                    gradient: AppTheme.blueGreenGradient,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Center(
                    child: Text(
                      group.name.isNotEmpty ? group.name[0].toUpperCase() : 'G',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 18,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        group.name,
                        style: const TextStyle(
                          fontSize: 15,
                          fontWeight: FontWeight.w600,
                          color: AppTheme.textPrimary,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      const SizedBox(height: 2),
                      Row(
                        children: [
                          const Icon(
                            Icons.group_outlined,
                            size: 14,
                            color: AppTheme.textSecondary,
                          ),
                          const SizedBox(width: 4),
                          Text(
                            '${group.totalMembers ?? 0} thành viên',  // ⭐ Thêm ?? 0
                                style: const TextStyle(
                                  fontSize: 12,
                                  color: AppTheme.textSecondary,
                            ),
                          ),
                          const SizedBox(width: 12),
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 8,
                              vertical: 2,
                            ),
                            decoration: BoxDecoration(
                              color: AppTheme.primaryBlueGlow,
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Text(
                              'Mã: ${group.groupCode}',
                              style: const TextStyle(
                                fontSize: 10,
                                color: AppTheme.primaryBlue,
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                IconButton(
                  icon: const Icon(
                    Icons.more_vert_rounded,
                    color: AppTheme.textMuted,
                    size: 20,
                  ),
                  onPressed: () {
                    showModalBottomSheet(
                      context: context,
                      backgroundColor: AppTheme.surfaceDark,
                      shape: const RoundedRectangleBorder(
                        borderRadius: BorderRadius.vertical(
                          top: Radius.circular(20),
                        ),
                      ),
                      builder: (_) => SafeArea(
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Container(
                              margin: const EdgeInsets.only(top: 12),
                              width: 36,
                              height: 4,
                              decoration: BoxDecoration(
                                color: AppTheme.textMuted,
                                borderRadius: BorderRadius.circular(2),
                              ),
                            ),
                            ListTile(
                              leading: const Icon(
                                Icons.exit_to_app_rounded,
                                color: AppTheme.danger,
                              ),
                              title: const Text(
                                'Rời nhóm',
                                style: TextStyle(color: AppTheme.danger),
                              ),
                              onTap: () {
                                Navigator.pop(context);
                                onLeave();
                              },
                            ),
                            const SizedBox(height: 8),
                          ],
                        ),
                      ),
                    );
                  },
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              group.description.isNotEmpty
                  ? group.description
                  : 'Nhóm học tập ${group.name}',
              style: const TextStyle(
                fontSize: 13,
                color: AppTheme.textSecondary,
              ),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
          ],
        ),
      ),
    );
  }
}