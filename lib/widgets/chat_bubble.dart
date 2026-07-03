import 'package:flutter/material.dart';

/// ── CHAT BUBBLE WIDGET ────────────────────────────────────────
class ChatBubble extends StatelessWidget {
  final String senderName;
  final String message;
  final String? imageUrl;
  final bool isSender; // true = bên phải (người gửi)

  const ChatBubble({
    super.key,
    required this.senderName,
    required this.message,
    this.imageUrl,
    required this.isSender,
  });

  @override
  Widget build(BuildContext context) {
    final alignment =
        isSender ? Alignment.centerRight : Alignment.centerLeft;

    final bgColor = isSender
        ? Colors.blueAccent
        : Colors.grey.shade300;

    final textColor = isSender ? Colors.white : Colors.black87;

    return Align(
      alignment: alignment,
      child: Container(
        margin: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.7,
        ),
        decoration: BoxDecoration(
          color: bgColor,
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(12),
            topRight: const Radius.circular(12),
            bottomLeft: Radius.circular(isSender ? 12 : 0),
            bottomRight: Radius.circular(isSender ? 0 : 12),
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            /// sender name
            Text(
              senderName,
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.bold,
                color: textColor.withValues(alpha: 0.8),
              ),
            ),

            const SizedBox(height: 4),

            /// message text
            Text(
              message,
              style: TextStyle(
                fontSize: 14,
                color: textColor,
              ),
            ),

            /// optional image
            if (imageUrl != null) ...[
              const SizedBox(height: 8),
              ClipRRect(
                borderRadius: BorderRadius.circular(8),
                child: Image.network(
                  imageUrl!,
                  fit: BoxFit.cover,
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}