import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:student_agent/core/theme/app_theme.dart';
import 'package:student_agent/providers/providers.dart';
import 'package:student_agent/widgets/glass_card.dart';

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final studentAsync = ref.watch(studentProvider);
    final ktAsync = ref.watch(knowledgeStateProvider);

    return Scaffold(
      backgroundColor: AppTheme.backgroundDark,
      appBar: AppBar(
        title: const Text('Profile'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded,
              size: 18, color: AppTheme.textSecondary),
          onPressed: () =>
              context.canPop() ? context.pop() : context.go('/'),
        ),
      ),
      body: studentAsync.when(
        loading: () => const Center(
            child: CircularProgressIndicator(color: AppTheme.primaryBlue)),
        error: (e, _) =>
            Center(child: Text('Lỗi: $e', style: const TextStyle(color: AppTheme.danger))),
        data: (student) => ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // Avatar + name
            Center(
              child: Column(
                children: [
                  Container(
                    width: 80,
                    height: 80,
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
                            fontSize: 28,
                            fontWeight: FontWeight.w600),
                      ),
                    ),
                  ),
                  const SizedBox(height: 12),
                  Text(student.fullName,
                      style: const TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.w600,
                          color: AppTheme.textPrimary)),
                  Text('MSV ${student.studentId}',
                      style: const TextStyle(
                          fontSize: 13, color: AppTheme.textSecondary)),
                ],
              ),
            ),
            const SizedBox(height: 24),

            _Section(
              title: 'Thông tin cá nhân',
              children: [
                _InfoRow(
                    label: 'Giới tính',
                    value: student.demographics.gender == 'M' ? 'Nam' : 'Nữ'),
                _InfoRow(
                    label: 'Độ tuổi', value: student.demographics.ageBand),
                _InfoRow(
                    label: 'Khu vực', value: student.demographics.region),
                _InfoRow(
                    label: 'Trình độ',
                    value: student.demographics.highestEducation),
                _InfoRow(
                    label: 'Số lần thử trước',
                    value: '${student.demographics.numPrevAttempts}'),
              ],
            ),
            const SizedBox(height: 14),

            const _Section(
              title: 'Tùy chỉnh học tập',
              children: [
                _ToggleRow(label: 'Nhắc nhở hàng ngày', value: true),
                _ToggleRow(label: 'Thông báo từ giảng viên', value: true),
                _ToggleRow(label: 'Chế độ tập trung', value: false),
              ],
            ),
            const SizedBox(height: 14),

            _Section(
              title: 'Cài đặt',
              children: [
                const _InfoRow(label: 'Ngôn ngữ', value: 'Tiếng Việt'),
                _InfoRow(
                    label: 'Tài khoản',
                    value: 'Auth0 · ${student.auth0Id.substring(0, 14)}...'),
              ],
            ),
            const SizedBox(height: 14),

            // ── Knowledge mastery ───────────────────────────────────
            ktAsync.when(
              loading: () => const SizedBox.shrink(),
              error: (_, __) => const SizedBox.shrink(),
              data: (kt) => _MasterySection(states: kt),
            ),
          ],
        ),
      ),
    );
  }
}

class _Section extends StatelessWidget {
  final String title;
  final List<Widget> children;
  const _Section({required this.title, required this.children});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(title,
            style: const TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w500,
                color: AppTheme.textSecondary,
                letterSpacing: 0.5)),
        const SizedBox(height: 8),
        Container(
          decoration: BoxDecoration(
            color: AppTheme.surfaceCard,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: AppTheme.cardBorder, width: 1),
          ),
          child: Column(children: children),
        ),
      ],
    );
  }
}

class _InfoRow extends StatelessWidget {
  final String label;
  final String value;
  const _InfoRow({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 11),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label,
              style: const TextStyle(
                  fontSize: 13, color: AppTheme.textSecondary)),
          Text(value,
              style: const TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w500,
                  color: AppTheme.textPrimary)),
        ],
      ),
    );
  }
}

class _ToggleRow extends StatefulWidget {
  final String label;
  final bool value;
  const _ToggleRow({required this.label, required this.value});

  @override
  State<_ToggleRow> createState() => _ToggleRowState();
}

class _ToggleRowState extends State<_ToggleRow> {
  late bool _value;

  @override
  void initState() {
    super.initState();
    _value = widget.value;
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(widget.label,
              style: const TextStyle(
                  fontSize: 13, color: AppTheme.textPrimary)),
          Switch.adaptive(
            value: _value,
            onChanged: (v) => setState(() => _value = v),
            activeThumbColor: Colors.white,
            activeTrackColor: AppTheme.primaryBlue,
          ),
        ],
      ),
    );
  }
}

// ── Knowledge mastery section ─────────────────────────────────────────────────

class _MasterySection extends StatelessWidget {
  final Map<String, dynamic> states;
  const _MasterySection({required this.states});

  Color _barColor(double mastery) {
    if (mastery >= 0.7) return AppTheme.accentGreen;
    if (mastery >= 0.5) return AppTheme.warning;
    return AppTheme.danger;
  }

  @override
  Widget build(BuildContext context) {
    if (states.isEmpty) return const SizedBox.shrink();
    final entries = states.entries.toList()
      ..sort((a, b) {
        final ma = (a.value['mastery'] as num?)?.toDouble() ?? 0.0;
        final mb = (b.value['mastery'] as num?)?.toDouble() ?? 0.0;
        return ma.compareTo(mb);
      });

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'NĂNG LỰC HỌC TẬP',
          style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w500,
              color: AppTheme.textSecondary,
              letterSpacing: 0.5),
        ),
        const SizedBox(height: 8),
        GlassCard(
          padding: const EdgeInsets.all(14),
          child: Column(
            children: entries.map((e) {
              final mastery =
                  (e.value['mastery'] as num?)?.toDouble() ?? 0.0;
              final pct = (mastery * 100).round();
              return Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Expanded(
                          child: Text(e.key,
                              style: const TextStyle(
                                  fontSize: 13,
                                  color: AppTheme.textPrimary)),
                        ),
                        Text('$pct%',
                            style: TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.w600,
                                color: _barColor(mastery))),
                      ],
                    ),
                    const SizedBox(height: 6),
                    ClipRRect(
                      borderRadius: BorderRadius.circular(4),
                      child: LinearProgressIndicator(
                        value: mastery,
                        minHeight: 6,
                        backgroundColor: AppTheme.surfaceDark,
                        valueColor:
                            AlwaysStoppedAnimation(_barColor(mastery)),
                      ),
                    ),
                  ],
                ),
              );
            }).toList(),
          ),
        ),
      ],
    );
  }
}
