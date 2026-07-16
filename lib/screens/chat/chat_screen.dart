import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:student_agent/core/theme/app_theme.dart';
import 'package:student_agent/models/chat_message_model.dart';
import 'package:student_agent/providers/providers.dart';
import 'package:student_agent/widgets/formatted_text.dart';

class ChatScreen extends ConsumerStatefulWidget {
  const ChatScreen({super.key});

  @override
  ConsumerState<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends ConsumerState<ChatScreen> {
  final _controller = TextEditingController();
  final _scrollController = ScrollController();

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _send() {
    final text = _controller.text.trim();
    if (text.isEmpty) return;
    ref.read(chatProvider.notifier).sendMessage(text);
    _controller.clear();
    Future.delayed(const Duration(milliseconds: 100), _scrollToBottom);
  }

  void _scrollToBottom() {
    if (_scrollController.hasClients) {
      _scrollController.animateTo(
        _scrollController.position.maxScrollExtent,
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeOut,
      );
    }
  }

  void _showConversationSheet(BuildContext context, ChatState chatState) {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppTheme.surfaceDark,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => _ConversationSheet(
        conversations: chatState.conversations,
        activeId: chatState.activeId,
        onSelect: (id) {
          ref.read(chatProvider.notifier).switchConversation(id);
          Navigator.of(context).pop();
        },
        onDelete: (id) => ref.read(chatProvider.notifier).deleteConversation(id),
        onNew: () {
          ref.read(chatProvider.notifier).newConversation();
          Navigator.of(context).pop();
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final chatState = ref.watch(chatProvider);
    final active = chatState.active;

    ref.listen(activeChatProvider, (_, __) {
      Future.delayed(const Duration(milliseconds: 50), _scrollToBottom);
    });

    return Scaffold(
      backgroundColor: AppTheme.backgroundDark,
      appBar: AppBar(
        backgroundColor: AppTheme.navBar,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded,
              size: 18, color: AppTheme.textSecondary),
          onPressed: () =>
              context.canPop() ? context.pop() : context.go('/'),
        ),
        title: Row(
          children: [
            Container(
              width: 32,
              height: 32,
              decoration: const BoxDecoration(
                gradient: AppTheme.blueGreenGradient,
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.auto_awesome_rounded,
                  size: 16, color: Colors.white),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    active?.title ?? 'AI Study Assistant',
                    style: const TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                        color: AppTheme.textPrimary),
                    overflow: TextOverflow.ellipsis,
                  ),
                  const Text('Luôn trực tuyến',
                      style: TextStyle(
                          fontSize: 11, color: AppTheme.accentGreen)),
                ],
              ),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.add_comment_outlined,
                size: 20, color: AppTheme.textSecondary),
            onPressed: () => ref.read(chatProvider.notifier).newConversation(),
            tooltip: 'Cuộc hội thoại mới',
          ),
          IconButton(
            icon: const Icon(Icons.forum_outlined,
                size: 20, color: AppTheme.textSecondary),
            onPressed: () => _showConversationSheet(context, chatState),
            tooltip: 'Danh sách hội thoại',
          ),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: active == null || active.messages.isEmpty
                ? const _EmptyState()
                : ListView.builder(
                    controller: _scrollController,
                    padding: const EdgeInsets.all(16),
                    itemCount: active.messages.length,
                    itemBuilder: (_, i) =>
                        _ChatBubble(message: active.messages[i]),
                  ),
          ),
          _SuggestedPrompts(onTap: (text) {
            _controller.text = text;
            _send();
          }),
          _ChatInput(
            controller: _controller,
            onSend: _send,
            enabled: !chatState.isLoading,
          ),
        ],
      ),
    );
  }
}

// ── Conversation bottom sheet ─────────────────────────────────────────────────

class _ConversationSheet extends StatelessWidget {
  final List<ChatConversation> conversations;
  final String? activeId;
  final void Function(String) onSelect;
  final void Function(String) onDelete;
  final VoidCallback onNew;

  const _ConversationSheet({
    required this.conversations,
    required this.activeId,
    required this.onSelect,
    required this.onDelete,
    required this.onNew,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        // Handle bar
        Container(
          margin: const EdgeInsets.only(top: 12),
          width: 36,
          height: 4,
          decoration: BoxDecoration(
            color: AppTheme.textMuted,
            borderRadius: BorderRadius.circular(2),
          ),
        ),
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 16, 8, 8),
          child: Row(
            children: [
              const Text('Hội thoại',
                  style: TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.w600,
                      color: AppTheme.textPrimary)),
              const Spacer(),
              IconButton(
                icon: const Icon(Icons.add, size: 20, color: AppTheme.primaryBlue),
                onPressed: onNew,
                tooltip: 'Cuộc hội thoại mới',
              ),
            ],
          ),
        ),
        const Divider(height: 0, color: AppTheme.divider),
        ConstrainedBox(
          constraints: BoxConstraints(
            maxHeight: MediaQuery.sizeOf(context).height * 0.5,
          ),
          child: conversations.isEmpty
              ? const Padding(
                  padding: EdgeInsets.all(24),
                  child: Text('Chưa có hội thoại nào',
                      style: TextStyle(
                          fontSize: 13, color: AppTheme.textSecondary)),
                )
              : ListView.builder(
                  shrinkWrap: true,
                  itemCount: conversations.length,
                  itemBuilder: (_, i) {
                    final conv = conversations[i];
                    final isActive = conv.id == activeId;
                    return ListTile(
                      selected: isActive,
                      selectedTileColor: AppTheme.primaryBlueGlow,
                      shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(8)),
                      contentPadding:
                          const EdgeInsets.symmetric(horizontal: 12),
                      dense: true,
                      leading: Icon(
                        Icons.chat_bubble_outline_rounded,
                        size: 18,
                        color: isActive
                            ? AppTheme.primaryBlue
                            : AppTheme.textSecondary,
                      ),
                      title: Text(
                        conv.title,
                        style: TextStyle(
                          fontSize: 13,
                          color: isActive
                              ? AppTheme.primaryBlue
                              : AppTheme.textPrimary,
                          fontWeight: isActive
                              ? FontWeight.w500
                              : FontWeight.normal,
                        ),
                        overflow: TextOverflow.ellipsis,
                      ),
                      trailing: IconButton(
                        icon: const Icon(Icons.delete_outline,
                            size: 16, color: AppTheme.textMuted),
                        onPressed: () => onDelete(conv.id),
                      ),
                      onTap: () => onSelect(conv.id),
                    );
                  },
                ),
        ),
        SizedBox(height: MediaQuery.paddingOf(context).bottom + 8),
      ],
    );
  }
}

// ── Chat bubble ───────────────────────────────────────────────────────────────

class _ChatBubble extends StatefulWidget {
  final ChatMessage message;
  const _ChatBubble({required this.message});

  @override
  State<_ChatBubble> createState() => _ChatBubbleState();
}

class _ChatBubbleState extends State<_ChatBubble> {
  bool _reasoningExpanded = false;

  @override
  Widget build(BuildContext context) {
    final msg = widget.message;
    final isUser = msg.isUser;
    final hasReasoning = msg.reasoning.isNotEmpty;
    final hasToolCalls = msg.toolCalls.isNotEmpty;
    final showLoadingDots =
        msg.isLoading && msg.content.isEmpty && !hasReasoning && !hasToolCalls;
    final showContent = msg.content.isNotEmpty || showLoadingDots;

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        mainAxisAlignment:
            isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (!isUser) ...[
            Container(
              width: 28,
              height: 28,
              decoration: const BoxDecoration(
                gradient: AppTheme.blueGreenGradient,
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.auto_awesome_rounded,
                  size: 13, color: Colors.white),
            ),
            const SizedBox(width: 8),
          ],
          Flexible(
            child: Column(
              crossAxisAlignment:
                  isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
              children: [
                if (!isUser && hasToolCalls)
                  _ToolCallChips(toolCalls: msg.toolCalls),
                if (!isUser && hasReasoning)
                  _ReasoningBlock(
                    reasoning: msg.reasoning,
                    isThinkingDone: msg.isThinkingDone,
                    expanded: _reasoningExpanded,
                    onToggle: () => setState(
                        () => _reasoningExpanded = !_reasoningExpanded),
                  ),
                if (showContent)
                  Container(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 14, vertical: 10),
                    decoration: BoxDecoration(
                      color: isUser
                          ? AppTheme.primaryBlueGlow
                          : AppTheme.surfaceCard,
                      borderRadius: BorderRadius.only(
                        topLeft: const Radius.circular(16),
                        topRight: const Radius.circular(16),
                        bottomLeft: Radius.circular(isUser ? 16 : 4),
                        bottomRight: Radius.circular(isUser ? 4 : 16),
                      ),
                      border: Border.all(
                        color: isUser
                            ? AppTheme.primaryBlue.withValues(alpha: 0.4)
                            : AppTheme.cardBorder,
                        width: 1,
                      ),
                    ),
                    child: showLoadingDots
                        ? const _LoadingDots()
                        : FormattedText(
                            msg.content,
                            baseStyle: const TextStyle(
                              fontSize: 14,
                              height: 1.5,
                              color: AppTheme.textPrimary,
                            ),
                          ),
                  ),
              ],
            ),
          ),
          if (isUser) const SizedBox(width: 8),
        ],
      ),
    );
  }
}

// ── Tool call chips ───────────────────────────────────────────────────────────

class _ToolCallChips extends StatelessWidget {
  final List<ToolCallInfo> toolCalls;
  const _ToolCallChips({required this.toolCalls});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Wrap(
        spacing: 6,
        runSpacing: 4,
        children: toolCalls
            .map(
              (tc) => Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: AppTheme.primaryBlueGlow,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                      color: AppTheme.primaryBlue.withValues(alpha: 0.3),
                      width: 1),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.data_object_rounded,
                        size: 12, color: AppTheme.primaryBlue),
                    const SizedBox(width: 4),
                    Text(
                      tc.displayLabel,
                      style: const TextStyle(
                          fontSize: 11, color: AppTheme.primaryBlue),
                    ),
                  ],
                ),
              ),
            )
            .toList(),
      ),
    );
  }
}

// ── Reasoning block ───────────────────────────────────────────────────────────

class _ReasoningBlock extends StatelessWidget {
  final String reasoning;
  final bool isThinkingDone;
  final bool expanded;
  final VoidCallback onToggle;

  const _ReasoningBlock({
    required this.reasoning,
    required this.isThinkingDone,
    required this.expanded,
    required this.onToggle,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 6),
      constraints: const BoxConstraints(maxWidth: 300),
      decoration: BoxDecoration(
        color: AppTheme.surfaceDark,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppTheme.cardBorder, width: 1),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          GestureDetector(
            onTap: onToggle,
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  if (!isThinkingDone)
                    const SizedBox(
                      width: 11,
                      height: 11,
                      child: CircularProgressIndicator(
                          strokeWidth: 1.5, color: AppTheme.primaryBlue),
                    )
                  else
                    const Icon(Icons.psychology_outlined,
                        size: 13, color: AppTheme.textSecondary),
                  const SizedBox(width: 6),
                  Text(
                    isThinkingDone ? 'Đã suy nghĩ' : 'Đang suy nghĩ...',
                    style: const TextStyle(
                        fontSize: 12, color: AppTheme.textSecondary),
                  ),
                  const SizedBox(width: 4),
                  Icon(
                    expanded ? Icons.expand_less : Icons.expand_more,
                    size: 13,
                    color: AppTheme.textSecondary,
                  ),
                ],
              ),
            ),
          ),
          if (expanded)
            Padding(
              padding: const EdgeInsets.fromLTRB(10, 0, 10, 8),
              child: Text(
                reasoning,
                style: const TextStyle(
                  fontSize: 12,
                  color: AppTheme.textSecondary,
                  fontStyle: FontStyle.italic,
                  height: 1.5,
                ),
              ),
            ),
        ],
      ),
    );
  }
}

// ── Loading dots ──────────────────────────────────────────────────────────────

class _LoadingDots extends StatefulWidget {
  const _LoadingDots();

  @override
  State<_LoadingDots> createState() => _LoadingDotsState();
}

class _LoadingDotsState extends State<_LoadingDots>
    with SingleTickerProviderStateMixin {
  late AnimationController _c;

  @override
  void initState() {
    super.initState();
    _c = AnimationController(
        vsync: this, duration: const Duration(milliseconds: 900))
      ..repeat();
  }

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _c,
      builder: (_, __) => Row(
        mainAxisSize: MainAxisSize.min,
        children: List.generate(3, (i) {
          final delay = i / 3.0;
          final val = ((_c.value - delay) % 1.0).clamp(0.0, 1.0);
          final scale = 1.0 + (val < 0.5 ? val : 1.0 - val) * 0.5;
          return Container(
            margin: const EdgeInsets.symmetric(horizontal: 2),
            width: 8 * scale,
            height: 8 * scale,
            decoration: BoxDecoration(
              color: AppTheme.primaryBlue.withValues(alpha: 0.6),
              shape: BoxShape.circle,
            ),
          );
        }),
      ),
    );
  }
}

// ── Suggested prompts ─────────────────────────────────────────────────────────

class _SuggestedPrompts extends StatelessWidget {
  final void Function(String) onTap;
  const _SuggestedPrompts({required this.onTap});

  static const _prompts = [
    'Tóm tắt tuần này',
    'Tôi cần ôn gì cho TMA?',
    'Giải thích khái niệm khó',
    'Lên kế hoạch học cuối tuần',
  ];

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 40,
      padding: const EdgeInsets.symmetric(horizontal: 12),
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: _prompts.length,
        separatorBuilder: (_, __) => const SizedBox(width: 8),
        itemBuilder: (_, i) => GestureDetector(
          onTap: () => onTap(_prompts[i]),
          child: Container(
            alignment: Alignment.center,
            padding: const EdgeInsets.symmetric(horizontal: 12),
            decoration: BoxDecoration(
              color: AppTheme.surfaceDark,
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: AppTheme.cardBorder, width: 1),
            ),
            child: Text(
              _prompts[i],
              style: const TextStyle(
                  fontSize: 12, color: AppTheme.textSecondary),
            ),
          ),
        ),
      ),
    );
  }
}

// ── Chat input ────────────────────────────────────────────────────────────────

class _ChatInput extends StatelessWidget {
  final TextEditingController controller;
  final VoidCallback onSend;
  final bool enabled;

  const _ChatInput({
    required this.controller,
    required this.onSend,
    required this.enabled,
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
          Expanded(
            child: TextField(
              controller: controller,
              decoration: const InputDecoration(
                hintText: 'Nhập câu hỏi...',
              ),
              style: const TextStyle(fontSize: 14, color: AppTheme.textPrimary),
              onSubmitted: enabled ? (_) => onSend() : null,
              textInputAction: TextInputAction.send,
              maxLines: 3,
              minLines: 1,
              enabled: enabled,
            ),
          ),
          const SizedBox(width: 8),
          GestureDetector(
            onTap: enabled ? onSend : null,
            child: Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                gradient: enabled ? AppTheme.blueGreenGradient : null,
                color: enabled ? null : AppTheme.textMuted,
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.arrow_upward_rounded,
                  color: Colors.white, size: 18),
            ),
          ),
        ],
      ),
    );
  }
}

// ── Empty state ───────────────────────────────────────────────────────────────

class _EmptyState extends StatelessWidget {
  const _EmptyState();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 64,
            height: 64,
            decoration: const BoxDecoration(
              gradient: AppTheme.blueGreenGradient,
              shape: BoxShape.circle,
            ),
            child: const Icon(Icons.auto_awesome_rounded,
                size: 28, color: Colors.white),
          ),
          const SizedBox(height: 16),
          ShaderMask(
            shaderCallback: (b) =>
                AppTheme.blueGreenGradient.createShader(b),
            child: const Text(
              'AI Study Assistant',
              style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w700,
                  color: Colors.white),
            ),
          ),
          const SizedBox(height: 6),
          const Text('Hỏi về bài học, lịch học, hoặc bài nộp',
              style: TextStyle(
                  fontSize: 13, color: AppTheme.textSecondary)),
        ],
      ),
    );
  }
}
