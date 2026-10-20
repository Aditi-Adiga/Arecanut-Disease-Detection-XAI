import '../core/constants.dart';

class ScreeningResult {
  final String id;
  final String predictedClass;
  final double confidence;
  final String status; // 'Healthy' | 'Suspected' | 'Unsure'
  final Map<String, double> scores;
  final String? camImageBase64;
  final String? originalImageBase64;
  final String summaryText;
  final List<String> whatToDo;
  final String? limitsText;
  final List<String> sourceIds;
  final DateTime timestamp;
  final bool isOffline;

  ScreeningResult({
    required this.id,
    required this.predictedClass,
    required this.confidence,
    required this.status,
    required this.scores,
    this.camImageBase64,
    this.originalImageBase64,
    required this.summaryText,
    required this.whatToDo,
    this.limitsText,
    required this.sourceIds,
    required this.timestamp,
    this.isOffline = false,
  });

  factory ScreeningResult.fromJson(Map<String, dynamic> json) {
    final rawScores = json['scores'] as Map<String, dynamic>? ?? {};
    final scores = rawScores.map((k, v) => MapEntry(k, (v as num).toDouble()));

    final predicted = json['predicted_class'] as String? ?? 'Yellow_Leaf';
    final conf = (json['confidence'] as num?)?.toDouble() ?? 0.0;
    final status = json['status'] as String? ??
        AppConstants.computeStatus(predicted, conf);

    final whatToDoRaw = json['what_to_do'] as List<dynamic>? ?? [];
    final whatToDoList = whatToDoRaw.map((e) {
      if (e is Map<String, dynamic>) {
        return e['text'] as String? ?? '';
      }
      return e.toString();
    }).where((s) => s.isNotEmpty).toList();

    final sourcesRaw = json['sources'] as List<dynamic>? ?? [];
    final sourceIds = sourcesRaw.map((e) {
      if (e is Map<String, dynamic>) {
        return e['id'] as String? ?? '';
      }
      return e.toString();
    }).where((s) => s.isNotEmpty).toList();

    return ScreeningResult(
      id: json['id'] as String? ?? DateTime.now().millisecondsSinceEpoch.toString(),
      predictedClass: predicted,
      confidence: conf,
      status: status,
      scores: scores,
      camImageBase64: json['cam_image_base64'] as String?,
      originalImageBase64: json['original_image_base64'] as String?,
      summaryText: json['summary_text'] as String? ??
          (json['summary'] is Map ? json['summary']['text'] : '') ?? '',
      whatToDo: whatToDoList,
      limitsText: json['limits_text'] as String? ??
          (json['limits'] is Map ? json['limits']['text'] : null),
      sourceIds: sourceIds,
      timestamp: json['timestamp'] != null
          ? DateTime.parse(json['timestamp'] as String)
          : DateTime.now(),
      isOffline: json['is_offline'] as bool? ?? false,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'predicted_class': predictedClass,
      'confidence': confidence,
      'status': status,
      'scores': scores,
      'cam_image_base64': camImageBase64,
      'original_image_base64': originalImageBase64,
      'summary_text': summaryText,
      'what_to_do': whatToDo,
      'limits_text': limitsText,
      'sources': sourceIds,
      'timestamp': timestamp.toIso8601String(),
      'is_offline': isOffline,
    };
  }
}
