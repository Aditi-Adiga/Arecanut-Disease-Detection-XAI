import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../core/constants.dart';
import '../models/screening_result.dart';

class HistoryService extends ChangeNotifier {
  static const String _prefKey = 'arecalens_history';
  List<ScreeningResult> _history = [];

  List<ScreeningResult> get history => List.unmodifiable(_history);

  ScreeningResult? get latestResult => _history.isNotEmpty ? _history.first : null;

  Future<void> init() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_prefKey);
    if (raw != null) {
      try {
        final decoded = json.decode(raw) as List<dynamic>;
        _history = decoded
            .map((item) => ScreeningResult.fromJson(item as Map<String, dynamic>))
            .toList();
      } catch (e) {
        _history = [];
      }
    }
    notifyListeners();
  }

  Future<void> addResult(ScreeningResult result) async {
    // Remove if already exists with same id
    _history.removeWhere((item) => item.id == result.id);
    _history.insert(0, result);
    // Cap strictly at 8 items
    if (_history.length > AppConstants.maxHistoryScans) {
      _history = _history.sublist(0, AppConstants.maxHistoryScans);
    }
    await _save();
    notifyListeners();
  }

  Future<void> deleteResult(String id) async {
    _history.removeWhere((item) => item.id == id);
    await _save();
    notifyListeners();
  }

  Future<void> clearHistory() async {
    _history.clear();
    await _save();
    notifyListeners();
  }

  Future<void> _save() async {
    final prefs = await SharedPreferences.getInstance();
    final encoded = json.encode(_history.map((e) => e.toJson()).toList());
    await prefs.setString(_prefKey, encoded);
  }
}
