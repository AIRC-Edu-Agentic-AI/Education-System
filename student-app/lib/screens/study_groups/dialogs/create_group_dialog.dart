import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:student_agent/core/theme/app_theme.dart';
import 'package:student_agent/providers/study_group_provider.dart';

class CreateGroupDialog extends ConsumerStatefulWidget {
  final VoidCallback onCreated;

  const CreateGroupDialog({super.key, required this.onCreated});

  @override
  ConsumerState<CreateGroupDialog> createState() => _CreateGroupDialogState();
}

class _CreateGroupDialogState extends ConsumerState<CreateGroupDialog> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _descController = TextEditingController();
  bool _loading = false;

  @override
  void dispose() {
    _nameController.dispose();
    _descController.dispose();
    super.dispose();
  }

  // lib/screens/study_groups/dialogs/create_group_dialog.dart
Future<void> _createGroup() async {
  if (!_formKey.currentState!.validate()) return;

  setState(() => _loading = true);

  try {
    // ⭐ THÊM DEBUG
    print('📤 Creating group with name: ${_nameController.text.trim()}');
    
    final result = await ref.read(
      createGroupProvider({
        'name': _nameController.text.trim(),
        'description': _descController.text.trim(),
      }).future,
    );
    
    // ⭐ THÊM DEBUG
    print('✅ Group created: ${result.id} - ${result.name}');
    print('📊 Members: ${result.members}');
    print('📊 Member count: ${result.memberCount}');

    if (mounted) {
      Navigator.pop(context);
      widget.onCreated();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Đã tạo nhóm thành công!')),
      );
    }
  } catch (e) {
    print('❌ Error creating group: $e');
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Lỗi: $e'),
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
        'Tạo nhóm mới',
        style: TextStyle(color: AppTheme.textPrimary),
      ),
      content: Form(
        key: _formKey,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextFormField(
              controller: _nameController,
              style: const TextStyle(color: AppTheme.textPrimary),
              decoration: const InputDecoration(
                labelText: 'Tên nhóm',
                labelStyle: TextStyle(color: AppTheme.textSecondary),
                hintText: 'Nhập tên nhóm học tập',
              ),
              validator: (v) {
                if (v == null || v.trim().isEmpty) {
                  return 'Vui lòng nhập tên nhóm';
                }
                return null;
              },
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: _descController,
              style: const TextStyle(color: AppTheme.textPrimary),
              decoration: const InputDecoration(
                labelText: 'Mô tả (không bắt buộc)',
                labelStyle: TextStyle(color: AppTheme.textSecondary),
                hintText: 'Mô tả về nhóm học tập',
              ),
              maxLines: 3,
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: _loading ? null : () => Navigator.pop(context),
          child: const Text('Hủy'),
        ),
        ElevatedButton(
          onPressed: _loading ? null : _createGroup,
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
              : const Text('Tạo nhóm'),
        ),
      ],
    );
  }
}