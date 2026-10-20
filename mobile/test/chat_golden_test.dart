import 'dart:convert';
import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:arecalens/chat/chat_engine.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late ChatEngine engine;
  late List<dynamic> goldenRecords;

  setUpAll(() {
    // Load FAQ and Disease Info
    final faqFile = File('assets/data/chatbot_faq.json');
    final infoFile = File('assets/data/disease_info.json');
    final goldenFile = File('test/assets/chat_golden.json');

    expect(faqFile.existsSync(), isTrue, reason: 'chatbot_faq.json should exist');
    expect(infoFile.existsSync(), isTrue, reason: 'disease_info.json should exist');
    expect(goldenFile.existsSync(), isTrue, reason: 'chat_golden.json should exist');

    final faq = json.decode(faqFile.readAsStringSync()) as Map<String, dynamic>;
    final info = json.decode(infoFile.readAsStringSync()) as Map<String, dynamic>;
    goldenRecords = json.decode(goldenFile.readAsStringSync()) as List<dynamic>;

    engine = ChatEngine(faq, info: info);
  });

  test('Dart ChatEngine achieves 100% parity with Python ChatEngine golden set (404 tests)', () {
    int passed = 0;
    final failures = <String>[];

    for (int i = 0; i < goldenRecords.length; i++) {
      final rec = goldenRecords[i] as Map<String, dynamic>;
      final question = rec['question'] as String;
      final language = rec['language'] as String;
      final context = rec['context'] as Map<String, dynamic>?;

      final expectedIntent = rec['expected_intent'] as String;
      final expectedEntryId = rec['expected_entry_id'] as String?;
      final expectedAnswer = rec['expected_answer'] as String;
      final expectedRefused = rec['refused'] as bool;
      final expectedReview = rec['needs_expert_review'] as bool;
      final expectedFallback = rec['language_fallback'] as bool;

      final reply = engine.answer(question, language: language, context: context);

      bool ok = true;
      final diffs = <String>[];

      if (reply.intent != expectedIntent) {
        ok = false;
        diffs.add('intent: got "${reply.intent}", expected "$expectedIntent"');
      }
      if (reply.entryId != expectedEntryId) {
        ok = false;
        diffs.add('entryId: got "${reply.entryId}", expected "$expectedEntryId"');
      }
      if (reply.answer != expectedAnswer) {
        ok = false;
        diffs.add('answer mismatch');
      }
      if (reply.refused != expectedRefused) {
        ok = false;
        diffs.add('refused: got ${reply.refused}, expected $expectedRefused');
      }
      if (reply.needsExpertReview != expectedReview) {
        ok = false;
        diffs.add('needsReview: got ${reply.needsExpertReview}, expected $expectedReview');
      }
      if (reply.languageFallback != expectedFallback) {
        ok = false;
        diffs.add('langFallback: got ${reply.languageFallback}, expected $expectedFallback');
      }

      if (ok) {
        passed++;
      } else {
        failures.add('Case $i ("$question" [$language]): ${diffs.join(', ')}');
      }
    }

    if (failures.isNotEmpty) {
      fail('${failures.length}/${goldenRecords.length} golden tests failed:\n${failures.take(10).join('\n')}');
    }

    expect(passed, goldenRecords.length);
  });
}
