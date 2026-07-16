import 'package:flutter/material.dart';

/// Lightweight markdown-ish renderer for agent text (chat + notifications).
/// Supports: **bold**, bullet lines (-, *, •), numbered lines (1. / 1)),
/// # headings, and blank-line spacing. No external dependency.
class FormattedText extends StatelessWidget {
  final String text;
  final TextStyle baseStyle;
  const FormattedText(this.text, {required this.baseStyle, super.key});

  static final _bullet = RegExp(r'^\s*[-*•]\s+(.*)');
  static final _numbered = RegExp(r'^\s*(\d+)[.)]\s+(.*)');
  static final _heading = RegExp(r'^#{1,6}\s*(.*)');
  static final _bold = RegExp(r'\*\*(.+?)\*\*');

  TextSpan _inline(String s, TextStyle style) {
    final spans = <TextSpan>[];
    int i = 0;
    for (final m in _bold.allMatches(s)) {
      if (m.start > i) spans.add(TextSpan(text: s.substring(i, m.start)));
      spans.add(TextSpan(
          text: m.group(1), style: const TextStyle(fontWeight: FontWeight.w700)));
      i = m.end;
    }
    if (i < s.length) spans.add(TextSpan(text: s.substring(i)));
    return TextSpan(style: style, children: spans);
  }

  Widget _line(String prefix, String content, TextStyle style) => Padding(
        padding: const EdgeInsets.only(bottom: 3),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(prefix, style: style),
            Expanded(child: RichText(text: _inline(content, style))),
          ],
        ),
      );

  @override
  Widget build(BuildContext context) {
    final children = <Widget>[];
    for (final raw in text.split('\n')) {
      final line = raw.trimRight();
      if (line.trim().isEmpty) {
        children.add(const SizedBox(height: 6));
        continue;
      }
      final b = _bullet.firstMatch(line);
      final n = _numbered.firstMatch(line);
      final h = _heading.firstMatch(line);
      if (b != null) {
        children.add(_line('•  ', b.group(1)!, baseStyle));
      } else if (n != null) {
        children.add(_line('${n.group(1)}. ', n.group(2)!, baseStyle));
      } else if (h != null) {
        children.add(Padding(
          padding: const EdgeInsets.symmetric(vertical: 2),
          child: RichText(
              text: _inline(h.group(1)!,
                  baseStyle.copyWith(fontWeight: FontWeight.w700))),
        ));
      } else {
        children.add(Padding(
          padding: const EdgeInsets.only(bottom: 2),
          child: RichText(text: _inline(line, baseStyle)),
        ));
      }
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: children,
    );
  }
}
