import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:student_agent/core/theme/app_theme.dart';
import 'package:student_agent/providers/study_group_provider.dart';

class JoinGroupDialog extends ConsumerStatefulWidget {
  final VoidCallback onJoined;

  const JoinGroupDialog({super.key, required this.onJoined});

  @override
  ConsumerState<JoinGroupDialog> createState() => _JoinGroupDialogState();
}

class _JoinGroupDialogState extends ConsumerState<JoinGroupDialog> {
  final _codeController = TextEditingController();
  bool _loading = false;

  @override
  void dispose() {
    _codeController.dispose();
    super.dispose();
  }

  Future<void> _joinGroup() async {
    final code = _codeController.text.trim().toUpperCase();
    if (code.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Vui lòng nhập mã nhóm')),
      );
      return;
    }

    setState(() => _loading = true);

    try {
      await ref.read(joinGroupProvider(code).future);

      if (mounted) {
        Navigator.pop(context);
        widget.onJoined();
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Đã tham gia nhóm thành công!')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Không tìm thấy nhóm. Vui lòng kiểm tra mã.'),
            backgroundColor: AppTheme.danger,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      backgroundColor: AppTheme.surfaceDark,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(20),
        side: const BorderSide(color: AppTheme.cardBorder),
      ),
      title: const Text(
        'Tham gia nhóm',
        style: TextStyle(color: AppTheme.textPrimary),
      ),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Text(
            'Nhập mã nhóm để tham gia',
            style: TextStyle(color: AppTheme.textSecondary),
          ),
          const SizedBox(height: 16),
          TextFormField(
            controller: _codeController,
            style: const TextStyle(
              color: AppTheme.textPrimary,
              fontSize: 16,
              fontWeight: FontWeight.w600,
            ),
            decoration: const InputDecoration(
              labelText: 'Mã nhóm',
              labelStyle: TextStyle(color: AppTheme.textSecondary),
              hintText: 'VD: GRP-ABC123',
              hintStyle: TextStyle(color: AppTheme.textMuted),
              prefixIcon: Icon(Icons.code_rounded, color: AppTheme.textMuted),
            ),
            textCapitalization: TextCapitalization.characters,
          ),
          const SizedBox(height: 8),
          const Text(
            'Mã nhóm có định dạng GRP-XXXXXX',
            style: TextStyle(
              fontSize: 11,
              color: AppTheme.textMuted,
            ),
          ),
        ],
      ),
      actions: [
        TextButton(
          onPressed: _loading ? null : () => Navigator.pop(context),
          child: const Text('Hủy'),
        ),
        ElevatedButton(
          onPressed: _loading ? null : _joinGroup,
          style: ElevatedButton.styleFrom(
            backgroundColor: AppTheme.primaryBlue,
            foregroundColor: Colors.white,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
          ),
          child: _loading
              ? const SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    color: Colors.white,
                  ),
                )
              : const Text('Tham gia'),
        ),
      ],
    );
  }
}