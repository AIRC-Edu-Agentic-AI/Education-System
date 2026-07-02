import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import 'package:student_agent/core/theme/app_theme.dart';
import 'package:student_agent/data/mock/mock_message_store.dart';
import 'package:student_agent/models/course_model.dart';
import 'package:student_agent/providers/providers.dart';

import 'dart:async';
import 'package:student_agent/core/config/env_config.dart';

class CourseChannelMessagesScreen extends ConsumerStatefulWidget {
  final String courseCode;
  final String channelId;
  final String? channelName;
  final String? channelType;
  final String? returnTo;

  const CourseChannelMessagesScreen({
    super.key,
    required this.courseCode,
    required this.channelId,
    this.channelName,
    this.channelType,
    this.returnTo,
  });

  @override
  ConsumerState<CourseChannelMessagesScreen> createState() =>
      _CourseChannelMessagesScreenState();
}

class _CourseChannelMessagesScreenState
extends ConsumerState<CourseChannelMessagesScreen> {
  final _controller = TextEditingController();
  final _scrollController = ScrollController();
  final _expandedThreads = <String>{};
  String? _replyToMessageId;
  bool _sending = false;
  Timer? _messageRefreshTimer;

  @override
  void dispose() {
    _messageRefreshTimer?.cancel();
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  @override
  void initState() {
    super.initState();
    _startMessagePolling();
  }

  void _startMessagePolling() {
    final seconds = EnvConfig.pollingIntervalSeconds < 3
      ? 3
      : EnvConfig.pollingIntervalSeconds;

    _messageRefreshTimer = Timer.periodic(
      Duration(seconds: seconds),
      (_) {
        if (!mounted) return;
    
        ref.invalidate(
          channelThreadMessagesProvider(
            ChannelMessagesArgs(channelId: widget.channelId),
          ),
        );

        for (final parentId in _expandedThreads) {
          ref.invalidate(
            channelThreadMessagesProvider(
              ChannelMessagesArgs(
                channelId: widget.channelId,
                parentId: parentId,
              ),
            ),
          );
        }
      },
    );
  }

  bool get _isAnnouncement =>
    widget.channelType == 'announcement' ||
    widget.channelId.contains('announcement') ||
    (widget.channelName?.toLowerCase().contains('thông báo') ?? false);

  bool get _canPostRoot {
    if (!_isAnnouncement) return true;
    // Mock: student chỉ reply announcement, không tạo tin gốc mới
    return false;
  }

  Future<void> _send() async {
    final text = _controller.text.trim();
    if (text.isEmpty || _sending) return;

    if (!_canPostRoot && _replyToMessageId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Kênh thông báo: chỉ được trả lời trong thread.'),
        ),
      );
      return;
    }

    setState(() => _sending = true);
    final api = ref.read(apiServiceProvider);
    final studentId = ref.read(activeStudentIdProvider);

    final message = await api.postChannelMessage(
      channelId: widget.channelId,
      senderId: studentId,
      content: text,
      parentId: _replyToMessageId,
    );

    if (message == null) {
      if (!mounted) return;
      setState(() => _sending = false);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Không gửi được tin nhắn. Vui lòng kiểm tra kết nối backend.'),
        ),
      );
      return;
    }

    _controller.clear();
    setState(() {
      _sending = false;
      if (_replyToMessageId != null) {
        _expandedThreads.add(_replyToMessageId!);
      }
    });

    ref.invalidate(
      channelThreadMessagesProvider(
        ChannelMessagesArgs(channelId: widget.channelId),
      ),
    );
    
    _scrollToBottom();

    if (_replyToMessageId != null) {
      ref.invalidate(
        channelThreadMessagesProvider(
          ChannelMessagesArgs(
            channelId: widget.channelId,
            parentId: _replyToMessageId,
          ),
        ),
      );
    }
  }

  String _senderLabel(CourseMessage msg) {
    if (msg.senderId == ref.read(activeStudentIdProvider)) return 'Bạn';
    switch (msg.senderRole) {
      case 'instructor':
        return 'Giảng viên';
      case 'class_rep':
        return 'Lớp trưởng';
      default:
        return 'SV ${msg.senderId}';
    }
  }

  @override
  Widget build(BuildContext context) {
    ref.listen(
      channelThreadMessagesProvider(
        ChannelMessagesArgs(channelId: widget.channelId),
      ),
      (_, next) {
        next.whenData((_) {
          _scrollToBottom();
        });
      },
    );

    final rootsAsync = ref.watch(
      channelThreadMessagesProvider(
        ChannelMessagesArgs(channelId: widget.channelId),
      ),
    );

    return Scaffold(
      backgroundColor: AppTheme.backgroundDark,
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded, size: 18),
          onPressed: () {
            if (widget.returnTo != null && widget.returnTo!.isNotEmpty) {
              context.go(widget.returnTo!);
              return;
            }
            context.pop();
          },
        ),
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              widget.channelName ?? widget.channelId,
              style: const TextStyle(fontSize: 16),
            ),
            Text(
              widget.courseCode,
              style: const TextStyle(
                fontSize: 12,
                color: AppTheme.textSecondary,
              ),
            ),
          ],
        ),
      ),
      body: Column(
        children: [
          Expanded(
            child: rootsAsync.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (e, _) => Center(child: Text('Lỗi: $e')),
              data: (roots) {
                if (roots.isEmpty) {
                  return const Center(
                    child: Text(
                      'Chưa có tin nhắn',
                      style: TextStyle(color: AppTheme.textSecondary),
                    ),
                  );
                }
                return ListView.builder(
                  controller: _scrollController,
                  padding: const EdgeInsets.all(16),
                  itemCount: roots.length,
                  itemBuilder: (context, index) {
                    final msg = roots[index];
                    return _MessageThread(
                      message: msg,
                      channelId: widget.channelId,
                      expanded: _expandedThreads.contains(msg.id),
                      replyToId: _replyToMessageId,
                      senderLabel: _senderLabel(msg),
                      onToggleThread: () {
                        setState(() {
                          if (_expandedThreads.contains(msg.id)) {
                            _expandedThreads.remove(msg.id);
                          } else {
                            _expandedThreads.add(msg.id);
                          }
                        });
                      },
                      onReply: () {
                        setState(() => _replyToMessageId = msg.id);
                      },
                    );
                  },
                );
              },
            ),
          ),
          if (_replyToMessageId != null)
            Container(
              width: double.infinity,
              color: AppTheme.surfaceDark,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Row(
                children: [
                  const Icon(Icons.reply, size: 16, color: AppTheme.primaryBlue),
                  const SizedBox(width: 8),
                  const Expanded(
                    child: Text(
                      'Đang trả lời thread',
                      style: TextStyle(color: AppTheme.textSecondary),
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close, size: 18),
                    onPressed: () => setState(() => _replyToMessageId = null),
                  ),
                ],
              ),
            ),
          _MessageInputBar(
            controller: _controller,
            sending: _sending,
            enabled: _canPostRoot || _replyToMessageId != null,
            hint: _canPostRoot
                ? 'Nhập tin nhắn...'
                : 'Trả lời thông báo...',
            onSend: _send,
          ),
        ],
      ),
    );
  }

  void _scrollToBottom({bool animated = true}) {
    if (!_scrollController.hasClients) return;

    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!_scrollController.hasClients) return;

      final offset = _scrollController.position.maxScrollExtent;

      if (animated) {
        _scrollController.animateTo(
          offset,
          duration: const Duration(milliseconds: 250),
          curve: Curves.easeOut,
        );
      } else {
        _scrollController.jumpTo(offset);
      }
    });
  }
}

class _MessageThread extends ConsumerWidget {
  final CourseMessage message;
  final String channelId;
  final bool expanded;
  final String? replyToId;
  final String senderLabel;
  final VoidCallback onToggleThread;
  final VoidCallback onReply;

  const _MessageThread({
    required this.message,
    required this.channelId,
    required this.expanded,
    required this.replyToId,
    required this.senderLabel,
    required this.onToggleThread,
    required this.onReply,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final replyCount = MockMessageStore.replyCount(channelId, message.id);

    final repliesAsync = expanded
        ? ref.watch(
            channelThreadMessagesProvider(
              ChannelMessagesArgs(
                channelId: channelId,
                parentId: message.id,
              ),
            ),
          )
        : null;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _MessageBubble(
          message: message,
          senderLabel: senderLabel,
          highlighted: replyToId == message.id,
        ),
        Padding(
          padding: const EdgeInsets.only(left: 8, bottom: 12),
          child: Row(
            children: [
              if (replyCount > 0)
                TextButton(
                  onPressed: onToggleThread,
                  child: Text(
                    expanded
                        ? 'Ẩn $replyCount phản hồi'
                        : '$replyCount phản hồi',
                  ),
                ),
              TextButton(
                onPressed: onReply,
                child: const Text('Trả lời'),
              ),
            ],
          ),
        ),
        if (expanded && repliesAsync != null)
          repliesAsync.when(
            loading: () => const Padding(
              padding: EdgeInsets.only(left: 24, bottom: 12),
              child: CircularProgressIndicator(strokeWidth: 2),
            ),
            error: (e, _) => Text('Lỗi thread: $e'),
            data: (replies) => Column(
              children: replies
                  .map(
                    (r) => Padding(
                      padding: const EdgeInsets.only(left: 24, bottom: 8),
                      child: _MessageBubble(
                        message: r,
                        senderLabel: r.senderId == 28400 ? 'Bạn' : 'SV ${r.senderId}',
                      ),
                    ),
                  )
                  .toList(),
            ),
          ),
      ],
    );
  }
}

class _MessageBubble extends StatelessWidget {
  final CourseMessage message;
  final String senderLabel;
  final bool highlighted;

  const _MessageBubble({
    required this.message,
    required this.senderLabel,
    this.highlighted = false,
  });

  @override
  Widget build(BuildContext context) {
    final time = DateFormat('dd/MM HH:mm').format(message.createdAt);

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: highlighted
            ? AppTheme.primaryBlueGlow
            : AppTheme.surfaceCard,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: highlighted ? AppTheme.primaryBlue : AppTheme.cardBorder,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(
                senderLabel,
                style: const TextStyle(
                  fontWeight: FontWeight.w600,
                  color: AppTheme.textPrimary,
                ),
              ),
              const SizedBox(width: 8),
              Text(
                time,
                style: const TextStyle(
                  fontSize: 11,
                  color: AppTheme.textSecondary,
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            message.content,
            style: const TextStyle(color: AppTheme.textPrimary),
          ),
        ],
      ),
    );
  }
}

class _MessageInputBar extends StatelessWidget {
  final TextEditingController controller;
  final bool sending;
  final bool enabled;
  final String hint;
  final VoidCallback onSend;

  const _MessageInputBar({
    required this.controller,
    required this.sending,
    required this.enabled,
    required this.hint,
    required this.onSend,
  });

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(12, 8, 12, 12),
        child: Row(
          children: [
            Expanded(
              child: TextField(
                controller: controller,
                enabled: enabled && !sending,
                decoration: InputDecoration(
                  hintText: hint,
                  filled: true,
                  fillColor: AppTheme.surfaceDark,
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(24),
                    borderSide: const BorderSide(color: AppTheme.cardBorder),
                  ),
                ),
                onSubmitted: (_) => onSend(),
              ),
            ),
            const SizedBox(width: 8),
            IconButton.filled(
              onPressed: enabled && !sending ? onSend : null,
              icon: sending
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.send_rounded),
            ),
          ],
        ),
      ),
    );
  }
}
