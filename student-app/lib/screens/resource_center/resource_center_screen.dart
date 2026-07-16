import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:student_agent/core/theme/app_theme.dart';
import 'package:student_agent/providers/providers.dart';

class ResourceCenterScreen extends ConsumerWidget {
  const ResourceCenterScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final resourcesAsync = ref.watch(resourcesProvider);

    return Scaffold(
      backgroundColor: AppTheme.backgroundDark,
      appBar: AppBar(
        title: const Text('Resource Center'),
        bottom: const PreferredSize(
          preferredSize: Size.fromHeight(56),
          child: Padding(
            padding: EdgeInsets.fromLTRB(16, 0, 16, 12),
            child: TextField(
              decoration: InputDecoration(
                hintText: 'Tìm kiếm tài liệu...',
                prefixIcon: Icon(Icons.search_rounded,
                    size: 18, color: AppTheme.textMuted),
                isDense: true,
              ),
            ),
          ),
        ),
      ),
      body: resourcesAsync.when(
        loading: () => const Center(
            child: CircularProgressIndicator(color: AppTheme.primaryBlue)),
        error: (e, _) =>
            Center(child: Text('Lỗi: $e', style: const TextStyle(color: AppTheme.danger))),
        data: (resources) => ListView.separated(
          padding: const EdgeInsets.all(16),
          itemCount: resources.length,
          separatorBuilder: (_, __) => const SizedBox(height: 8),
          itemBuilder: (_, i) {
            final r = resources[i];
            final typeIcon = switch (r['type']) {
              'slide' => Icons.slideshow_outlined,
              'video' => Icons.play_circle_outline_rounded,
              'quiz' => Icons.quiz_outlined,
              _ => Icons.description_outlined,
            };
            final typeColor = switch (r['type']) {
              'slide' => AppTheme.primaryBlue,
              'video' => AppTheme.danger,
              'quiz' => AppTheme.warning,
              _ => AppTheme.accentGreen,
            };

            return Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppTheme.surfaceCard,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppTheme.cardBorder, width: 1),
              ),
              child: Row(
                children: [
                  Container(
                    width: 38,
                    height: 38,
                    decoration: BoxDecoration(
                      color: typeColor.withValues(alpha: 0.12),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Icon(typeIcon, size: 18, color: typeColor),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(r['title'],
                            style: const TextStyle(
                                fontSize: 13,
                                fontWeight: FontWeight.w500,
                                color: AppTheme.textPrimary)),
                        Text(r['module'],
                            style: const TextStyle(
                                fontSize: 11,
                                color: AppTheme.textSecondary)),
                      ],
                    ),
                  ),
                  Row(
                    children: [
                      Icon(
                        r['bookmarked']
                            ? Icons.bookmark_rounded
                            : Icons.bookmark_border_rounded,
                        size: 18,
                        color: r['bookmarked']
                            ? AppTheme.primaryBlue
                            : AppTheme.textMuted,
                      ),
                      const SizedBox(width: 8),
                      const Icon(Icons.open_in_new_rounded,
                          size: 16, color: AppTheme.textMuted),
                    ],
                  ),
                ],
              ),
            );
          },
        ),
      ),
    );
  }
}
