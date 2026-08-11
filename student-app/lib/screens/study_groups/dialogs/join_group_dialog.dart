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
        const SnackBar(content: Text('Please enter group code')),
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
          const SnackBar(content: Text('Joined group successfully!')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Group not found. Please check the code.'),
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
        'Join Group',
        style: TextStyle(color: AppTheme.textPrimary),
      ),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Text(
            'Enter group code to join',
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
              labelText: 'Group Code',
              labelStyle: TextStyle(color: AppTheme.textSecondary),
              hintText: 'e.g. GRP-ABC123',
              hintStyle: TextStyle(color: AppTheme.textMuted),
              prefixIcon: Icon(Icons.code_rounded, color: AppTheme.textMuted),
            ),
            textCapitalization: TextCapitalization.characters,
          ),
          const SizedBox(height: 8),
          const Text(
            'Group code format: GRP-XXXXXX',
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
          child: const Text('Cancel'),
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
              : const Text('Join Group'),
        ),
      ],
    );
  }
}