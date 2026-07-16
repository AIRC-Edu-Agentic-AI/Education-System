import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class AppTheme {
  // ── Dark palette ────────────────────────────────────────────────────────────
  static const Color backgroundDark = Color(0xFF0D1117);
  static const Color surfaceDark = Color(0xFF0F1724);
  static const Color surfaceCard = Color(0x0DFFFFFF); // 5% white
  static const Color navBar = Color(0xFF0A0F1A);

  // Accent — blue
  static const Color primaryBlue = Color(0xFF3B82F6);
  static const Color primaryBlueGlow = Color(0x263B82F6); // 15% blue

  // Accent — green
  static const Color accentGreen = Color(0xFF10B981);
  static const Color accentGreenGlow = Color(0x2610B981); // 15% green

  // Semantic
  static const Color danger = Color(0xFFEF4444);
  static const Color dangerGlow = Color(0x26EF4444);
  static const Color warning = Color(0xFFF59E0B);
  static const Color warningGlow = Color(0x26F59E0B);
  static const Color success = Color(0xFF10B981);
  static const Color successGlow = Color(0x2610B981);

  // Text
  static const Color textPrimary = Color(0xFFF0F6FF);
  static const Color textSecondary = Color(0xFF8BA3BE);
  static const Color textMuted = Color(0xFF4A6080);

  // Card / border
  static const Color cardBorder = Color(0x3363B3ED); // 20% blue-ish
  static const Color divider = Color(0xFF1A2540);

  // Gradient
  static const LinearGradient blueGreenGradient = LinearGradient(
    colors: [primaryBlue, accentGreen],
    begin: Alignment.centerLeft,
    end: Alignment.centerRight,
  );

  static const LinearGradient blueGreenGradientDiagonal = LinearGradient(
    colors: [primaryBlue, accentGreen],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  // ── Legacy aliases (kept so existing screens compile without changes) ────────
  static const Color primary = primaryBlue;
  static const Color primaryLight = primaryBlueGlow;
  static const Color teal = accentGreen;
  static const Color tealLight = accentGreenGlow;
  static const Color amber = warning;
  static const Color amberLight = warningGlow;
  static const Color coral = danger;
  static const Color coralLight = dangerGlow;
  static const Color dangerLight = dangerGlow;
  static const Color successLight = successGlow;
  static const Color textSecondaryAlias = textSecondary;
  static const Color border = cardBorder;
  static const Color surfaceGray = surfaceDark;

  // ── Dark ThemeData ───────────────────────────────────────────────────────────
  static ThemeData get dark => ThemeData(
        useMaterial3: true,
      fontFamily: GoogleFonts.poppins().fontFamily,
        brightness: Brightness.dark,
        colorScheme: const ColorScheme.dark(
          brightness: Brightness.dark,
          primary: primaryBlue,
          onPrimary: textPrimary,
          secondary: accentGreen,
          onSecondary: textPrimary,
          surface: surfaceDark,
          onSurface: textPrimary,
          error: danger,
          onError: textPrimary,
        ),
        scaffoldBackgroundColor: backgroundDark,
        appBarTheme: const AppBarTheme(
          backgroundColor: Colors.transparent,
          foregroundColor: textPrimary,
          elevation: 0,
          scrolledUnderElevation: 0,
          titleTextStyle: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w500,
            color: textPrimary,
          ),
          iconTheme: IconThemeData(color: textSecondary),
        ),
        cardTheme: CardThemeData(
          color: surfaceCard,
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
            side: const BorderSide(color: cardBorder, width: 1),
          ),
          margin: EdgeInsets.zero,
        ),
        navigationBarTheme: NavigationBarThemeData(
          backgroundColor: navBar,
          indicatorColor: primaryBlueGlow,
          iconTheme: WidgetStateProperty.resolveWith((states) {
            if (states.contains(WidgetState.selected)) {
              return const IconThemeData(color: primaryBlue, size: 22);
            }
            return const IconThemeData(color: textMuted, size: 22);
          }),
          labelTextStyle: WidgetStateProperty.resolveWith((states) {
            if (states.contains(WidgetState.selected)) {
              return const TextStyle(
                  color: primaryBlue, fontSize: 11, fontWeight: FontWeight.w500);
            }
            return const TextStyle(color: textMuted, fontSize: 11);
          }),
          elevation: 0,
          height: 64,
          labelBehavior: NavigationDestinationLabelBehavior.alwaysShow,
        ),
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: surfaceDark,
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(24),
            borderSide: BorderSide.none,
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(24),
            borderSide: const BorderSide(color: cardBorder, width: 1),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(24),
            borderSide: const BorderSide(color: primaryBlue, width: 1),
          ),
          contentPadding:
              const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          hintStyle: const TextStyle(color: textMuted, fontSize: 14),
        ),
        textTheme: const TextTheme(
          headlineMedium: TextStyle(
              fontSize: 22, fontWeight: FontWeight.w500, color: textPrimary),
          headlineSmall: TextStyle(
              fontSize: 18, fontWeight: FontWeight.w500, color: textPrimary),
          titleMedium: TextStyle(
              fontSize: 16, fontWeight: FontWeight.w500, color: textPrimary),
          titleSmall: TextStyle(
              fontSize: 14, fontWeight: FontWeight.w500, color: textPrimary),
          bodyMedium: TextStyle(fontSize: 14, color: textPrimary),
          bodySmall: TextStyle(fontSize: 12, color: textSecondary),
          labelSmall: TextStyle(fontSize: 11, color: textMuted),
        ),
        chipTheme: ChipThemeData(
          backgroundColor: primaryBlueGlow,
          side: const BorderSide(color: primaryBlue, width: 0.5),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
          labelStyle:
              const TextStyle(fontSize: 12, color: primaryBlue),
        ),
        dividerTheme: const DividerThemeData(
          color: divider,
          thickness: 1,
          space: 0,
        ),
        snackBarTheme: const SnackBarThemeData(
          backgroundColor: surfaceDark,
          contentTextStyle: TextStyle(color: textPrimary),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.all(Radius.circular(12)),
          ),
          behavior: SnackBarBehavior.floating,
        ),
        progressIndicatorTheme: const ProgressIndicatorThemeData(
          color: primaryBlue,
        ),
        iconTheme: const IconThemeData(color: textSecondary),
        floatingActionButtonTheme: const FloatingActionButtonThemeData(
          backgroundColor: primaryBlue,
          foregroundColor: Colors.white,
          elevation: 4,
        ),
        listTileTheme: const ListTileThemeData(
          tileColor: Colors.transparent,
          iconColor: textSecondary,
          textColor: textPrimary,
        ),
        drawerTheme: const DrawerThemeData(
          backgroundColor: surfaceDark,
        ),
      );

  // ── Light alias (keeps MaterialApp.router compiling if still referenced) ────
  static ThemeData get light => dark;
}
