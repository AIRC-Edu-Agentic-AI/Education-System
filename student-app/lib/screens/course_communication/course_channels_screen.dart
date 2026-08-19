import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../models/course_model.dart';
import '../../providers/providers.dart';

import 'package:go_router/go_router.dart';

class CourseChannelsScreen extends ConsumerWidget {
  const CourseChannelsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final coursesAsync = ref.watch(studentCoursesProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Course Communication'),
      ),
      body: coursesAsync.when(
        loading: () =>
            const Center(child: CircularProgressIndicator()),
        error: (e, _) =>
            Center(child: Text('Error: $e')),
        data: (courses) {
          if (courses.isEmpty) {
            return const Center(
              child: Text('No courses found'),
            );
          }

          return ListView.builder(
            itemCount: courses.length,
            itemBuilder: (context, index) {
              final course = courses[index];

              return _CourseCard(course: course);
            },
          );
        },
      ),
    );
  }
}

class _CourseCard extends ConsumerWidget {
  final CourseModel course;

  const _CourseCard({
    required this.course,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final channelsAsync =
        ref.watch(courseChannelsProvider(course.courseCode));

    return Card(
      margin: const EdgeInsets.all(12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              course.title,
              style: const TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),

            const SizedBox(height: 4),

            Text(course.courseCode),

            const SizedBox(height: 12),

            channelsAsync.when(
              loading: () =>
                  const CircularProgressIndicator(),
              error: (e, _) =>
                  Text('Error: $e'),
              data: (channels) {
                if (channels.isEmpty) {
                  return const Text('No channels');
                }

                return Column(
                  children: channels.map((channel) {
                    return _ChannelTile(course: course, channel: channel);
                  }).toList(),
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}

class _ChannelTile extends ConsumerWidget {
  final CourseModel course;
  final CourseChannel channel;

  const _ChannelTile({
    required this.course,
    required this.channel,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isAnnouncement = channel.type == 'announcement';
    final unreadCount = isAnnouncement
        ? ref.watch(courseUnreadAnnouncementsCountProvider(course.courseCode))
        : ref.watch(channelUnreadCountProvider(channel.id));

    return ListTile(
      leading: Stack(
        clipBehavior: Clip.none,
        children: [
          Icon(
            isAnnouncement ? Icons.campaign : Icons.forum,
            color: isAnnouncement ? const Color(0xFFF59E0B) : const Color(0xFF38BDF8),
          ),
          if (unreadCount > 0)
            Positioned(
              right: -4,
              top: -4,
              child: Container(
                width: 8,
                height: 8,
                decoration: const BoxDecoration(
                  color: Color(0xFFEF4444),
                  shape: BoxShape.circle,
                ),
              ),
            ),
        ],
      ),
      title: Text(
        channel.name,
        style: TextStyle(
          fontWeight: unreadCount > 0 ? FontWeight.bold : FontWeight.w500,
        ),
      ),
      subtitle: Text(channel.type),
      trailing: unreadCount > 0
          ? Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
              decoration: BoxDecoration(
                color: const Color(0xFFEF4444),
                borderRadius: BorderRadius.circular(12),
                boxShadow: [
                  BoxShadow(
                    color: const Color(0xFFEF4444).withValues(alpha: 0.4),
                    blurRadius: 6,
                    offset: const Offset(0, 2),
                  ),
                ],
              ),
              child: Text(
                unreadCount > 99 ? '99+' : '$unreadCount',
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 11,
                  fontWeight: FontWeight.bold,
                ),
              ),
            )
          : const Icon(Icons.chevron_right_rounded),
      onTap: () {
        ref.read(channelReadStateProvider.notifier).markChannelRead(channel.id);
        if (isAnnouncement) {
          final notifs = ref.read(courseNotificationsProvider(course.courseCode)).value ?? [];
          for (final n in notifs.where((item) => !item.read)) {
            ref.read(notificationProvider.notifier).markRead(n.id);
          }
        }
        context.go(
          '/course/${course.courseCode}/channels/${channel.id}/messages'
          '?name=${Uri.encodeComponent(channel.name)}'
          '&type=${Uri.encodeComponent(channel.type)}',
        );
      },
    );
  }
}