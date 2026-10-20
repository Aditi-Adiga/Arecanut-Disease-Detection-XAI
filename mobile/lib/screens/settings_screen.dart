import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/constants.dart';
import '../core/theme.dart';
import '../services/api_service.dart';
import '../services/chat_history_service.dart';
import '../services/history_service.dart';
import '../services/locale_service.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  late TextEditing4EditingController _urlController;
  bool _isTesting = false;
  String? _testStatus;

  @override
  void initState() {
    super.initState();
    final api = context.read<ApiService>();
    _urlController = TextEditing4EditingController(text: api.baseUrl);
  }

  @override
  void dispose() {
    _urlController.dispose();
    super.dispose();
  }

  Future<void> _testConnection() async {
    setState(() {
      _isTesting = true;
      _testStatus = null;
    });

    final api = context.read<ApiService>();
    await api.setBaseUrl(_urlController.text);

    final isHealthy = await api.checkHealth();
    final isOnlineChat = await api.checkOnlineChatEnabled();

    setState(() {
      _isTesting = false;
      if (isHealthy) {
        _testStatus = isOnlineChat
            ? 'Connected successfully! (Backend is online, LLM proxy active)'
            : 'Connected successfully! (Backend is online, offline chat mode)';
      } else {
        _testStatus =
            'Could not reach server at ${_urlController.text}. Please check host and port.';
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final locale = context.watch<LocaleService>();
    final history = context.watch<HistoryService>();
    final chatHistory = context.watch<ChatHistoryService>();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Settings'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Language Selection Card
            Card(
              child: Padding(
                padding: const EdgeInsets.all(14),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: const [
                        Icon(Icons.language, color: AppTheme.primaryGreen),
                        SizedBox(width: 8),
                        Text(
                          'Language / ಭಾಷೆ / भाषा / ഭാഷ',
                          style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    ...LocaleService.languageNames.entries.map((entry) {
                      final isSelected = locale.currentLanguage == entry.key;
                      final isDraft = entry.key != 'en';
                      return RadioListTile<String>(
                        value: entry.key,
                        // ignore: deprecated_member_use
                        groupValue: locale.currentLanguage,
                        activeColor: AppTheme.primaryGreen,
                        contentPadding: EdgeInsets.zero,
                        title: Row(
                          children: [
                            Text(
                              entry.value,
                              style: TextStyle(
                                fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                              ),
                            ),
                            if (isDraft) ...[
                              const SizedBox(width: 8),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                decoration: BoxDecoration(
                                  color: Colors.amber.shade100,
                                  borderRadius: BorderRadius.circular(4),
                                ),
                                child: Text(
                                  'Draft',
                                  style: TextStyle(fontSize: 10, color: Colors.amber.shade900),
                                ),
                              ),
                            ],
                          ],
                        ),
                        // ignore: deprecated_member_use
                        onChanged: (val) {
                          if (val != null) {
                            locale.setLanguage(val);
                          }
                        },
                      );
                    }),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Server URL Configuration Card
            Card(
              child: Padding(
                padding: const EdgeInsets.all(14),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: const [
                        Icon(Icons.dns, color: AppTheme.primaryGreen),
                        SizedBox(width: 8),
                        Text(
                          'App Server Connection',
                          style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Use http://10.0.2.2:8000 for Android emulator, or http://127.0.0.1:8000 for local desktop/web.',
                      style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      controller: _urlController,
                      decoration: const InputDecoration(
                        labelText: 'Server Base URL',
                        hintText: 'http://10.0.2.2:8000',
                      ),
                    ),
                    const SizedBox(height: 12),
                    OutlinedButton.icon(
                      icon: _isTesting
                          ? const SizedBox(
                              width: 16,
                              height: 16,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : const Icon(Icons.network_check),
                      label: Text(_isTesting ? 'Testing...' : 'Test Connection'),
                      onPressed: _isTesting ? null : _testConnection,
                    ),
                    if (_testStatus != null) ...[
                      const SizedBox(height: 10),
                      Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: _testStatus!.contains('success')
                              ? Colors.green.shade50
                              : Colors.red.shade50,
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text(
                          _testStatus!,
                          style: TextStyle(
                            fontSize: 12,
                            color: _testStatus!.contains('success')
                                ? Colors.green.shade800
                                : Colors.red.shade800,
                          ),
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Data Management Card
            Card(
              child: Padding(
                padding: const EdgeInsets.all(14),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: const [
                        Icon(Icons.storage, color: AppTheme.primaryGreen),
                        SizedBox(width: 8),
                        Text(
                          'Storage & Privacy',
                          style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Scan history (${history.history.length}/${AppConstants.maxHistoryScans} scans) and chat messages (${chatHistory.messages.length}/${AppConstants.maxChatMessages}) are stored only on your local device.',
                      style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
                    ),
                    const SizedBox(height: 12),
                    OutlinedButton.icon(
                      style: OutlinedButton.styleFrom(
                        foregroundColor: Colors.red.shade700,
                        side: BorderSide(color: Colors.red.shade300),
                      ),
                      icon: const Icon(Icons.delete_sweep),
                      label: const Text('Clear All Local Data'),
                      onPressed: () async {
                        final confirm = await showDialog<bool>(
                          context: context,
                          builder: (ctx) => AlertDialog(
                            title: const Text('Clear All Local Data?'),
                            content: const Text(
                              'This will permanently delete your local scan history and all chat messages from this device.',
                            ),
                            actions: [
                              TextButton(
                                onPressed: () => Navigator.pop(ctx, false),
                                child: const Text('Cancel'),
                              ),
                              TextButton(
                                onPressed: () => Navigator.pop(ctx, true),
                                child: const Text('Clear All', style: TextStyle(color: Colors.red)),
                              ),
                            ],
                          ),
                        );
                        if (confirm == true) {
                          await history.clearHistory();
                          await chatHistory.clearChat();
                          if (!context.mounted) return;
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(content: Text('All local data cleared.')),
                          );
                        }
                      },
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Disclaimers and Project Info
            Card(
              color: AppTheme.surfaceGreen,
              child: Padding(
                padding: const EdgeInsets.all(14),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: const [
                    Text(
                      'About ArecaLens',
                      style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold),
                    ),
                    SizedBox(height: 6),
                    Text(
                      'ArecaLens is a field screening aid designed for arecanut farmers in Karnataka and Kerala. It classifies photos into 4 categories using MobileNetV3 with Class Activation Mapping (CAM) explanations.\n\nAll guidance is strictly grounded in ICAR-CPCRI literature.',
                      style: TextStyle(fontSize: 12, color: AppTheme.textMuted, height: 1.3),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class TextEditing4EditingController extends TextEditingController {
  TextEditing4EditingController({super.text});
}
