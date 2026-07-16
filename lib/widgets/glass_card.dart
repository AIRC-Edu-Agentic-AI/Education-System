import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:student_agent/core/theme/app_theme.dart';

class GlassCard extends StatelessWidget {
  const GlassCard({
    super.key,
    required this.child,
    this.borderRadius = 16,
    this.padding = const EdgeInsets.all(16),
    this.glowColor = AppTheme.cardBorder,
    this.blurSigma = 12.0,
    this.fillOpacity = 0.05,
    this.gradient,
  });

  final Widget child;
  final double borderRadius;
  final EdgeInsetsGeometry padding;
  final Color glowColor;
  final double blurSigma;
  final double fillOpacity;
  final Gradient? gradient;

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(borderRadius),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: blurSigma, sigmaY: blurSigma),
        child: Container(
          decoration: BoxDecoration(
            color: gradient == null
                ? Colors.white.withValues(alpha: fillOpacity)
                : null,
            gradient: gradient,
            borderRadius: BorderRadius.circular(borderRadius),
            border: Border.all(color: glowColor, width: 1),
          ),
          padding: padding,
          child: child,
        ),
      ),
    );
  }
}
