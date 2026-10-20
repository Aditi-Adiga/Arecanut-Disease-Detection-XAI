class SourceItem {
  final String id;
  final String title;
  final String publisher;
  final String year;
  final String url;

  SourceItem({
    required this.id,
    required this.title,
    required this.publisher,
    required this.year,
    required this.url,
  });

  factory SourceItem.fromJson(Map<String, dynamic> json) {
    return SourceItem(
      id: json['id'] as String? ?? '',
      title: json['title'] as String? ?? '',
      publisher: json['publisher'] as String? ?? '',
      year: json['year']?.toString() ?? '',
      url: json['url'] as String? ?? '',
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'title': title,
    'publisher': publisher,
    'year': year,
    'url': url,
  };
}

class SuggestionItem {
  final String id;
  final String question;

  SuggestionItem({required this.id, required this.question});

  factory SuggestionItem.fromJson(Map<String, dynamic> json) {
    return SuggestionItem(
      id: json['id'] as String? ?? '',
      question: json['question'] as String? ?? '',
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'question': question,
  };
}

class ChatMessage {
  final String id;
  final String role; // 'user' | 'assistant'
  final String text;
  final List<SourceItem> sources;
  final bool needsExpertReview;
  final bool languageFallback;
  final bool aiGenerated;
  final String answerSource; // 'guide' | 'ai'
  final List<SuggestionItem> suggestions;
  final String? entryId;
  final DateTime timestamp;

  ChatMessage({
    required this.id,
    required this.role,
    required this.text,
    this.sources = const [],
    this.needsExpertReview = false,
    this.languageFallback = false,
    this.aiGenerated = false,
    this.answerSource = 'guide',
    this.suggestions = const [],
    this.entryId,
    DateTime? timestamp,
  }) : timestamp = timestamp ?? DateTime.now();

  factory ChatMessage.fromJson(Map<String, dynamic> json) {
    final rawSources = json['sources'] as List<dynamic>? ?? [];
    final sources = rawSources
        .map((s) => s is Map<String, dynamic> ? SourceItem.fromJson(s) : null)
        .whereType<SourceItem>()
        .toList();

    final rawSuggestions = json['suggestions'] as List<dynamic>? ?? [];
    final suggestions = rawSuggestions
        .map((s) => s is Map<String, dynamic> ? SuggestionItem.fromJson(s) : null)
        .whereType<SuggestionItem>()
        .toList();

    return ChatMessage(
      id: json['id'] as String? ?? DateTime.now().millisecondsSinceEpoch.toString(),
      role: json['role'] as String? ?? 'assistant',
      text: json['text'] as String? ?? json['answer'] as String? ?? '',
      sources: sources,
      needsExpertReview: json['needs_expert_review'] as bool? ?? false,
      languageFallback: json['language_fallback'] as bool? ?? false,
      aiGenerated: json['ai_generated'] as bool? ?? false,
      answerSource: json['answer_source'] as String? ?? 'guide',
      suggestions: suggestions,
      entryId: json['entry_id'] as String?,
      timestamp: json['timestamp'] != null
          ? DateTime.parse(json['timestamp'] as String)
          : DateTime.now(),
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'role': role,
    'text': text,
    'sources': sources.map((s) => s.toJson()).toList(),
    'needs_expert_review': needsExpertReview,
    'language_fallback': languageFallback,
    'ai_generated': aiGenerated,
    'answer_source': answerSource,
    'suggestions': suggestions.map((s) => s.toJson()).toList(),
    'entry_id': entryId,
    'timestamp': timestamp.toIso8601String(),
  };
}
