import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:file_picker/file_picker.dart';
import 'package:go_router/go_router.dart';
import 'package:student_agent/core/theme/app_theme.dart';
import 'package:student_agent/providers/study_group_provider.dart';
import 'package:student_agent/widgets/chat_bubble.dart';
import 'package:student_agent/screens/study_groups/widgets/file_attachment.dart';

class GroupChatScreen extends ConsumerStatefulWidget {
  final String groupId;

  const GroupChatScreen({super.key, required this.groupId});

  @override
  ConsumerState<GroupChatScreen> createState() => _GroupChatScreenState();
}

class _GroupChatScreenState extends ConsumerState<GroupChatScreen> {
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  
  // ⭐ Thêm state cho file
  File? _selectedFile;
  String? _selectedFileName;
  int? _selectedFileSize;
  bool _isUploading = false;

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    Future.delayed(const Duration(milliseconds: 100), () {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  // ⭐ Thêm hàm chọn file
// ⭐ CÁCH 1: Sử dụng FilePicker.platform (đúng cách)
  Future<void> _selectFile() async {
    try {
      FilePickerResult? result = await FilePicker.platform.pickFiles(
        allowMultiple: false,
        type: FileType.custom,
        allowedExtensions: ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 
                          'jpg', 'jpeg', 'png', 'gif', 'txt', 'zip', 'rar'],
      );

      if (result != null) {
        setState(() {
          _selectedFile = File(result.files.single.path!);
          _selectedFileName = result.files.single.name;
          _selectedFileSize = result.files.single.size;
        });
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Lỗi chọn file: $e'),
            backgroundColor: AppTheme.danger,
          ),
        );
      }
    }
  }

  // ⭐ Thêm hàm gửi tin nhắn với file
// ⭐ Hàm gửi tin nhắn với file
Future<void> _sendMessageWithFile() async {
  final text = _controller.text.trim();
  if (text.isEmpty && _selectedFile == null) return;

  setState(() => _isUploading = true);

  try {
    String? fileUrl;
    String? fileName;
    int? fileSize;
    String? fileType;

    if (_selectedFile != null) {
      // Upload file lên server
      final api = ref.read(studyGroupServiceProvider);
      final studentId = ref.read(activeStudentIdProvider);
      
      final result = await api.uploadFile(
        groupId: widget.groupId,
        studentId: studentId,
        file: _selectedFile!,
        fileName: _selectedFileName!,
      );
      
      fileUrl = result['url']?.toString();
      fileName = result['name']?.toString() ?? _selectedFileName;
      fileSize = result['size'] is int ? result['size'] as int : _selectedFileSize;
      fileType = _selectedFile?.path.split('.').last;
    }

    // ⭐ SỬA: Xác định type đúng
    final msgType = _selectedFile != null ? 'document' : 'text';  // ⭐ Dùng string

    // Gửi tin nhắn
    await ref.read(
      sendGroupMessageProvider({
        'groupId': widget.groupId,
        'content': text.isEmpty ? 'Đã gửi file: $fileName' : text,
        'fileUrl': fileUrl,
        'fileName': fileName,
        'fileSize': fileSize,
        'fileType': fileType,
        'type': msgType,  // ⭐ Gửi 'document' hoặc 'text'
      }).future,
    );

    ref.invalidate(groupMessagesProvider(widget.groupId));
    _controller.clear();
    setState(() {
      _selectedFile = null;
      _selectedFileName = null;
      _selectedFileSize = null;
      _isUploading = false;
    });
    _scrollToBottom();
  } catch (e) {
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Lỗi gửi tin nhắn: $e'),
          backgroundColor: AppTheme.danger,
        ),
      );
    }
    setState(() => _isUploading = false);
  }
}

  @override
  Widget build(BuildContext context) {
    final groupAsync = ref.watch(groupDetailProvider(widget.groupId));
    final messagesAsync = ref.watch(groupMessagesProvider(widget.groupId));
    final studentId = ref.watch(activeStudentIdProvider);

    return Scaffold(
      backgroundColor: AppTheme.backgroundDark,
      appBar: groupAsync.when(
        loading: () => AppBar(
          title: const Text('Loading...'),
          backgroundColor: Colors.transparent,
          leading: IconButton(
            icon: const Icon(Icons.arrow_back_ios_new_rounded,
                size: 18, color: AppTheme.textSecondary),
            onPressed: () => context.pop(),
          ),
        ),
        error: (e, _) => AppBar(
          title: const Text('Lỗi'),
          backgroundColor: Colors.transparent,
          leading: IconButton(
            icon: const Icon(Icons.arrow_back_ios_new_rounded,
                size: 18, color: AppTheme.textSecondary),
            onPressed: () => context.pop(),
          ),
        ),
        data: (group) => AppBar(
          backgroundColor: Colors.transparent,
          leading: IconButton(
            icon: const Icon(Icons.arrow_back_ios_new_rounded,
                size: 18, color: AppTheme.textSecondary),
            onPressed: () => context.pop(),
          ),
          title: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                group.name,
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                  color: AppTheme.textPrimary,
                ),
              ),
              Text(
                '${group.totalMembers} thành viên',
                style: const TextStyle(
                  fontSize: 11,
                  color: AppTheme.textSecondary,
                ),
              ),
            ],
          ),
          actions: [
            IconButton(
              icon: const Icon(Icons.attach_file_rounded,
                  color: AppTheme.textSecondary),
              onPressed: _selectFile,
              tooltip: 'Đính kèm file',
            ),
            IconButton(
              icon: const Icon(Icons.info_outline_rounded,
                  color: AppTheme.textSecondary),
              onPressed: () {
                context.push('/study-group-detail/${widget.groupId}');
              },
            ),
          ],
        ),
      ),
      body: Column(
        children: [
          Expanded(
            child: messagesAsync.when(
              loading: () => const Center(
                child: CircularProgressIndicator(color: AppTheme.primaryBlue),
              ),
              error: (e, _) => Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.error_outline_rounded,
                        size: 48, color: AppTheme.danger),
                    const SizedBox(height: 12),
                    const Text(
                      'Lỗi tải tin nhắn',
                      style: TextStyle(color: AppTheme.textSecondary),
                    ),
                    const SizedBox(height: 8),
                    ElevatedButton(
                      onPressed: () {
                        ref.invalidate(groupMessagesProvider(widget.groupId));
                      },
                      child: const Text('Thử lại'),
                    ),
                  ],
                ),
              ),
              data: (messages) {
                if (messages.isEmpty) {
                  return const Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.chat_bubble_outline_rounded,
                            size: 48, color: AppTheme.textMuted),
                        SizedBox(height: 12),
                        Text(
                          'Chưa có tin nhắn',
                          style: TextStyle(
                            color: AppTheme.textSecondary,
                            fontSize: 14,
                          ),
                        ),
                        Text(
                          'Hãy bắt đầu cuộc trò chuyện nào!',
                          style: TextStyle(
                            color: AppTheme.textMuted,
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ),
                  );
                }

                return ListView.builder(
                  controller: _scrollController,
                  padding: const EdgeInsets.all(16),
                  reverse: false,
                  itemCount: messages.length,
                  itemBuilder: (_, i) {
                    final msg = messages[i];
                    final isSender = msg.senderId == studentId.toString();
                    
                    // ⭐ Tạo nội dung hiển thị có file
                    String displayContent = msg.content;
                    if (msg.fileName != null) {
                      displayContent = '📎 ${msg.fileName}\n$displayContent';
                    }
                    
                    return ChatBubble(
                      senderName: msg.senderName,
                      message: displayContent,
                      isSender: isSender,
                      imageUrl: msg.fileUrl,
                    );
                  },
                );
              },
            ),
          ),
          // ⭐ Hiển thị file attachment nếu có
          if (_selectedFile != null)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
              child: FileAttachment(
                file: _selectedFile,
                fileName: _selectedFileName,
                fileSize: _selectedFileSize,
                onRemove: () {
                  setState(() {
                    _selectedFile = null;
                    _selectedFileName = null;
                    _selectedFileSize = null;
                  });
                },
                onSelectFile: _selectFile,
              ),
            ),
          _ChatInput(
            controller: _controller,
            onSend: _sendMessageWithFile,
            isLoading: _isUploading,
            onAttachFile: _selectFile,
          ),
        ],
      ),
    );
  }
}

// ── Chat Input Widget (cập nhật) ──
class _ChatInput extends StatelessWidget {
  final TextEditingController controller;
  final VoidCallback onSend;
  final bool isLoading;
  final VoidCallback onAttachFile;

  const _ChatInput({
    required this.controller,
    required this.onSend,
    required this.isLoading,
    required this.onAttachFile,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(12, 8, 12, 16),
      decoration: const BoxDecoration(
        color: AppTheme.navBar,
        border: Border(top: BorderSide(color: AppTheme.divider, width: 1)),
      ),
      child: Row(
        children: [
          // ⭐ Nút đính kèm file
          IconButton(
            icon: const Icon(Icons.attach_file_rounded,
                color: AppTheme.textSecondary, size: 24),
            onPressed: isLoading ? null : onAttachFile,
            tooltip: 'Đính kèm file',
          ),
          Expanded(
            child: TextField(
              controller: controller,
              decoration: const InputDecoration(
                hintText: 'Nhập tin nhắn...',
                hintStyle: TextStyle(color: AppTheme.textMuted),
                border: InputBorder.none,
              ),
              style: const TextStyle(
                fontSize: 14,
                color: AppTheme.textPrimary,
              ),
              onSubmitted: (_) => onSend(),
              textInputAction: TextInputAction.send,
              maxLines: 3,
              minLines: 1,
            ),
          ),
          const SizedBox(width: 8),
          GestureDetector(
            onTap: isLoading ? null : onSend,
            child: Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                gradient: isLoading ? null : AppTheme.blueGreenGradient,
                color: isLoading ? AppTheme.textMuted : null,
                shape: BoxShape.circle,
              ),
              child: isLoading
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: Colors.white,
                      ),
                    )
                  : const Icon(
                      Icons.send_rounded,
                      color: Colors.white,
                      size: 18,
                    ),
            ),
          ),
        ],
      ),
    );
  }
}