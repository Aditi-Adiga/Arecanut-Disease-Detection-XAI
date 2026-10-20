import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../core/constants.dart';
import '../models/chat_message.dart';

class ChatHistoryService extends ChangeNotifier {
  static const String _prefKey = 'arecalens_chat_history';
  List<ChatMessage> _messages = [];

  List<ChatMessage> get messages => List.unmodifiable(_messages);

  Future<void> init() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_prefKey);
    if (raw != null) {
      try {
        final decoded = json.decode(raw) as List<dynamic>;
        _messages = decoded
            .map((item) => ChatMessage.fromJson(item as Map<String, dynamic>))
            .toList();
      } catch (e) {
        _messages = [];
      }
    }
    notifyListeners();
  }

  Future<void> addMessage(ChatMessage msg) async {
    _messages.add(msg);
    // Cap at 30 messages, dropping the oldest beyond 30
    if (_messages.length > AppConstants.maxChatMessages) {
      _messages = _messages.sublist(_messages.length - AppConstants.maxChatMessages);
    }
    await _save();
    notifyListeners();
  }

  Future<void> clearChat() async {
    _messages.clear();
    await _save();
    notifyListeners();
  }

  Future<void> _save() async {
    final prefs = await SharedPreferences.getInstance();
    final encoded = json.encode(_messages.map((e) => e.toJson()).toList());
    await prefs.setString(_prefKey, encoded);
  }
}
