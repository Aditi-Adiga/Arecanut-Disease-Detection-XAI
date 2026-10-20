import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'core/theme.dart';
import 'screens/main_navigation_screen.dart';
import 'services/api_service.dart';
import 'services/chat_history_service.dart';
import 'services/history_service.dart';
import 'services/locale_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  final localeService = LocaleService();
  final historyService = HistoryService();
  final chatHistoryService = ChatHistoryService();
  final apiService = ApiService();

  await localeService.init();
  await historyService.init();
  await chatHistoryService.init();
  await apiService.init();

  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider.value(value: localeService),
        ChangeNotifierProvider.value(value: historyService),
        ChangeNotifierProvider.value(value: chatHistoryService),
        ChangeNotifierProvider.value(value: apiService),
      ],
      child: const ArecaLensApp(),
    ),
  );
}

class ArecaLensApp extends StatelessWidget {
  const ArecaLensApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'ArecaLens',
      theme: AppTheme.lightTheme,
      debugShowCheckedModeBanner: false,
      home: const MainNavigationScreen(),
    );
  }
}
