import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:student_agent/providers/auth_provider.dart';
import 'package:student_agent/screens/auth/login_screen.dart';
import 'package:student_agent/screens/chat/chat_screen.dart';
import 'package:student_agent/screens/dashboard/dashboard_screen.dart';
import 'package:student_agent/screens/study_plan/study_plan_screen.dart';
import 'package:student_agent/screens/timetable/timetable_screen.dart';
import 'package:student_agent/screens/my_class/my_class_screen.dart';
import 'package:student_agent/screens/my_enrollment/my_enrollment_screen.dart';
import 'package:student_agent/screens/resource_center/resource_center_screen.dart';
import 'package:student_agent/screens/analytics/analytics_screen.dart';
import 'package:student_agent/screens/profile/profile_screen.dart';
import 'package:student_agent/screens/more/more_screen.dart';
import 'package:student_agent/screens/notifications/notifications_screen.dart';
import 'package:student_agent/widgets/app_shell.dart';

import 'package:student_agent/screens/course_communication/course_channels_screen.dart';
import 'package:student_agent/screens/course_communication/course_channel_messages_screen.dart';

final routerProvider = Provider<GoRouter>((ref) {
  final authNotifier = ref.read(authNotifierProvider);

  return GoRouter(
    initialLocation: '/login',
    refreshListenable: authNotifier,
    redirect: (context, state) {
      final auth = authNotifier.state;
      final initialized = authNotifier.initialized;
      final isLoginRoute = state.matchedLocation == '/login';

      if (!initialized) return null;

      if (!auth.isAuthenticated && !isLoginRoute) return '/login';
      if (auth.isAuthenticated && isLoginRoute) return '/';
      return null;
    },
    routes: [
      // Standalone routes (no bottom nav shell)
      GoRoute(path: '/login', builder: (ctx, state) => const LoginScreen()),
      GoRoute(path: '/chat', builder: (ctx, state) => const ChatScreen()),
      GoRoute(path: '/profile', builder: (ctx, state) => const ProfileScreen()),
      GoRoute(
          path: '/notifications',
          builder: (ctx, state) => const NotificationsScreen()),

      // Shell routes (bottom nav + floating chat button)
      ShellRoute(
        builder: (ctx, state, child) => AppShell(child: child),
        routes: [
          GoRoute(path: '/', builder: (ctx, state) => const DashboardScreen()),
          GoRoute(path: '/timetable', builder: (ctx, state) => const TimetableScreen()),
          GoRoute(path: '/study-plan', builder: (ctx, state) => const StudyPlanScreen()),
          GoRoute(path: '/analytics', builder: (ctx, state) => const AnalyticsScreen()),
          GoRoute(path: '/more', builder: (ctx, state) => const MoreScreen()),
          GoRoute(path: '/my-class', builder: (ctx, state) => const MyClassScreen()),
          GoRoute(path: '/my-enrollment', builder: (ctx, state) => const MyEnrollmentScreen()),
          GoRoute(path: '/resources', builder: (ctx, state) => const ResourceCenterScreen()),
          GoRoute(
            path: '/course/:courseCode/channels',
            builder: (ctx, state) => const CourseChannelsScreen(),
            routes: [
              GoRoute(
                path: ':channelId/messages', // Đuôi path nối tiếp, không cần lặp lại đoạn của cha
                builder: (ctx, state) => CourseChannelMessagesScreen(
                  courseCode: state.pathParameters['courseCode']!, // Vẫn lấy được tham số của cha
                  channelId: state.pathParameters['channelId']!,
                  channelName: state.uri.queryParameters['name'],
                ),
              ),
            ],
          ),
        ],
      ),
    ],
  );
});
