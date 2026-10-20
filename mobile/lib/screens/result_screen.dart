import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/constants.dart';
import '../core/theme.dart';
import '../models/screening_result.dart';
import '../services/locale_service.dart';

class ResultScreen extends StatefulWidget {
  final ScreeningResult result;
  final Function(String predictedClass)? onAskAboutResult;

  const ResultScreen({
    super.key,
    required this.result,
    this.onAskAboutResult,
  });

  @override
  State<ResultScreen> createState() => _ResultScreenState();
}

class _ResultScreenState extends State<ResultScreen> {
  bool _showCamOverlay = true;

  Color _getStatusColor(String status) {
    switch (status) {
      case 'Healthy':
        return AppTheme.primaryGreen;
      case 'Suspected':
        return AppTheme.amberWarning;
      case 'Unsure':
      default:
        return const Color(0xFF616161);
    }
  }

  IconData _getStatusIcon(String status) {
    switch (status) {
      case 'Healthy':
        return Icons.check_circle_outline;
      case 'Suspected':
        return Icons.warning_amber_rounded;
      case 'Unsure':
      default:
        return Icons.help_outline;
    }
  }

  @override
  Widget build(BuildContext context) {
    final locale = context.watch<LocaleService>();
    final r = widget.result;
    final statusColor = _getStatusColor(r.status);
    final statusIcon = _getStatusIcon(r.status);
    final displayClass = AppConstants.getDisplayClassName(r.predictedClass, locale.currentLanguage);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Screening Result'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Status Banner Card
            Card(
              elevation: 2,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
                side: BorderSide(color: statusColor, width: 2),
              ),
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(statusIcon, color: statusColor, size: 28),
                        const SizedBox(width: 8),
                        Text(
                          r.status == 'Healthy'
                              ? 'HEALTHY'
                              : r.status == 'Suspected'
                                  ? 'SUSPECTED CONDITION'
                                  : 'RESULT UNSURE',
                          style: TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                            color: statusColor,
                            letterSpacing: 0.5,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text(
                      displayClass,
                      style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Relative Score: ${(r.confidence * 100).toStringAsFixed(1)}%',
                      style: TextStyle(fontSize: 14, color: Colors.grey.shade700),
                    ),
                    const SizedBox(height: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                      decoration: BoxDecoration(
                        color: Colors.grey.shade100,
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: const Text(
                        'Screening aid only. Never a confirmed diagnosis. Please confirm with your agricultural officer or KVK.',
                        style: TextStyle(fontSize: 12, color: AppTheme.textMuted),
                        textAlign: TextAlign.center,
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // CAM Heatmap / Image Visualizer Card
            if (r.camImageBase64 != null) ...[
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(14),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Text(
                            'Class Activation Map (CAM)',
                            style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold),
                          ),
                          Row(
                            children: [
                              const Text('Overlay', style: TextStyle(fontSize: 13)),
                              Switch(
                                value: _showCamOverlay,
                                activeThumbColor: AppTheme.primaryGreen,
                                onChanged: (val) {
                                  setState(() {
                                    _showCamOverlay = val;
                                  });
                                },
                              ),
                            ],
                          ),
                        ],
                      ),
                      const SizedBox(height: 6),
                      Text(
                        'Warm regions (red/yellow) highlight areas of the image that contributed most to this screening prediction.',
                        style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
                      ),
                      const SizedBox(height: 12),
                      Center(
                        child: ClipRRect(
                          borderRadius: BorderRadius.circular(8),
                          child: Container(
                            height: 220,
                            color: Colors.black12,
                            child: _showCamOverlay
                                ? Image.memory(
                                    base64Decode(r.camImageBase64!),
                                    fit: BoxFit.contain,
                                  )
                                : r.originalImageBase64 != null
                                    ? Image.memory(
                                        base64Decode(r.originalImageBase64!),
                                        fit: BoxFit.contain,
                                      )
                                    : Image.memory(
                                        base64Decode(r.camImageBase64!),
                                        fit: BoxFit.contain,
                                      ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
            ],

            // Relative Scores Breakdown
            Card(
              child: Padding(
                padding: const EdgeInsets.all(14),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Relative Model Scores',
                      style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Scores are relative comparison values across categories, not probabilities of disease presence.',
                      style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
                    ),
                    const SizedBox(height: 12),
                    ...AppConstants.classes.map((cls) {
                      final score = r.scores[cls] ?? 0.0;
                      final isTop = cls == r.predictedClass;
                      return Padding(
                        padding: const EdgeInsets.only(bottom: 8),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Text(
                                  AppConstants.getDisplayClassName(cls, locale.currentLanguage),
                                  style: TextStyle(
                                    fontSize: 13,
                                    fontWeight: isTop ? FontWeight.bold : FontWeight.normal,
                                    color: isTop ? AppTheme.primaryGreen : Colors.black87,
                                  ),
                                ),
                                Text(
                                  '${(score * 100).toStringAsFixed(1)}%',
                                  style: TextStyle(
                                    fontSize: 13,
                                    fontWeight: isTop ? FontWeight.bold : FontWeight.normal,
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 4),
                            LinearProgressIndicator(
                              value: score.clamp(0.0, 1.0),
                              backgroundColor: Colors.grey.shade200,
                              color: isTop ? AppTheme.primaryGreen : Colors.grey.shade400,
                              minHeight: 6,
                            ),
                          ],
                        ),
                      );
                    }),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Agricultural Guidance Card
            if (r.summaryText.isNotEmpty || r.whatToDo.isNotEmpty) ...[
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(14),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: const [
                          Icon(Icons.menu_book, color: AppTheme.primaryGreen, size: 20),
                          SizedBox(width: 8),
                          Text(
                            'Field Guidance (ICAR-CPCRI)',
                            style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold),
                          ),
                        ],
                      ),
                      if (r.summaryText.isNotEmpty) ...[
                        const SizedBox(height: 8),
                        Text(
                          r.summaryText,
                          style: TextStyle(fontSize: 13.5, color: Colors.grey.shade800),
                        ),
                      ],
                      if (r.whatToDo.isNotEmpty) ...[
                        const SizedBox(height: 12),
                        const Text(
                          'Recommended Next Steps:',
                          style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
                        ),
                        const SizedBox(height: 6),
                        ...r.whatToDo.map(
                          (item) => Padding(
                            padding: const EdgeInsets.only(bottom: 6),
                            child: Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text('• ', style: TextStyle(fontWeight: FontWeight.bold)),
                                Expanded(
                                  child: Text(
                                    item,
                                    style: TextStyle(fontSize: 13, color: Colors.grey.shade800),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ],
                      if (r.limitsText != null && r.limitsText!.isNotEmpty) ...[
                        const SizedBox(height: 8),
                        Container(
                          padding: const EdgeInsets.all(8),
                          decoration: BoxDecoration(
                            color: Colors.amber.shade50,
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: Text(
                            r.limitsText!,
                            style: TextStyle(fontSize: 12, color: Colors.amber.shade900),
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
            ],

            // Action Button: Ask about this result
            ElevatedButton.icon(
              icon: const Icon(Icons.chat_bubble_outline),
              label: Text('Ask about ${AppConstants.getDisplayClassName(r.predictedClass, locale.currentLanguage)}'),
              onPressed: () {
                widget.onAskAboutResult?.call(r.predictedClass);
              },
            ),
          ],
        ),
      ),
    );
  }
}
