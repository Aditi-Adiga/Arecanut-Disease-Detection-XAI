import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';
import '../core/constants.dart';
import '../core/theme.dart';
import '../models/chat_message.dart';
import '../services/api_service.dart';
import '../services/chat_history_service.dart';
import '../services/history_service.dart';
import '../services/locale_service.dart';

class AskScreen extends StatefulWidget {
  const AskScreen({super.key});

  @override
  State<AskScreen> createState() => _AskScreenState();
}

class _AskScreenState extends State<AskScreen> {
  final TextEditingController _textController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  List<SuggestionItem> _starterChips = [];
  bool _isLoading = false;
  bool _isOnlineAvailable = false;

  @override
  void initState() {
    super.initState();
    _loadChips();
    _checkOnlineStatus();
  }

  @override
  void dispose() {
    _textController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  Future<void> _checkOnlineStatus() async {
    final api = context.read<ApiService>();
    final isOnline = await api.checkOnlineChatEnabled();
    if (mounted) {
      setState(() {
        _isOnlineAvailable = isOnline;
      });
    }
  }

  Future<void> _loadChips() async {
    final locale = context.read<LocaleService>();
    final api = context.read<ApiService>();
    // Try server chips
    final chips = await api.getChips(locale.currentLanguage);
    if (chips.isNotEmpty && mounted) {
      setState(() {
        _starterChips = chips;
      });
      return;
    }

    // Fallback: load chips from bundled chatbot_faq.json asset
    try {
      final jsonStr = await rootBundle.loadString('assets/data/chatbot_faq.json');
      final data = json.decode(jsonStr) as Map<String, dynamic>;
      final chipIds = data['chips'] as List<dynamic>? ?? [];
      final entries = (data['entries'] as List<dynamic>? ?? []).cast<Map<String, dynamic>>();

      final fallbackChips = <SuggestionItem>[];
      for (final cid in chipIds) {
        final match = entries.firstWhere(
          (e) => e['id'] == cid,
          orElse: () => <String, dynamic>{},
        );
        if (match.isNotEmpty) {
          var q = ((match['questions'] as List<dynamic>?)?.firstOrNull ?? cid).toString();
          final qI18n = match['questions_i18n'] as Map<String, dynamic>?;
          if (qI18n != null && qI18n[locale.currentLanguage] != null) {
            final regionalList = qI18n[locale.currentLanguage] as List<dynamic>?;
            if (regionalList != null && regionalList.isNotEmpty) {
              q = regionalList.first.toString();
            }
          }
          fallbackChips.add(SuggestionItem(id: cid.toString(), question: q));
        }
      }
      if (mounted) {
        setState(() {
          _starterChips = fallbackChips;
        });
      }
    } catch (_) {}
  }

  Future<void> _sendMessage(String text, {String? entryId, bool isOnlineMode = false}) async {
    final cleanText = text.trim();
    if (cleanText.isEmpty || _isLoading) return;

    final chatHistory = context.read<ChatHistoryService>();
    final locale = context.read<LocaleService>();
    final historyService = context.read<HistoryService>();
    final api = context.read<ApiService>();

    // Add user message to UI
    final userMsg = ChatMessage(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      role: 'user',
      text: cleanText,
    );
    await chatHistory.addMessage(userMsg);
    _textController.clear();
    _scrollToBottom();

    setState(() {
      _isLoading = true;
    });

    Map<String, dynamic>? ctx;
    final lastScan = historyService.latestResult;
    if (lastScan != null) {
      ctx = {
        'class': lastScan.predictedClass,
        'status': lastScan.status,
        'confidence': lastScan.confidence,
      };
    }

    try {
      final reply = await api.sendChatMessage(
        message: cleanText,
        language: locale.currentLanguage,
        context: ctx,
        entryId: entryId,
        history: chatHistory.messages,
        isOnline: isOnlineMode,
      );

      await chatHistory.addMessage(reply);
      _scrollToBottom();
    } catch (e) {
      // Local fallback answer if network fails
      final errorMsg = ChatMessage(
        id: (DateTime.now().millisecondsSinceEpoch + 1).toString(),
        role: 'assistant',
        text: 'Could not connect to the assistant server. Please verify your connection or server URL in Settings.',
        answerSource: 'guide',
      );
      await chatHistory.addMessage(errorMsg);
      _scrollToBottom();
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final chatHistory = context.watch<ChatHistoryService>();
    final historyService = context.watch<HistoryService>();
    final locale = context.watch<LocaleService>();
    final messages = chatHistory.messages;
    final lastScan = historyService.latestResult;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Ask ArecaLens'),
        actions: [
          if (messages.isNotEmpty)
            IconButton(
              icon: const Icon(Icons.delete_outline),
              tooltip: 'Clear Chat',
              onPressed: () async {
                final confirm = await showDialog<bool>(
                  context: context,
                  builder: (ctx) => AlertDialog(
                    title: const Text('Clear Chat?'),
                    content: const Text('This will delete all messages in this conversation. (Max 30 messages stored locally).'),
                    actions: [
                      TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancel')),
                      TextButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Clear', style: TextStyle(color: Colors.red))),
                    ],
                  ),
                );
                if (confirm == true) {
                  await chatHistory.clearChat();
                }
              },
            ),
        ],
      ),
      body: Column(
        children: [
          // Header disclaimer & Result Context Chip
          Container(
            color: AppTheme.surfaceGreen,
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                if (lastScan != null) ...[
                  Row(
                    children: [
                      const Icon(Icons.history_edu, size: 18, color: AppTheme.primaryGreen),
                      const SizedBox(width: 6),
                      Expanded(
                        child: Text(
                          'Last scan: ${AppConstants.getDisplayClassName(lastScan.predictedClass, locale.currentLanguage)} (${lastScan.status})',
                          style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppTheme.primaryGreen),
                        ),
                      ),
                      ActionChip(
                        label: const Text('Ask about this', style: TextStyle(fontSize: 11)),
                        backgroundColor: Colors.white,
                        onPressed: () {
                          _sendMessage('What should I do about ${lastScan.predictedClass}?');
                        },
                      ),
                    ],
                  ),
                ],
                const SizedBox(height: 2),
                const Text(
                  'Knowledge-grounded assistant. Never gives unverified chemical spray doses. Screening aid only.',
                  style: TextStyle(fontSize: 11, color: AppTheme.textMuted),
                  textAlign: TextAlign.center,
                ),
              ],
            ),
          ),

          // Message List
          Expanded(
            child: messages.isEmpty
                ? _buildEmptyState(locale)
                : ListView.builder(
                    controller: _scrollController,
                    padding: const EdgeInsets.all(12),
                    itemCount: messages.length,
                    itemBuilder: (ctx, index) {
                      final msg = messages[index];
                      return _buildMessageBubble(msg, locale);
                    },
                  ),
          ),

          if (_isLoading)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 4),
              child: LinearProgressIndicator(color: AppTheme.primaryGreen),
            ),

          // Starter chips when chat is active
          if (messages.isNotEmpty && _starterChips.isNotEmpty)
            Container(
              height: 42,
              padding: const EdgeInsets.symmetric(horizontal: 8),
              child: ListView.builder(
                scrollDirection: Axis.horizontal,
                itemCount: _starterChips.length,
                itemBuilder: (ctx, index) {
                  final chip = _starterChips[index];
                  return Padding(
                    padding: const EdgeInsets.only(right: 6),
                    child: ActionChip(
                      label: Text(chip.question, style: const TextStyle(fontSize: 12)),
                      backgroundColor: Colors.grey.shade100,
                      onPressed: () => _sendMessage(chip.question, entryId: chip.id),
                    ),
                  );
                },
              ),
            ),

          // Input field and Send button
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: Colors.white,
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.05),
                  offset: const Offset(0, -2),
                  blurRadius: 4,
                ),
              ],
            ),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _textController,
                    maxLength: 300,
                    decoration: const InputDecoration(
                      hintText: 'Ask about leaf/nut symptoms...',
                      counterText: '',
                      contentPadding: EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                    ),
                    onSubmitted: (val) => _sendMessage(val),
                  ),
                ),
                const SizedBox(width: 8),
                IconButton(
                  icon: const Icon(Icons.send, color: AppTheme.primaryGreen),
                  onPressed: () => _sendMessage(_textController.text),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyState(LocaleService locale) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          const SizedBox(height: 16),
          const Icon(Icons.chat_bubble_outline, size: 56, color: AppTheme.primaryGreen),
          const SizedBox(height: 12),
          const Text(
            'Ask ArecaLens Questions',
            style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 6),
          Text(
            'Select a common question below or type your inquiry. Answers are strictly verified against ICAR-CPCRI publications.',
            style: TextStyle(fontSize: 13, color: Colors.grey.shade600),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 20),
          if (_starterChips.isNotEmpty) ...[
            const Align(
              alignment: Alignment.centerLeft,
              child: Text('Suggested Questions:', style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold)),
            ),
            const SizedBox(height: 10),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: _starterChips.map((chip) {
                return ActionChip(
                  label: Text(chip.question),
                  backgroundColor: AppTheme.surfaceGreen,
                  side: const BorderSide(color: AppTheme.primaryGreen, width: 0.8),
                  onPressed: () => _sendMessage(chip.question, entryId: chip.id),
                );
              }).toList(),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildMessageBubble(ChatMessage msg, LocaleService locale) {
    final isUser = msg.role == 'user';

    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 6),
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.88,
        ),
        decoration: BoxDecoration(
          color: isUser ? AppTheme.primaryGreen : Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: isUser ? null : Border.all(color: Colors.grey.shade300),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.04),
              blurRadius: 3,
              offset: const Offset(0, 1),
            ),
          ],
        ),
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Message text
            Text(
              msg.text,
              style: TextStyle(
                fontSize: 14,
                color: isUser ? Colors.white : Colors.black87,
                height: 1.35,
              ),
            ),

            if (!isUser) ...[
              const SizedBox(height: 8),

              // Badges
              Wrap(
                spacing: 6,
                runSpacing: 4,
                children: [
                  // Provenance badge
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: msg.aiGenerated ? Colors.purple.shade50 : AppTheme.surfaceGreen,
                      borderRadius: BorderRadius.circular(4),
                      border: Border.all(
                        color: msg.aiGenerated ? Colors.purple.shade300 : AppTheme.primaryGreen,
                        width: 0.8,
                      ),
                    ),
                    child: Text(
                      msg.aiGenerated ? 'AI-generated • Verify with officer' : 'From verified guide',
                      style: TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.bold,
                        color: msg.aiGenerated ? Colors.purple.shade900 : AppTheme.primaryGreen,
                      ),
                    ),
                  ),

                  // Expert review badge
                  if (msg.needsExpertReview)
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                      decoration: BoxDecoration(
                        color: Colors.amber.shade100,
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text(
                        'Please confirm with agricultural officer',
                        style: TextStyle(fontSize: 10, color: Colors.amber.shade900),
                      ),
                    ),

                  // Language fallback notice
                  if (msg.languageFallback)
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                      decoration: BoxDecoration(
                        color: Colors.blue.shade50,
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text(
                        'English fallback (Regional translation pending)',
                        style: TextStyle(fontSize: 10, color: Colors.blue.shade800),
                      ),
                    ),
                ],
              ),

              // Sources Expander
              if (msg.sources.isNotEmpty) ...[
                const SizedBox(height: 6),
                _SourcesTile(sources: msg.sources),
              ],

              // Ask more (online) button
              if (!msg.aiGenerated && _isOnlineAvailable) ...[
                const SizedBox(height: 8),
                OutlinedButton.icon(
                  style: OutlinedButton.styleFrom(
                    visualDensity: VisualDensity.compact,
                    foregroundColor: Colors.deepPurple,
                    side: const BorderSide(color: Colors.deepPurple, width: 1.2),
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  ),
                  icon: const Icon(Icons.auto_awesome, size: 16),
                  label: const Text('Ask more (online)', style: TextStyle(fontSize: 12)),
                  onPressed: () {
                    _sendMessage(
                      'Provide more practical context on: ${msg.text.split('.').first}',
                      isOnlineMode: true,
                    );
                  },
                ),
              ],

              // Suggestion chips
              if (msg.suggestions.isNotEmpty) ...[
                const SizedBox(height: 8),
                Wrap(
                  spacing: 6,
                  runSpacing: 4,
                  children: msg.suggestions.map((sug) {
                    return ActionChip(
                      visualDensity: VisualDensity.compact,
                      label: Text(sug.question, style: const TextStyle(fontSize: 11)),
                      backgroundColor: Colors.grey.shade50,
                      onPressed: () => _sendMessage(sug.question, entryId: sug.id),
                    );
                  }).toList(),
                ),
              ],
            ],
          ],
        ),
      ),
    );
  }
}

class _SourcesTile extends StatefulWidget {
  final List<SourceItem> sources;

  const _SourcesTile({required this.sources});

  @override
  State<_SourcesTile> createState() => _SourcesTileState();
}

class _SourcesTileState extends State<_SourcesTile> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        InkWell(
          onTap: () => setState(() => _expanded = !_expanded),
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 4),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(_expanded ? Icons.expand_less : Icons.expand_more, size: 16, color: Colors.grey.shade700),
                const SizedBox(width: 4),
                Text(
                  'Sources (${widget.sources.length})',
                  style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Colors.grey.shade700),
                ),
              ],
            ),
          ),
        ),
        if (_expanded)
          Padding(
            padding: const EdgeInsets.only(top: 4, left: 6),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: widget.sources.map((s) {
                return Padding(
                  padding: const EdgeInsets.only(bottom: 4),
                  child: InkWell(
                    onTap: s.url.isNotEmpty ? () => launchUrl(Uri.parse(s.url)) : null,
                    child: Text(
                      '• ${s.title} (${s.publisher}, ${s.year})',
                      style: TextStyle(
                        fontSize: 11,
                        color: s.url.isNotEmpty ? Colors.blue.shade700 : Colors.black87,
                        decoration: s.url.isNotEmpty ? TextDecoration.underline : null,
                      ),
                    ),
                  ),
                );
              }).toList(),
            ),
          ),
      ],
    );
  }
}
