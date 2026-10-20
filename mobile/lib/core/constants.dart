class AppConstants {
  // Classification classes in exact trained order
  static const List<String> classes = [
    'Healthy_Leaf',
    'Healthy_Nut',
    'Mahali_Koleroga',
    'Yellow_Leaf',
  ];

  // Hard thresholds specified in ANTIGRAVITY_TASK.md
  static const double healthyThreshold = 0.95;
  static const double diseaseThreshold = 0.70;

  // Maximum local storage capacities
  static const int maxHistoryScans = 8;
  static const int maxChatMessages = 30;
  static const int maxImageBytes = 10 * 1024 * 1024; // 10 MB

  // Feature flags
  // Set to false: offline photo screening requires on-device TFLite parity verification
  // with at least 20 farm validation images. Unverified offline screening is disabled for farmer safety.
  static const bool enableOfflineScreening = false;

  // Supported UI languages
  static const List<String> supportedLanguages = ['en', 'kn', 'hi', 'ml'];

  // Default server URLs
  static const String defaultEmulatorBaseUrl = 'http://10.0.2.2:8000';
  static const String defaultLocalBaseUrl = 'http://127.0.0.1:8000';

  // Human-readable class labels
  static String getDisplayClassName(String rawClass, String lang) {
    switch (rawClass) {
      case 'Healthy_Leaf':
        if (lang == 'kn') return 'ಆರೋಗ್ಯಕರ ಎಲೆ (Healthy Leaf)';
        if (lang == 'hi') return 'स्वस्थ पत्ता (Healthy Leaf)';
        if (lang == 'ml') return 'ആരോഗ്യമുള്ള ഇല (Healthy Leaf)';
        return 'Healthy Leaf';
      case 'Healthy_Nut':
        if (lang == 'kn') return 'ಆರೋಗ್ಯಕರ ಅಡಿಕೆ (Healthy Nut)';
        if (lang == 'hi') return 'स्वस्थ सुपारी (Healthy Nut)';
        if (lang == 'ml') return 'ആരോഗ്യമുള്ള അടക്ക (Healthy Nut)';
        return 'Healthy Nut';
      case 'Mahali_Koleroga':
        if (lang == 'kn') return 'ಕೊಳೆರೋಗ / ಮಹಾಲಿ (Mahali / Koleroga)';
        if (lang == 'hi') return 'कोलेरोगा / महाली (Mahali / Koleroga)';
        if (lang == 'ml') return 'മഹാലി / കൊളെറോഗ (Mahali / Koleroga)';
        return 'Mahali / Koleroga';
      case 'Yellow_Leaf':
        if (lang == 'kn') return 'ಹಳದಿ ಎಲೆ ರೋಗ (Yellow Leaf Disease)';
        if (lang == 'hi') return 'पीला पत्ता रोग (Yellow Leaf Disease)';
        if (lang == 'ml') return 'മഞ്ഞളിപ്പ് രോഗം (Yellow Leaf Disease)';
        return 'Yellow Leaf Disease';
      default:
        return rawClass;
    }
  }

  // Determine screening status using hard 0.95 and 0.70 thresholds
  static String computeStatus(String predictedClass, double confidence) {
    final isHealthy = predictedClass.startsWith('Healthy');
    if (isHealthy) {
      return confidence >= healthyThreshold ? 'Healthy' : 'Unsure';
    } else {
      return confidence >= diseaseThreshold ? 'Suspected' : 'Unsure';
    }
  }
}
