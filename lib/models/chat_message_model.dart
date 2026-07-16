class ToolCallInfo {
  final String name;
  final String displayLabel;

  const ToolCallInfo({required this.name, required this.displayLabel});
}

const Map<String, String> kToolDisplayLabels = {
  'get_student_profile': 'Looking up your profile...',
  'get_assignments': 'Checking your assignments...',
  'get_schedule': 'Looking up your schedule...',
  'get_study_plan': 'Reviewing your study plan...',
  'update_study_plan': 'Updating your study plan...',
  'create_reminder': 'Creating a reminder...',
  'mark_assignment_complete': 'Marking assignment complete...',
  'save_study_note': 'Saving a study note...',
  'get_knowledge_state': 'Checking your knowledge state...',
  'update_knowledge_state': 'Updating knowledge state...',
  'get_resources': 'Finding learning resources...',
  'break_down_assignment': 'Breaking down assignment...',
  'get_assignment_milestones': 'Loading milestones...',
  'update_milestone_status': 'Updating milestone...',
  'get_course_recommendations': 'Checking course recommendations...',
};

class ChatMessage {
  final String id;
  final String role;
  final String content;
  final String reasoning;
  final bool isThinkingDone;
  final List<ToolCallInfo> toolCalls;
  final DateTime timestamp;
  final bool isLoading;

  const ChatMessage({
    required this.id,
    required this.role,
    required this.content,
    this.reasoning = '',
    this.isThinkingDone = false,
    this.toolCalls = const [],
    required this.timestamp,
    this.isLoading = false,
  });

  bool get isUser => role == 'user';

  ChatMessage copyWith({
    String? content,
    String? reasoning,
    bool? isThinkingDone,
    List<ToolCallInfo>? toolCalls,
    bool? isLoading,
  }) =>
      ChatMessage(
        id: id,
        role: role,
        content: content ?? this.content,
        reasoning: reasoning ?? this.reasoning,
        isThinkingDone: isThinkingDone ?? this.isThinkingDone,
        toolCalls: toolCalls ?? this.toolCalls,
        timestamp: timestamp,
        isLoading: isLoading ?? this.isLoading,
      );

  Map<String, dynamic> toJson() => {'role': role, 'content': content};
}
