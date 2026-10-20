import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../core/constants.dart';
import '../core/theme.dart';
import '../services/history_service.dart';
import '../services/locale_service.dart';
import 'result_screen.dart';

class HistoryScreen extends StatelessWidget {
  final Function(int tabIndex)? onNavigateTab;

  const HistoryScreen({super.key, this.onNavigateTab});

  Color _getStatusColor(String status) {
    switch (status) {
      case 'Healthy':
        return AppTheme.primaryGreen;
      case 'Suspected':
        return AppTheme.amberWarning;
      case 'Unsure':
      default:
        return const Color(0xFF757575);
    }
  }

  @override
  Widget build(BuildContext context) {
    final historyService = context.watch<HistoryService>();
    final locale = context.watch<LocaleService>();
    final history = historyService.history;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Scan History'),
        actions: [
          if (history.isNotEmpty)
            IconButton(
              icon: const Icon(Icons.delete_outline),
              tooltip: 'Clear history',
              onPressed: () async {
                final confirm = await showDialog<bool>(
                  context: context,
                  builder: (ctx) => AlertDialog(
                    title: const Text('Clear Scan History?'),
                    content: const Text(
                      'This will remove all saved scans stored on this device. (Max 8 scans are kept locally).',
                    ),
                    actions: [
                      TextButton(
                        onPressed: () => Navigator.pop(ctx, false),
                        child: const Text('Cancel'),
                      ),
                      TextButton(
                        onPressed: () => Navigator.pop(ctx, true),
                        child: const Text('Clear', style: TextStyle(color: Colors.red)),
                      ),
                    ],
                  ),
                );
                if (confirm == true) {
                  await historyService.clearHistory();
                }
              },
            ),
        ],
      ),
      body: history.isEmpty
          ? Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.history_toggle_off, size: 64, color: Colors.grey.shade400),
                  const SizedBox(height: 12),
                  Text(
                    'No scan history yet',
                    style: TextStyle(fontSize: 16, color: Colors.grey.shade600),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    'Up to 8 recent scans will be stored locally on your device.',
                    style: TextStyle(fontSize: 13, color: Colors.grey.shade500),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton.icon(
                    icon: const Icon(Icons.camera_alt),
                    label: const Text('Start First Scan'),
                    onPressed: () => onNavigateTab?.call(0),
                  ),
                ],
              ),
            )
          : ListView.builder(
              padding: const EdgeInsets.symmetric(vertical: 8),
              itemCount: history.length,
              itemBuilder: (ctx, index) {
                final item = history[index];
                final statusColor = _getStatusColor(item.status);
                final formattedDate =
                    DateFormat('MMM d, yyyy • h:mm a').format(item.timestamp);
                final displayClass =
                    AppConstants.getDisplayClassName(item.predictedClass, locale.currentLanguage);

                return Card(
                  child: ListTile(
                    contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                    leading: ClipRRect(
                      borderRadius: BorderRadius.circular(8),
                      child: Container(
                        width: 54,
                        height: 54,
                        color: Colors.grey.shade200,
                        child: item.camImageBase64 != null
                            ? Image.memory(
                                base64Decode(item.camImageBase64!),
                                fit: BoxFit.cover,
                              )
                            : item.originalImageBase64 != null
                                ? Image.memory(
                                    base64Decode(item.originalImageBase64!),
                                    fit: BoxFit.cover,
                                  )
                                : const Icon(Icons.image, color: Colors.grey),
                      ),
                    ),
                    title: Text(
                      displayClass,
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                    ),
                    subtitle: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const SizedBox(height: 4),
                        Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                              decoration: BoxDecoration(
                                color: statusColor.withValues(alpha: 0.15),
                                borderRadius: BorderRadius.circular(4),
                              ),
                              child: Text(
                                item.status.toUpperCase(),
                                style: TextStyle(
                                  fontSize: 11,
                                  fontWeight: FontWeight.bold,
                                  color: statusColor,
                                ),
                              ),
                            ),
                            const SizedBox(width: 8),
                            Text(
                              '${(item.confidence * 100).toStringAsFixed(1)}%',
                              style: TextStyle(fontSize: 12, color: Colors.grey.shade700),
                            ),
                          ],
                        ),
                        const SizedBox(height: 4),
                        Text(
                          formattedDate,
                          style: TextStyle(fontSize: 11, color: Colors.grey.shade500),
                        ),
                      ],
                    ),
                    trailing: const Icon(Icons.chevron_right, color: Colors.grey),
                    onTap: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (ctx) => ResultScreen(
                            result: item,
                            onAskAboutResult: (cls) {
                              Navigator.pop(ctx);
                              onNavigateTab?.call(2);
                            },
                          ),
                        ),
                      );
                    },
                  ),
                );
              },
            ),
    );
  }
}
