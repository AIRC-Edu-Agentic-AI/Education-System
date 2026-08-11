import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:student_agent/core/theme/app_theme.dart';
import 'package:student_agent/models/course_model.dart';
import 'package:student_agent/providers/providers.dart';
import 'package:student_agent/widgets/formatted_text.dart';

class InstructorInfo {
  final String id;
  final String name;
  final String title;
  final String avatarUrl;

  const InstructorInfo({
    required this.id,
    required this.name,
    required this.title,
    this.avatarUrl = '',
  });
}

class FloatingChatButton extends ConsumerStatefulWidget {
  final Size bodySize;

  const FloatingChatButton({super.key, required this.bodySize});

  @override
  ConsumerState<FloatingChatButton> createState() => _FloatingChatButtonState();
}

class _FloatingChatButtonState extends ConsumerState<FloatingChatButton> {
  static const double _size = 58;
  Offset? _pos;
  bool _isExpanded = false;
  int _activeTab = 0; // 0 = Nhắn tin (Giảng viên), 1 = Hỏi AI Assistant
  
  // Selected instructor for chat thread view (null = show instructor list)
  InstructorInfo? _selectedInstructor;
  
  int _unreadCount = 0;
  CourseMessage? _lastMessage;
  String? _privateChannelId;
  StreamSubscription? _msgSub;
  final TextEditingController _textController = TextEditingController();
  final ScrollController _aiScrollController = ScrollController();
  final ScrollController _msgScrollController = ScrollController();
  bool _isSending = false;

  // List of instructors (form structured so adding new instructors is effortless)
  final List<InstructorInfo> _instructors = const [
    InstructorInfo(
      id: 'teacher_admin',
      name: 'Course Instructor',
      title: 'Instructor for AAA 2013J',
    ),
  ];

  Timer? _pollTimer;

  @override
  void initState() {
    super.initState();
    _loadPrivateChannel();
    _msgSub = newMessageStreamController.stream.listen((msg) {
      if (!mounted) return;
      final isPrivate = (msg.channelType == 'private_message') ||
          (msg.channelId == _privateChannelId) ||
          (msg.senderRole == 'instructor' && msg.courseCode.isEmpty);
      if (isPrivate || msg.channelId == _privateChannelId) {
        setState(() {
          _unreadCount++;
          _lastMessage = msg;
          if (msg.channelId.isNotEmpty) {
            _privateChannelId = msg.channelId;
          }
        });
      }
      ref.invalidate(channelThreadMessagesProvider(ChannelMessagesArgs(channelId: msg.channelId)));
      if (_privateChannelId != null) {
        ref.invalidate(channelThreadMessagesProvider(ChannelMessagesArgs(channelId: _privateChannelId!)));
      }
    });

    _pollTimer = Timer.periodic(const Duration(seconds: 4), (_) {
      if (!mounted) return;
      if (_privateChannelId != null) {
        ref.invalidate(channelThreadMessagesProvider(ChannelMessagesArgs(channelId: _privateChannelId!)));
      }
      final studentId = ref.read(activeStudentIdProvider);
      ref.invalidate(channelThreadMessagesProvider(ChannelMessagesArgs(channelId: 'private_$studentId')));
    });
  }

  Future<void> _loadPrivateChannel() async {
    try {
      final studentId = ref.read(activeStudentIdProvider);
      final api = ref.read(apiServiceProvider);
      final channel = await api.getPrivateChannel(studentId);
      if (mounted) {
        setState(() {
          _privateChannelId = channel.id;
        });
      }
    } catch (_) {}
  }

  @override
  void dispose() {
    _pollTimer?.cancel();
    _msgSub?.cancel();
    _textController.dispose();
    _aiScrollController.dispose();
    _msgScrollController.dispose();
    super.dispose();
  }

  void _onPanUpdate(DragUpdateDetails d) {
    final size = widget.bodySize;
    _pos ??= Offset(size.width - _size - 16, size.height - _size - 80);
    setState(() {
      _pos = Offset(
        (_pos!.dx + d.delta.dx).clamp(0.0, size.width - _size),
        (_pos!.dy + d.delta.dy).clamp(0.0, size.height - _size - 60),
      );
    });
  }

  void _scrollToAiBottom() {
    if (_aiScrollController.hasClients) {
      _aiScrollController.animateTo(
        _aiScrollController.position.maxScrollExtent,
        duration: const Duration(milliseconds: 250),
        curve: Curves.easeOut,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_privateChannelId == null) {
      _loadPrivateChannel();
    }

    final size = widget.bodySize;
    final defaultPos = Offset(size.width - _size - 16, size.height - _size - 80);
    final currentPos = _pos ?? defaultPos;

    return Stack(
      clipBehavior: Clip.none,
      children: [
        // ── 1. EXPANDED MINI CHAT WINDOW ────────────────────────────────────
        if (_isExpanded)
          Positioned(
            right: 16,
            bottom: 80,
            width: (size.width - 32).clamp(280.0, 380.0),
            height: 440,
            child: Material(
              color: Colors.transparent,
              child: Container(
                decoration: BoxDecoration(
                  color: const Color(0xFF0F172A),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(
                    color: const Color(0xFF38BDF8).withValues(alpha: 0.6),
                    width: 1.5,
                  ),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withValues(alpha: 0.6),
                      blurRadius: 24,
                      offset: const Offset(0, 10),
                    ),
                  ],
                ),
                child: Column(
                  children: [
                    // Header Segmented 2 Tabs Bar (Nhắn tin / Hỏi AI)
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                      decoration: const BoxDecoration(
                        color: Color(0xFF1E293B),
                        borderRadius: BorderRadius.vertical(top: Radius.circular(18)),
                      ),
                      child: Row(
                        children: [
                          if (_activeTab == 0 && _selectedInstructor != null)
                            IconButton(
                              icon: const Icon(Icons.arrow_back_ios_new_rounded, size: 16, color: Colors.white),
                              onPressed: () => setState(() => _selectedInstructor = null),
                              tooltip: 'Instructor list',
                            ),
                          Expanded(
                            child: Container(
                              height: 34,
                              padding: const EdgeInsets.all(2),
                              decoration: BoxDecoration(
                                color: const Color(0xFF0F172A),
                                borderRadius: BorderRadius.circular(10),
                              ),
                              child: Row(
                                children: [
                                  Expanded(
                                    child: GestureDetector(
                                      onTap: () => setState(() {
                                        _activeTab = 0;
                                      }),
                                      child: Container(
                                        decoration: BoxDecoration(
                                          color: _activeTab == 0 ? const Color(0xFF0EA5E9) : Colors.transparent,
                                          borderRadius: BorderRadius.circular(8),
                                        ),
                                        child: const Row(
                                          mainAxisAlignment: MainAxisAlignment.center,
                                          mainAxisSize: MainAxisSize.min,
                                          children: [
                                            Icon(Icons.chat_bubble_outline_rounded, size: 14, color: Colors.white),
                                            SizedBox(width: 4),
                                            Text(
                                              'Messages',
                                              style: TextStyle(
                                                fontSize: 11,
                                                fontWeight: FontWeight.bold,
                                                color: Colors.white,
                                              ),
                                            ),
                                          ],
                                        ),
                                      ),
                                    ),
                                  ),
                                  Expanded(
                                    child: GestureDetector(
                                      onTap: () => setState(() => _activeTab = 1),
                                      child: Container(
                                        decoration: BoxDecoration(
                                          color: _activeTab == 1 ? const Color(0xFF10B981) : Colors.transparent,
                                          borderRadius: BorderRadius.circular(8),
                                        ),
                                        child: const Row(
                                          mainAxisAlignment: MainAxisAlignment.center,
                                          mainAxisSize: MainAxisSize.min,
                                          children: [
                                            Icon(Icons.auto_awesome_rounded, size: 14, color: Colors.white),
                                            SizedBox(width: 4),
                                            Text(
                                              'Ask AI',
                                              style: TextStyle(
                                                fontSize: 11,
                                                fontWeight: FontWeight.bold,
                                                color: Colors.white,
                                              ),
                                            ),
                                          ],
                                        ),
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                          if (_activeTab == 1)
                            IconButton(
                              icon: const Icon(Icons.open_in_new_rounded, color: Color(0xFF94A3B8), size: 18),
                              tooltip: 'Open AI Fullscreen',
                              onPressed: () {
                                setState(() => _isExpanded = false);
                                context.push('/chat');
                              },
                            ),
                          IconButton(
                            icon: const Icon(Icons.remove_rounded, color: Color(0xFF94A3B8), size: 20),
                            onPressed: () => setState(() => _isExpanded = false),
                          ),
                        ],
                      ),
                    ),

                    // Body List Area
                    Expanded(
                      child: _activeTab == 0
                          ? (_selectedInstructor == null ? _buildInstructorList() : _buildInstructorMessageThread())
                          : _buildAiChatList(),
                    ),

                    // Input Bar (only shown when in Chat Thread or AI Tab)
                    if (_activeTab == 1 || (_activeTab == 0 && _selectedInstructor != null))
                      Container(
                        padding: const EdgeInsets.all(10),
                        decoration: const BoxDecoration(
                          color: Color(0xFF1E293B),
                          borderRadius: BorderRadius.vertical(bottom: Radius.circular(18)),
                        ),
                        child: Row(
                          children: [
                            Expanded(
                              child: Container(
                                height: 38,
                                padding: const EdgeInsets.symmetric(horizontal: 12),
                                decoration: BoxDecoration(
                                  color: const Color(0xFF0F172A),
                                  borderRadius: BorderRadius.circular(10),
                                  border: Border.all(color: const Color(0xFF334155)),
                                ),
                                child: TextField(
                                  controller: _textController,
                                  style: const TextStyle(fontSize: 12, color: Colors.white),
                                  onSubmitted: (_) => _handleSend(),
                                  decoration: InputDecoration(
                                    hintText: _activeTab == 0
                                        ? 'Message ${_selectedInstructor?.name ?? "Instructor"}...'
                                        : 'Ask AI Learning Assistant...',
                                    hintStyle: const TextStyle(fontSize: 12, color: Color(0xFF64748B)),
                                    border: InputBorder.none,
                                    isDense: true,
                                    contentPadding: const EdgeInsets.symmetric(vertical: 10),
                                  ),
                                ),
                              ),
                            ),
                            const SizedBox(width: 8),
                            _isSending
                                ? const SizedBox(
                                    width: 24,
                                    height: 24,
                                    child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFF38BDF8)),
                                  )
                                : Container(
                                    width: 38,
                                    height: 38,
                                    decoration: BoxDecoration(
                                      color: _activeTab == 0 ? const Color(0xFF0EA5E9) : const Color(0xFF10B981),
                                      borderRadius: BorderRadius.circular(10),
                                    ),
                                    child: IconButton(
                                      padding: EdgeInsets.zero,
                                      icon: const Icon(Icons.send_rounded, size: 18, color: Colors.white),
                                      onPressed: _handleSend,
                                    ),
                                  ),
                          ],
                        ),
                      ),
                  ],
                ),
              ),
            ),
          ),

        // ── 2. PERSISTENT FLOATING BUBBLE BUTTON ────────────────────────────
        Positioned(
          left: currentPos.dx,
          top: currentPos.dy,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              // Tooltip Preview Callout when new private message arrives
              if (_unreadCount > 0 && !_isExpanded && _lastMessage != null)
                GestureDetector(
                  onTap: () {
                    setState(() {
                      _isExpanded = true;
                      _activeTab = 0; // Messages tab
                      _selectedInstructor = _instructors.first; // Open instructor thread
                      _unreadCount = 0;
                    });
                  },
                  child: Container(
                    margin: const EdgeInsets.only(bottom: 6),
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    constraints: const BoxConstraints(maxWidth: 220),
                    decoration: BoxDecoration(
                      color: const Color(0xFF0F172A),
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(color: const Color(0xFF38BDF8), width: 1.2),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withValues(alpha: 0.4),
                          blurRadius: 12,
                          offset: const Offset(0, 4),
                        ),
                      ],
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Row(
                          children: [
                            Text(
                              'Instructor message:',
                              style: TextStyle(
                                fontSize: 11,
                                fontWeight: FontWeight.bold,
                                color: Color(0xFF38BDF8),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 2),
                        Text(
                          _lastMessage!.content,
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(fontSize: 11, color: Colors.white),
                        ),
                      ],
                    ),
                  ),
                ),

              // Floating Bubble Icon
              GestureDetector(
                behavior: HitTestBehavior.opaque,
                onPanUpdate: _onPanUpdate,
                onTap: () {
                  setState(() {
                    _isExpanded = !_isExpanded;
                    if (_isExpanded) _unreadCount = 0;
                  });
                },
                child: Stack(
                  clipBehavior: Clip.none,
                  children: [
                    Container(
                      width: _size,
                      height: _size,
                      decoration: BoxDecoration(
                        gradient: AppTheme.blueGreenGradient,
                        shape: BoxShape.circle,
                        boxShadow: [
                          BoxShadow(
                            color: const Color(0xFF3B82F6).withValues(alpha: 0.5),
                            blurRadius: 16,
                            spreadRadius: 2,
                          ),
                        ],
                      ),
                      child: Icon(
                        _isExpanded ? Icons.close_rounded : Icons.support_agent_rounded,
                        color: Colors.white,
                        size: 28,
                      ),
                    ),

                    // Unread Badge Counter
                    if (_unreadCount > 0 && !_isExpanded)
                      Positioned(
                        top: -4,
                        right: -4,
                        child: Container(
                          padding: const EdgeInsets.all(6),
                          decoration: const BoxDecoration(
                            color: Color(0xFFEF4444),
                            shape: BoxShape.circle,
                          ),
                          child: Text(
                            '$_unreadCount',
                            style: const TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.bold,
                              color: Colors.white,
                            ),
                          ),
                        ),
                      ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  // ── TAB 0 - SUBVIEW A: Instructor List ─────────────────────────────────────
  Widget _buildInstructorList() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Padding(
          padding: EdgeInsets.fromLTRB(14, 12, 14, 8),
          child: Text(
            'Instructor List',
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.bold,
              color: Color(0xFF94A3B8),
            ),
          ),
        ),
        Expanded(
          child: ListView.builder(
            padding: const EdgeInsets.symmetric(horizontal: 10),
            itemCount: _instructors.length,
            itemBuilder: (context, index) {
              final inst = _instructors[index];
              return Card(
                color: const Color(0xFF1E293B),
                margin: const EdgeInsets.only(bottom: 8),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(14),
                  side: BorderSide(color: const Color(0xFF38BDF8).withValues(alpha: 0.3)),
                ),
                child: ListTile(
                  contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                  leading: Stack(
                    children: [
                      Container(
                        width: 42,
                        height: 42,
                        decoration: const BoxDecoration(
                          color: Color(0xFF0EA5E9),
                          shape: BoxShape.circle,
                        ),
                        child: const Icon(Icons.person_rounded, color: Colors.white, size: 24),
                      ),
                      Positioned(
                        right: 0,
                        bottom: 0,
                        child: Container(
                          width: 12,
                          height: 12,
                          decoration: BoxDecoration(
                            color: const Color(0xFF22C55E),
                            shape: BoxShape.circle,
                            border: Border.all(color: const Color(0xFF1E293B), width: 2),
                          ),
                        ),
                      ),
                    ],
                  ),
                  title: Text(
                    inst.name,
                    style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: Colors.white),
                  ),
                  subtitle: Text(
                    inst.title,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontSize: 11, color: Color(0xFF94A3B8)),
                  ),
                  trailing: const Icon(Icons.chevron_right_rounded, color: Color(0xFF38BDF8)),
                  onTap: () {
                    setState(() {
                      _selectedInstructor = inst;
                      _unreadCount = 0;
                    });
                  },
                ),
              );
            },
          ),
        ),
      ],
    );
  }

  // ── TAB 0 - SUBVIEW B: Instructor Chat Thread ──────────────────────────────
  Widget _buildInstructorMessageThread() {
    final chanId = _privateChannelId ?? 'private_${ref.watch(activeStudentIdProvider)}';
    final messagesAsync = ref.watch(channelThreadMessagesProvider(ChannelMessagesArgs(channelId: chanId)));

    return messagesAsync.when(
      loading: () => const Center(child: CircularProgressIndicator(color: Color(0xFF38BDF8), strokeWidth: 2)),
      error: (e, _) => const Center(child: Text('No private messages yet', style: TextStyle(color: Color(0xFF94A3B8), fontSize: 12))),
      data: (messages) {
        if (messages.isEmpty) {
          return Center(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Text(
                'Private message to ${_selectedInstructor?.name ?? "Instructor"}.\nYou can send academic queries here.',
                textAlign: TextAlign.center,
                style: const TextStyle(color: Color(0xFF94A3B8), fontSize: 12),
              ),
            ),
          );
        }

        final activeStudentId = ref.watch(activeStudentIdProvider).toString();

        return ListView.builder(
          controller: _msgScrollController,
          padding: const EdgeInsets.all(12),
          itemCount: messages.length,
          itemBuilder: (context, index) {
            final msg = messages[index];
            final isMe = msg.senderId.toString() == activeStudentId;
            final isTeacher = msg.senderRole == 'instructor';

            return Align(
              alignment: isMe ? Alignment.centerRight : Alignment.centerLeft,
              child: Container(
                margin: const EdgeInsets.only(bottom: 8),
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                constraints: const BoxConstraints(maxWidth: 240),
                decoration: BoxDecoration(
                  color: isMe
                      ? const Color(0xFF0EA5E9)
                      : (isTeacher ? const Color(0xFF1E293B) : const Color(0xFF334155)),
                  borderRadius: BorderRadius.only(
                    topLeft: const Radius.circular(14),
                    topRight: const Radius.circular(14),
                    bottomLeft: Radius.circular(isMe ? 14 : 2),
                    bottomRight: Radius.circular(isMe ? 2 : 14),
                  ),
                  border: isTeacher ? Border.all(color: const Color(0xFF38BDF8).withValues(alpha: 0.4)) : null,
                ),
                child: Column(
                  crossAxisAlignment: isMe ? CrossAxisAlignment.end : CrossAxisAlignment.start,
                  children: [
                    if (!isMe)
                      Text(
                        isTeacher ? (_selectedInstructor?.name ?? 'Instructor') : 'Student',
                        style: TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                          color: isTeacher ? const Color(0xFF38BDF8) : const Color(0xFF94A3B8),
                        ),
                      ),
                    Text(
                      msg.content,
                      style: const TextStyle(fontSize: 12, color: Colors.white),
                    ),
                  ],
                ),
              ),
            );
          },
        );
      },
    );
  }

  // ── TAB 1: AI Study Assistant Chat ───────────────────────────────────────
  Widget _buildAiChatList() {
    final chatState = ref.watch(chatProvider);
    final messages = chatState.active?.messages ?? [];

    if (messages.isEmpty) {
      return ListView(
        padding: const EdgeInsets.all(14),
        children: [
          const Center(
            child: Column(
              children: [
                Icon(Icons.auto_awesome_rounded, size: 32, color: Color(0xFF10B981)),
                SizedBox(height: 8),
                Text(
                  'AI Learning Assistant',
                  style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: Colors.white),
                ),
                SizedBox(height: 4),
                Text(
                  'Ask AI to summarize lectures, solve exercises, or answer study questions.',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 11, color: Color(0xFF94A3B8)),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          Wrap(
            spacing: 6,
            runSpacing: 6,
            children: [
              _aiChip('Summarize lecture'),
              _aiChip('Explain concept'),
              _aiChip('Study plan for exam'),
            ],
          ),
        ],
      );
    }

    return ListView.builder(
      controller: _aiScrollController,
      padding: const EdgeInsets.all(12),
      itemCount: messages.length,
      itemBuilder: (context, index) {
        final msg = messages[index];
        final isUser = msg.role == 'user';

        return Align(
          alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
          child: Container(
            margin: const EdgeInsets.only(bottom: 8),
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            constraints: const BoxConstraints(maxWidth: 260),
            decoration: BoxDecoration(
              color: isUser ? const Color(0xFF10B981) : const Color(0xFF1E293B),
              borderRadius: BorderRadius.only(
                topLeft: const Radius.circular(14),
                topRight: const Radius.circular(14),
                bottomLeft: Radius.circular(isUser ? 14 : 2),
                bottomRight: Radius.circular(isUser ? 2 : 14),
              ),
              border: isUser ? null : Border.all(color: const Color(0xFF10B981).withValues(alpha: 0.3)),
            ),
            child: FormattedText(
              msg.content,
              baseStyle: const TextStyle(fontSize: 12, color: Colors.white),
            ),
          ),
        );
      },
    );
  }

  Widget _aiChip(String label) {
    return GestureDetector(
      onTap: () {
        _textController.text = label;
        _handleSend();
      },
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        decoration: BoxDecoration(
          color: const Color(0xFF1E293B),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: const Color(0xFF10B981).withValues(alpha: 0.4)),
        ),
        child: Text(
          label,
          style: const TextStyle(fontSize: 11, color: Color(0xFF34D399)),
        ),
      ),
    );
  }

  void _handleSend() {
    if (_activeTab == 0) {
      _sendPrivateMessage();
    } else {
      _sendAiMessage();
    }
  }

  Future<void> _sendPrivateMessage() async {
    final text = _textController.text.trim();
    if (text.isEmpty || _isSending) return;

    setState(() => _isSending = true);
    try {
      if (_privateChannelId == null) {
        await _loadPrivateChannel();
      }
      final studentId = ref.read(activeStudentIdProvider);
      final chanId = _privateChannelId ?? 'private_$studentId';
      final api = ref.read(apiServiceProvider);
      final sentMsg = await api.postChannelMessage(
        channelId: chanId,
        senderId: studentId,
        content: text,
        channelType: 'private_message',
      );
      _textController.clear();
      final targetChanId = sentMsg?.channelId ?? chanId;
      if (_privateChannelId != targetChanId) {
        setState(() {
          _privateChannelId = targetChanId;
        });
      }
      ref.invalidate(channelThreadMessagesProvider(ChannelMessagesArgs(channelId: targetChanId)));
    } catch (_) {}
    if (mounted) {
      setState(() => _isSending = false);
    }
  }

  void _sendAiMessage() {
    final text = _textController.text.trim();
    if (text.isEmpty) return;
    ref.read(chatProvider.notifier).sendMessage(text);
    _textController.clear();
    Future.delayed(const Duration(milliseconds: 150), _scrollToAiBottom);
  }
}
