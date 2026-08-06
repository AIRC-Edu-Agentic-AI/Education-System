import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:student_agent/core/theme/app_theme.dart';
import 'package:student_agent/providers/providers.dart';
import 'package:student_agent/widgets/floating_chat_button.dart';
import 'package:student_agent/widgets/notification_toast.dart';

class AppShell extends ConsumerStatefulWidget {
  const AppShell({super.key, required this.child});

  final Widget child;

  @override
  ConsumerState<AppShell> createState() => _AppShellState();
}

class _AppShellState extends ConsumerState<AppShell> {
  StreamSubscription? _notifSub;
  StreamSubscription? _msgSub;

  static const _tabs = [
    _Tab(icon: Icons.home_outlined, activeIcon: Icons.home_rounded, label: 'Home', route: '/'),
    _Tab(icon: Icons.calendar_month_outlined, activeIcon: Icons.calendar_month_rounded, label: 'Timetable', route: '/timetable'),
    _Tab(icon: Icons.class_outlined, activeIcon: Icons.class_rounded, label: 'MyClass', route: '/my-class'),
    _Tab(icon: Icons.insights_outlined, activeIcon: Icons.insights_rounded, label: 'Analytics', route: '/analytics'),
    _Tab(icon: Icons.grid_view_outlined, activeIcon: Icons.grid_view_rounded, label: 'More', route: '/more'),
  ];

  @override
  void initState() {
    super.initState();
    _notifSub = newNotificationStreamController.stream.listen((notif) {
      if (mounted) {
        NotificationToast.show(
          context,
          title: notif.title,
          body: notif.body,
          onTap: () {
            if (GoRouterState.of(context).uri.toString() != '/notifications') {
              context.push('/notifications');
            }
          },
        );
      }
    });

    _msgSub = newMessageStreamController.stream.listen((msg) {
      if (mounted) {
        ChatMessageToast.show(
          context,
          ref: ref,
          message: msg,
          onTap: () {
            final courseCode = msg.courseCode;
            context.push('/course/$courseCode/channels/${msg.channelId}/messages');
          },
        );
      }
    });
  }

  @override
  void dispose() {
    _notifSub?.cancel();
    _msgSub?.cancel();
    super.dispose();
  }

  int _selectedIndex(BuildContext context) {
    final location = GoRouterState.of(context).uri.toString();
    for (int i = 0; i < _tabs.length; i++) {
      if (location == _tabs[i].route) return i;
      if (i > 0 && location.startsWith(_tabs[i].route)) return i;
    }
    return 0;
  }

  @override
  Widget build(BuildContext context) {
    final selectedIndex = _selectedIndex(context);
    final unreadCount = ref.watch(unreadCountProvider);

    return Scaffold(
      backgroundColor: AppTheme.backgroundDark,
      body: LayoutBuilder(
        builder: (context, constraints) => Stack(
          children: [
            widget.child,
            FloatingChatButton(bodySize: constraints.biggest),
          ],
        ),
      ),
      bottomNavigationBar: Container(
        decoration: const BoxDecoration(
          border: Border(
            top: BorderSide(color: AppTheme.divider, width: 1),
          ),
        ),
        child: NavigationBar(
          selectedIndex: selectedIndex,
          onDestinationSelected: (i) => context.go(_tabs[i].route),
          destinations: _tabs.map((t) {
            final isMore = t.route == '/more';
            final showBadge = isMore && unreadCount > 0;
            return NavigationDestination(
              icon: showBadge
                  ? Badge(
                      smallSize: 8,
                      backgroundColor: AppTheme.danger,
                      child: Icon(t.icon),
                    )
                  : Icon(t.icon),
              selectedIcon: showBadge
                  ? Badge(
                      smallSize: 8,
                      backgroundColor: AppTheme.danger,
                      child: Icon(t.activeIcon),
                    )
                  : Icon(t.activeIcon),
              label: t.label,
            );
          }).toList(),
        ),
      ),
    );
  }
}

class _Tab {
  final IconData icon;
  final IconData activeIcon;
  final String label;
  final String route;
  const _Tab({
    required this.icon,
    required this.activeIcon,
    required this.label,
    required this.route,
  });
}
