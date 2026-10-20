import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

class LocaleService extends ChangeNotifier {
  static const String _prefKey = 'selected_language';
  String _currentLanguage = 'en';

  String get currentLanguage => _currentLanguage;

  static const Map<String, String> languageNames = {
    'en': 'English',
    'kn': 'ಕನ್ನಡ (Kannada)',
    'hi': 'हिन्दी (Hindi)',
    'ml': 'മലയാളം (Malayalam)',
  };

  static const Map<String, String> languageShortNames = {
    'en': 'English',
    'kn': 'ಕನ್ನಡ',
    'hi': 'हिन्दी',
    'ml': 'മലയാളം',
  };

  bool get isDraftLanguage => _currentLanguage != 'en';

  Future<void> init() async {
    final prefs = await SharedPreferences.getInstance();
    _currentLanguage = prefs.getString(_prefKey) ?? 'en';
    notifyListeners();
  }

  Future<void> setLanguage(String lang) async {
    if (_currentLanguage == lang) return;
    _currentLanguage = lang;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_prefKey, lang);
    notifyListeners();
  }
}
