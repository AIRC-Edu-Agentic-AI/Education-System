import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:student_agent/models/course_model.dart';
import 'package:student_agent/providers/providers.dart';

class NotificationToast {
  static OverlayEntry? _currentEntry;

  static void show(
    BuildContext context, {
    required String title,
    required String body,
    String type = 'info',
    VoidCallback? onTap,
  }) {
    try {
      _currentEntry?.remove();
      _currentEntry = null;
    } catch (_) {}

    final overlayState = Overlay.maybeOf(context, rootOverlay: true);
    if (overlayState == null) return;

    late OverlayEntry entry;

    entry = OverlayEntry(
      builder: (context) => Positioned(
        top: 45,
        right: 20,
        width: 350,
        child: Material(
          color: Colors.transparent,
          child: Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: const Color(0xFF1E293B),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                color: const Color(0xFF38BDF8).withValues(alpha: 0.6),
                width: 1.5,
              ),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.5),
                  blurRadius: 20,
                  offset: const Offset(0, 8),
                ),
              ],
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: const Color(0xFF0EA5E9).withValues(alpha: 0.2),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(
                    Icons.notifications_active_rounded,
                    color: Color(0xFF38BDF8),
                    size: 20,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: InkWell(
                    borderRadius: BorderRadius.circular(8),
                    onTap: () {
                      try {
                        entry.remove();
                        _currentEntry = null;
                      } catch (_) {}
                      if (onTap != null) onTap();
                    },
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Row(
                          children: [
                            Expanded(
                              child: Text(
                                title,
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                                style: const TextStyle(
                                  fontSize: 13,
                                  fontWeight: FontWeight.bold,
                                  color: Colors.white,
                                ),
                              ),
                            ),
                            const SizedBox(width: 6),
                            Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 6,
                                vertical: 2,
                              ),
                              decoration: BoxDecoration(
                                color: const Color(0xFFEF4444),
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: const Text(
                                'New',
                                style: TextStyle(
                                  fontSize: 10,
                                  color: Colors.white,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 4),
                        Text(
                          body,
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                            fontSize: 12,
                            color: Color(0xFF94A3B8),
                            height: 1.3,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                InkWell(
                  onTap: () {
                    try {
                      entry.remove();
                      _currentEntry = null;
                    } catch (_) {}
                  },
                  child: const Padding(
                    padding: EdgeInsets.all(4),
                    child: Icon(Icons.close, size: 16, color: Color(0xFF64748B)),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );

    _currentEntry = entry;
    overlayState.insert(entry);

    Future.delayed(const Duration(seconds: 5), () {
      if (_currentEntry == entry) {
        try {
          entry.remove();
          _currentEntry = null;
        } catch (_) {}
      }
    });
  }
}

class ChatMessageToast {
  static OverlayEntry? _currentEntry;

  static void show(
    BuildContext context, {
    required WidgetRef ref,
    required CourseMessage message,
    VoidCallback? onTap,
  }) {
    try {
      _currentEntry?.remove();
      _currentEntry = null;
    } catch (_) {}

    final overlayState = Overlay.maybeOf(context, rootOverlay: true);
    if (overlayState == null) return;

    late OverlayEntry entry;
    final controller = TextEditingController();
    bool sending = false;

    entry = OverlayEntry(
      builder: (context) => StatefulBuilder(
        builder: (context, setState) {
          return Positioned(
            top: 45,
            right: 20,
            width: 360,
            child: Material(
              color: Colors.transparent,
              child: Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: const Color(0xFF0F172A),
                  borderRadius: BorderRadius.circular(18),
                  border: Border.all(
                    color: const Color(0xFF10B981).withValues(alpha: 0.7),
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
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.all(8),
                          decoration: BoxDecoration(
                            color: const Color(0xFF10B981).withValues(alpha: 0.2),
                            shape: BoxShape.circle,
                          ),
                          child: const Icon(
                            Icons.mark_chat_unread_rounded,
                            color: Color(0xFF34D399),
                            size: 20,
                          ),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: InkWell(
                            onTap: () {
                              try {
                                entry.remove();
                                _currentEntry = null;
                              } catch (_) {}
                              if (onTap != null) onTap();
                            },
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  children: [
                                    Text(
                                      'Instructor',
                                      style: const TextStyle(
                                        fontSize: 13,
                                        fontWeight: FontWeight.bold,
                                        color: Colors.white,
                                      ),
                                    ),
                                    if (message.courseCode != null) ...[
                                      const SizedBox(width: 6),
                                      Container(
                                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1.5),
                                        decoration: BoxDecoration(
                                          color: const Color(0xFF3B82F6).withValues(alpha: 0.25),
                                          borderRadius: BorderRadius.circular(6),
                                        ),
                                        child: Text(
                                          message.courseCode!,
                                          style: const TextStyle(
                                            fontSize: 10,
                                            color: Color(0xFF60A5FA),
                                            fontWeight: FontWeight.w600,
                                          ),
                                        ),
                                      ),
                                    ],
                                  ],
                                ),
                                const SizedBox(height: 2),
                                Text(
                                  message.content,
                                  maxLines: 2,
                                  overflow: TextOverflow.ellipsis,
                                  style: const TextStyle(
                                    fontSize: 12,
                                    color: Color(0xFFCBD5E1),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                        IconButton(
                          icon: const Icon(Icons.close, size: 18, color: Color(0xFF64748B)),
                          onPressed: () {
                            try {
                              entry.remove();
                              _currentEntry = null;
                            } catch (_) {}
                          },
                        ),
                      ],
                    ),
                    const SizedBox(height: 10),
                    Row(
                      children: [
                        Expanded(
                          child: Container(
                            height: 38,
                            padding: const EdgeInsets.symmetric(horizontal: 12),
                            decoration: BoxDecoration(
                              color: const Color(0xFF1E293B),
                              borderRadius: BorderRadius.circular(10),
                              border: Border.all(color: const Color(0xFF334155)),
                            ),
                            child: TextField(
                              controller: controller,
                              style: const TextStyle(fontSize: 12, color: Colors.white),
                              decoration: const InputDecoration(
                                hintText: 'Write quick reply...',
                                hintStyle: TextStyle(fontSize: 12, color: Color(0xFF64748B)),
                                border: InputBorder.none,
                                isDense: true,
                                contentPadding: EdgeInsets.symmetric(vertical: 10),
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        sending
                            ? const SizedBox(
                                width: 24,
                                height: 24,
                                child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFF34D399)),
                              )
                            : Container(
                                width: 38,
                                height: 38,
                                decoration: BoxDecoration(
                                  color: const Color(0xFF10B981),
                                  borderRadius: BorderRadius.circular(10),
                                ),
                                child: IconButton(
                                  padding: EdgeInsets.zero,
                                  icon: const Icon(Icons.send_rounded, size: 18, color: Colors.white),
                                  onPressed: () async {
                                    final text = controller.text.trim();
                                    if (text.isEmpty) return;
                                    setState(() => sending = true);
                                    try {
                                      final studentId = ref.read(activeStudentIdProvider);
                                      final api = ref.read(apiServiceProvider);
                                      await api.postChannelMessage(
                                        channelId: message.channelId,
                                        senderId: studentId,
                                        content: text,
                                        courseCode: message.courseCode,
                                      );
                                      ref.invalidate(channelThreadMessagesProvider(ChannelMessagesArgs(channelId: message.channelId)));
                                      try {
                                        entry.remove();
                                        _currentEntry = null;
                                      } catch (_) {}
                                      if (context.mounted) {
                                        ScaffoldMessenger.of(context).showSnackBar(
                                          const SnackBar(
                                            content: Text('Reply sent to instructor!'),
                                            backgroundColor: Color(0xFF10B981),
                                            duration: Duration(seconds: 2),
                                          ),
                                        );
                                      }
                                    } catch (e) {
                                      setState(() => sending = false);
                                    }
                                  },
                                ),
                              ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          );
        },
      ),
    );

    _currentEntry = entry;
    overlayState.insert(entry);

    Future.delayed(const Duration(seconds: 10), () {
      if (_currentEntry == entry) {
        try {
          entry.remove();
          _currentEntry = null;
        } catch (_) {}
      }
    });
  }
}
