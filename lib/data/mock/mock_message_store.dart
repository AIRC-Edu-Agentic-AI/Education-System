import 'package:student_agent/data/mock/mock_data.dart';
import 'package:student_agent/models/course_model.dart';

class MockMessageStore {
  static final Map<String, List<CourseMessage>> _posted = {};

  static List<CourseMessage> allFor(String channelId, {String? parentId}) {
    final all = [
      ...MockData.seedMessagesFor(channelId),
      ...(_posted[channelId] ?? []),
    ];

    final filtered = all.where((m) {
      if (parentId == null) {
        return m.parentId == null || m.parentId!.isEmpty;
      }
      return m.parentId == parentId;
    }).toList().cast<CourseMessage>(); 

    filtered.sort((a, b) => a.createdAt.compareTo(b.createdAt));
    return filtered;
  }

  static void add(CourseMessage msg) {
    _posted.putIfAbsent(msg.channelId, () => []).add(msg);
  }

  static int replyCount(String channelId, String parentId) {
    return allFor(channelId, parentId: parentId).length;
  }

  /// mock_DATA201_announcement -> DATA201
  static String courseCodeFromChannelId(String channelId) {
    if (!channelId.startsWith('mock_')) return '';
    final body = channelId.substring(5);
    final idx = body.lastIndexOf('_');
    return idx > 0 ? body.substring(0, idx) : body;
  }
}