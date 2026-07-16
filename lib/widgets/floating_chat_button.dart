import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:student_agent/core/theme/app_theme.dart';

class FloatingChatButton extends StatefulWidget {
  /// The actual size of the Stack (body area, excluding nav bar).
  /// Passed in from LayoutBuilder in AppShell so positioning is always correct.
  final Size bodySize;

  const FloatingChatButton({super.key, required this.bodySize});

  @override
  State<FloatingChatButton> createState() => _FloatingChatButtonState();
}

class _FloatingChatButtonState extends State<FloatingChatButton> {
  static const double _size = 56;

  /// Null = use anchored Positioned(bottom:16, right:16).
  /// Set on first drag to absolute top-left within the Stack.
  Offset? _pos;

  void _onPanUpdate(DragUpdateDetails d) {
    final size = widget.bodySize;
    // First drag: initialise from the default bottom-right anchor position.
    _pos ??= Offset(size.width - _size - 16, size.height - _size - 16);
    setState(() {
      _pos = Offset(
        (_pos!.dx + d.delta.dx).clamp(0.0, size.width - _size),
        (_pos!.dy + d.delta.dy).clamp(0.0, size.height - _size),
      );
    });
  }

  @override
  Widget build(BuildContext context) {
    final button = GestureDetector(
      behavior: HitTestBehavior.opaque,
      onPanUpdate: _onPanUpdate,
      onTap: () => context.push('/chat'),
      child: Container(
        width: _size,
        height: _size,
        decoration: const BoxDecoration(
          gradient: AppTheme.blueGreenGradient,
          shape: BoxShape.circle,
          boxShadow: [
            BoxShadow(
              color: Color(0x663B82F6), // primaryBlue 40% opacity
              blurRadius: 16,
              spreadRadius: 2,
            ),
          ],
        ),
        child: const Icon(
          Icons.auto_awesome_rounded,
          color: Colors.white,
          size: 24,
        ),
      ),
    );

    // Anchored to bottom-right until the user first drags it.
    if (_pos == null) {
      return Positioned(bottom: 16, right: 16, child: button);
    }
    return Positioned(left: _pos!.dx, top: _pos!.dy, child: button);
  }
}
