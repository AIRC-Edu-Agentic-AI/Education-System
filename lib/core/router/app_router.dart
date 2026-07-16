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
import 'package:student_agent/screens/study_groups/study_groups_screen.dart';
import 'package:student_agent/screens/study_groups/group_chat_screen.dart';
import 'package:student_agent/screens/study_groups/group_detail_screen.dart';
import 'package:student_agent/screens/course_communication/course_channels_screen.dart';
import 'package:student_agent/screens/course_communication/course_channel_messages_screen.dart';
import 'package:student_agent/screens/my_class/course_detail_screen.dart';
import 'package:student_agent/screens/my_class/assignment_detail_screen.dart';

final routerProvider = Provider<GoRouter>((ref) {
  final authNotifier = ref.read(authNotifierProvider);

  return GoRouter(
    initialLocation: '/login',
    refreshListenable: authNotifier,
    debugLogDiagnostics: true,
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
      // ── AUTH ROUTES ──
      GoRoute(
        path: '/login',
        builder: (ctx, state) => const LoginScreen(),
      ),

      // ── STANDALONE ROUTES (KHÔNG có bottom nav) ──
      GoRoute(
        path: '/chat',
        builder: (ctx, state) => const ChatScreen(),
      ),
      GoRoute(
        path: '/profile',
        builder: (ctx, state) => const ProfileScreen(),
      ),
      GoRoute(
        path: '/notifications',
        builder: (ctx, state) => const NotificationsScreen(),
      ),


      GoRoute(
        path: '/study-groups',
        builder: (ctx, state) => const StudyGroupsScreen(),
      ),
      GoRoute(
        path: '/study-group/:groupId',
        builder: (ctx, state) {
          final groupId = state.pathParameters['groupId']!;
          return GroupChatScreen(groupId: groupId);
        },
      ),
      GoRoute(
        path: '/study-group-detail/:groupId',
        builder: (ctx, state) {
          final groupId = state.pathParameters['groupId']!;
          return GroupDetailScreen(groupId: groupId);
        },
      ),


      GoRoute(
        path: '/course/:courseCode/channels',
        builder: (ctx, state) {
          final courseCode = state.pathParameters['courseCode']!;
          return CourseChannelsScreen();
        },
        routes: [
          GoRoute(
            path: ':channelId/messages',
            builder: (ctx, state) {
              final courseCode = state.pathParameters['courseCode']!;
              final channelId = state.pathParameters['channelId']!;
              final channelName = state.uri.queryParameters['name'];
              final channelType = state.uri.queryParameters['type'];
              final returnTo = state.uri.queryParameters['returnTo'];
              
              return CourseChannelMessagesScreen(
                courseCode: courseCode,
                channelId: channelId,
                channelName: channelName,
                channelType: channelType,
                returnTo: returnTo,
              );
            },
          ),
        ],
      ),

      ShellRoute(
        builder: (ctx, state, child) => AppShell(child: child),
        routes: [
          GoRoute(
            path: '/',
            builder: (ctx, state) => const DashboardScreen(),
          ),
          GoRoute(
            path: '/timetable',
            builder: (ctx, state) => const TimetableScreen(),
          ),
          GoRoute(
            path: '/study-plan',
            builder: (ctx, state) => const StudyPlanScreen(),
          ),
          GoRoute(
            path: '/analytics',
            builder: (ctx, state) => const AnalyticsScreen(),
          ),
          GoRoute(
            path: '/more',
            builder: (ctx, state) => const MoreScreen(),
          ),
          
          GoRoute(
            path: '/my-class',
            builder: (ctx, state) => const MyClassScreen(),
            routes: [
              // ── Course Detail ──
              GoRoute(
                path: ':courseCode',
                builder: (ctx, state) {
                  final courseCode = state.pathParameters['courseCode']!;
                  return CourseDetailScreen(courseCode: courseCode);
                },
                routes: [
                  // ── Assignments List ──
                  GoRoute(
                    path: 'assignments',
                    builder: (ctx, state) {
                      final courseCode = state.pathParameters['courseCode']!;
                      return CourseAssignmentsScreen(courseCode: courseCode);
                    },
                    routes: [
                      // ── Assignment Detail ──
                      GoRoute(
                        path: ':assessmentId',
                        builder: (ctx, state) {
                          final courseCode = state.pathParameters['courseCode']!;
                          final assessmentId = int.parse(
                            state.pathParameters['assessmentId']!,
                          );
                          return AssignmentDetailScreen(
                            courseCode: courseCode,
                            assessmentId: assessmentId,
                          );
                        },
                      ),
                    ],
                  ),
                  // ── Grades ──
                  GoRoute(
                    path: 'grades',
                    builder: (ctx, state) {
                      final courseCode = state.pathParameters['courseCode']!;
                      return CourseGradesScreen(courseCode: courseCode);
                    },
                  ),
                  // ── Progress ──
                  GoRoute(
                    path: 'progress',
                    builder: (ctx, state) {
                      final courseCode = state.pathParameters['courseCode']!;
                      return CourseProgressScreen(courseCode: courseCode);
                    },
                  ),
                  // ── Exams ──
                  GoRoute(
                    path: 'exams',
                    builder: (ctx, state) {
                      final courseCode = state.pathParameters['courseCode']!;
                      return CourseExamsScreen(courseCode: courseCode);
                    },
                  ),
                ],
              ),
            ],
          ),
          
          GoRoute(
            path: '/my-enrollment',
            builder: (ctx, state) => const MyEnrollmentScreen(),
          ),
          GoRoute(
            path: '/resources',
            builder: (ctx, state) => const ResourceCenterScreen(),
          ),
        ],
      ),
    ],
  );
});