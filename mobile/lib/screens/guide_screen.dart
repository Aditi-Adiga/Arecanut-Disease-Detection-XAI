import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import '../core/constants.dart';
import '../core/theme.dart';
import '../services/locale_service.dart';

class GuideScreen extends StatefulWidget {
  const GuideScreen({super.key});

  @override
  State<GuideScreen> createState() => _GuideScreenState();
}

class _GuideScreenState extends State<GuideScreen> {
  Map<String, dynamic>? _diseaseData;
  bool _isLoading = true;
  String _selectedClass = 'Mahali_Koleroga';

  @override
  void initState() {
    super.initState();
    _loadGuideData();
  }

  Future<void> _loadGuideData() async {
    try {
      final jsonStr = await rootBundle.loadString('assets/data/disease_info.json');
      setState(() {
        _diseaseData = json.decode(jsonStr) as Map<String, dynamic>;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final locale = context.watch<LocaleService>();

    if (_isLoading) {
      return Scaffold(
        appBar: AppBar(title: const Text('Disease Guide')),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    final classesMap = _diseaseData?['classes'] as Map<String, dynamic>? ?? {};
    final classInfo = classesMap[_selectedClass] as Map<String, dynamic>? ?? {};

    // Get regional translation if available, or fall back to English
    final i18n = classInfo['i18n'] as Map<String, dynamic>? ?? {};
    final regional = i18n[locale.currentLanguage] as Map<String, dynamic>?;

    final summary = (regional != null && regional['summary'] != null)
        ? regional['summary'] as String
        : (classInfo['summary'] is Map ? classInfo['summary']['text'] : '') as String;

    final whatToDoRaw = (regional != null && regional['what_to_do'] != null)
        ? regional['what_to_do'] as List<dynamic>
        : (classInfo['what_to_do'] as List<dynamic>? ?? []);

    final whatToDoList = whatToDoRaw.map((e) {
      if (e is Map<String, dynamic>) {
        return e['text'] as String? ?? '';
      }
      return e.toString();
    }).where((s) => s.isNotEmpty).toList();

    final limits = (regional != null && regional['limits'] != null)
        ? regional['limits'] as String
        : (classInfo['limits'] is Map ? classInfo['limits']['text'] : '') as String;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Arecanut Disease Guide'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Class selector tabs
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: AppConstants.classes.map((cls) {
                  final isSelected = cls == _selectedClass;
                  return Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: ChoiceChip(
                      label: Text(
                        AppConstants.getDisplayClassName(cls, locale.currentLanguage),
                        style: TextStyle(
                          fontSize: 12,
                          color: isSelected ? Colors.white : Colors.black87,
                          fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                        ),
                      ),
                      selected: isSelected,
                      selectedColor: AppTheme.primaryGreen,
                      onSelected: (val) {
                        if (val) {
                          setState(() {
                            _selectedClass = cls;
                          });
                        }
                      },
                    ),
                  );
                }).toList(),
              ),
            ),
            const SizedBox(height: 16),

            // Class Details Card
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Icon(Icons.info_outline, color: AppTheme.primaryGreen),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            AppConstants.getDisplayClassName(_selectedClass, locale.currentLanguage),
                            style: const TextStyle(
                              fontSize: 17,
                              fontWeight: FontWeight.bold,
                              color: AppTheme.primaryGreen,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    const Text(
                      'Summary & Symptoms:',
                      style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      summary,
                      style: TextStyle(fontSize: 13.5, color: Colors.grey.shade800, height: 1.4),
                    ),
                    if (whatToDoList.isNotEmpty) ...[
                      const SizedBox(height: 16),
                      const Text(
                        'Management & Best Practices:',
                        style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 6),
                      ...whatToDoList.map(
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
                    if (limits.isNotEmpty) ...[
                      const SizedBox(height: 12),
                      Container(
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: Colors.amber.shade50,
                          borderRadius: BorderRadius.circular(6),
                          border: Border.all(color: Colors.amber.shade200),
                        ),
                        child: Text(
                          limits,
                          style: TextStyle(fontSize: 12, color: Colors.amber.shade900),
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Source Attribution
            Card(
              color: Colors.grey.shade50,
              child: Padding(
                padding: const EdgeInsets.all(14),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: const [
                    Text(
                      'Scientific Citations',
                      style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold),
                    ),
                    SizedBox(height: 4),
                    Text(
                      'Guidance compiled from ICAR-Central Plantation Crops Research Institute (CPCRI) and Tamil Nadu Agricultural University (TNAU) Agritech Portal.',
                      style: TextStyle(fontSize: 12, color: AppTheme.textMuted),
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
