import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../core/constants.dart';
import '../models/chat_message.dart';
import '../models/screening_result.dart';

class ApiService extends ChangeNotifier {
  static const String _prefBaseUrlKey = 'arecalens_server_url';
  String _baseUrl = AppConstants.defaultEmulatorBaseUrl;

  String get baseUrl => _baseUrl;

  Future<void> init() async {
    final prefs = await SharedPreferences.getInstance();
    final saved = prefs.getString(_prefBaseUrlKey);
    if (saved != null && saved.isNotEmpty) {
      _baseUrl = saved;
    } else {
      // Default: If running in web/desktop, use 127.0.0.1, otherwise 10.0.2.2 for Android emulator
      if (kIsWeb || defaultTargetPlatform == TargetPlatform.windows || defaultTargetPlatform == TargetPlatform.macOS) {
        _baseUrl = AppConstants.defaultLocalBaseUrl;
      } else {
        _baseUrl = AppConstants.defaultEmulatorBaseUrl;
      }
    }
    notifyListeners();
  }

  Future<void> setBaseUrl(String url) async {
    var cleanUrl = url.trim();
    if (cleanUrl.endsWith('/')) {
      cleanUrl = cleanUrl.substring(0, cleanUrl.length - 1);
    }
    _baseUrl = cleanUrl;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_prefBaseUrlKey, _baseUrl);
    notifyListeners();
  }

  // GET /api/health
  Future<bool> checkHealth() async {
    try {
      final response = await http
          .get(Uri.parse('$_baseUrl/api/health'))
          .timeout(const Duration(seconds: 4));
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  // GET /api/chat/status
  Future<bool> checkOnlineChatEnabled() async {
    try {
      final response = await http
          .get(Uri.parse('$_baseUrl/api/chat/status'))
          .timeout(const Duration(seconds: 4));
      if (response.statusCode == 200) {
        final data = json.decode(response.body) as Map<String, dynamic>;
        return data['online_enabled'] as bool? ?? false;
      }
      return false;
    } catch (_) {
      return false;
    }
  }

  // GET /api/chat/chips?language=...
  Future<List<SuggestionItem>> getChips(String lang, [List<String>? ids]) async {
    try {
      var urlStr = '$_baseUrl/api/chat/chips?language=$lang';
      if (ids != null && ids.isNotEmpty) {
        urlStr += '&ids=${ids.join(',')}';
      }
      final response = await http
          .get(Uri.parse(urlStr))
          .timeout(const Duration(seconds: 5));
      if (response.statusCode == 200) {
        final data = json.decode(response.body) as Map<String, dynamic>;
        final rawChips = data['chips'] as List<dynamic>? ?? [];
        return rawChips
            .map((c) => SuggestionItem.fromJson(c as Map<String, dynamic>))
            .toList();
      }
    } catch (_) {}
    return [];
  }

  // POST /api/predict?language=... multipart
  Future<ScreeningResult> predictOnline(
    Uint8List imageBytes,
    String filename,
    String language,
  ) async {
    final uri = Uri.parse('$_baseUrl/api/predict?language=$language');
    final request = http.MultipartRequest('POST', uri);
    request.files.add(
      http.MultipartFile.fromBytes('file', imageBytes, filename: filename),
    );

    // Cold start model load can take time; allow 45s timeout
    final streamed = await request.send().timeout(const Duration(seconds: 45));
    final response = await http.Response.fromStream(streamed);

    if (response.statusCode == 200) {
      final decoded = json.decode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
      final result = ScreeningResult.fromJson(decoded);
      return result;
    } else {
      throw Exception('Server returned ${response.statusCode}: ${response.body}');
    }
  }

  // POST /api/chat or /api/chat/online
  Future<ChatMessage> sendChatMessage({
    required String message,
    required String language,
    Map<String, dynamic>? context,
    String? entryId,
    List<ChatMessage>? history,
    bool isOnline = false,
  }) async {
    final endpoint = isOnline ? '$_baseUrl/api/chat/online' : '$_baseUrl/api/chat';

    final body = <String, dynamic>{
      'message': message,
      'language': language,
    };
    if (context != null) {
      body['context'] = context;
    }
    if (entryId != null) {
      body['entry_id'] = entryId;
    }
    if (history != null && history.isNotEmpty) {
      body['history'] = history.take(6).map((m) => {
        'role': m.role,
        'content': m.text,
      }).toList();
    }

    final response = await http.post(
      Uri.parse(endpoint),
      headers: {'Content-Type': 'application/json'},
      body: json.encode(body),
    ).timeout(const Duration(seconds: 20));

    if (response.statusCode == 200) {
      final decoded = json.decode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
      return ChatMessage.fromJson(decoded);
    } else {
      throw Exception('Chat request failed (HTTP ${response.statusCode})');
    }
  }
}
