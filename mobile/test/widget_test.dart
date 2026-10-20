import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:arecalens/core/constants.dart';
import 'package:arecalens/core/theme.dart';
import 'package:arecalens/models/chat_message.dart';
import 'package:arecalens/models/screening_result.dart';
import 'package:arecalens/screens/main_navigation_screen.dart';
import 'package:arecalens/services/api_service.dart';
import 'package:arecalens/services/chat_history_service.dart';
import 'package:arecalens/services/history_service.dart';
import 'package:arecalens/services/locale_service.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  group('Threshold and Status Unit Tests', () {
    test('Healthy_Leaf >= 0.95 returns Healthy', () {
      final status = AppConstants.computeStatus('Healthy_Leaf', 0.96);
      expect(status, 'Healthy');
    });

    test('Healthy_Leaf < 0.95 returns Unsure', () {
      final status = AppConstants.computeStatus('Healthy_Leaf', 0.94);
      expect(status, 'Unsure');
    });

    test('Healthy_Nut >= 0.95 returns Healthy', () {
      final status = AppConstants.computeStatus('Healthy_Nut', 0.95);
      expect(status, 'Healthy');
    });

    test('Mahali_Koleroga >= 0.70 returns Suspected', () {
      final status = AppConstants.computeStatus('Mahali_Koleroga', 0.75);
      expect(status, 'Suspected');
    });

    test('Mahali_Koleroga < 0.70 returns Unsure', () {
      final status = AppConstants.computeStatus('Mahali_Koleroga', 0.69);
      expect(status, 'Unsure');
    });

    test('Yellow_Leaf >= 0.70 returns Suspected', () {
      final status = AppConstants.computeStatus('Yellow_Leaf', 0.85);
      expect(status, 'Suspected');
    });

    test('Yellow_Leaf < 0.70 returns Unsure', () {
      final status = AppConstants.computeStatus('Yellow_Leaf', 0.50);
      expect(status, 'Unsure');
    });
  });

  group('Storage Capping Unit Tests', () {
    test('History strictly caps at 8 items', () async {
      final history = HistoryService();
      await history.init();

      for (int i = 0; i < 15; i++) {
        await history.addResult(
          ScreeningResult(
            id: 'test_$i',
            predictedClass: 'Healthy_Leaf',
            confidence: 0.98,
            status: 'Healthy',
            scores: {'Healthy_Leaf': 0.98},
            summaryText: 'Summary $i',
            whatToDo: ['Step $i'],
            sourceIds: ['S1'],
            timestamp: DateTime.now(),
          ),
        );
      }

      expect(history.history.length, 8);
      expect(history.history.first.id, 'test_14');
    });

    test('Chat history strictly caps at 30 items', () async {
      final chatHistory = ChatHistoryService();
      await chatHistory.init();

      for (int i = 0; i < 40; i++) {
        await chatHistory.addMessage(
          ChatMessage(
            id: 'msg_$i',
            role: i.isEven ? 'user' : 'assistant',
            text: 'Message $i',
          ),
        );
      }

      expect(chatHistory.messages.length, 30);
      expect(chatHistory.messages.last.id, 'msg_39');
    });
  });

  group('Widget Smoke Tests', () {
    testWidgets('Renders MainNavigationScreen with all 5 navigation tabs', (tester) async {
      final locale = LocaleService();
      final history = HistoryService();
      final chat = ChatHistoryService();
      final api = ApiService();

      await locale.init();
      await history.init();
      await chat.init();
      await api.init();

      await tester.pumpWidget(
        MultiProvider(
          providers: [
            ChangeNotifierProvider.value(value: locale),
            ChangeNotifierProvider.value(value: history),
            ChangeNotifierProvider.value(value: chat),
            ChangeNotifierProvider.value(value: api),
          ],
          child: MaterialApp(
            theme: AppTheme.lightTheme,
            home: const MainNavigationScreen(),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Check BottomNavigationBar items
      expect(find.text('Screen'), findsOneWidget);
      expect(find.text('Guide'), findsOneWidget);
      expect(find.text('Ask'), findsOneWidget);
      expect(find.text('History'), findsOneWidget);
      expect(find.text('Settings'), findsOneWidget);

      // Verify Screen Tab is initially displayed
      expect(find.text('ArecaLens Screening'), findsOneWidget);
    });
  });
}
