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
                    return ListTile(
                      leading: Icon(
                        channel.type == 'announcement' ? Icons.campaign : Icons.forum,
                      ),
                      title: Text(channel.name),
                      subtitle: Text(channel.type),
                      onTap: () {
                        context.go(
                          '/course/${course.courseCode}/channels/${channel.id}/messages'
                          '?name=${Uri.encodeComponent(channel.name)}',
                        );
                      },
                    );
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