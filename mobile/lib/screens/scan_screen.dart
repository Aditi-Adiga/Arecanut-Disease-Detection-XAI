import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';
import '../core/constants.dart';
import '../core/theme.dart';
import '../services/api_service.dart';
import '../services/history_service.dart';
import '../services/locale_service.dart';
import 'result_screen.dart';

class ScanScreen extends StatefulWidget {
  final Function(int tabIndex)? onNavigateTab;

  const ScanScreen({super.key, this.onNavigateTab});

  @override
  State<ScanScreen> createState() => _ScanScreenState();
}

class _ScanScreenState extends State<ScanScreen> {
  final ImagePicker _picker = ImagePicker();
  Uint8List? _selectedBytes;
  String? _selectedFileName;
  bool _isLoading = false;
  String? _errorMessage;

  Future<void> _pickImage(ImageSource source) async {
    setState(() {
      _errorMessage = null;
    });
    try {
      final XFile? file = await _picker.pickImage(
        source: source,
        maxWidth: 2048,
        maxHeight: 2048,
        imageQuality: 90,
      );
      if (file == null) return;

      final bytes = await file.readAsBytes();
      if (bytes.length > AppConstants.maxImageBytes) {
        setState(() {
          _errorMessage = 'Selected image is larger than 10 MB limit.';
        });
        return;
      }

      setState(() {
        _selectedBytes = bytes;
        _selectedFileName = file.name;
      });
    } catch (e) {
      setState(() {
        _errorMessage = 'Could not load image: $e';
      });
    }
  }

  Future<void> _runScreening() async {
    if (_selectedBytes == null) return;

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final apiService = context.read<ApiService>();
    final historyService = context.read<HistoryService>();
    final localeService = context.read<LocaleService>();

    try {
      final result = await apiService.predictOnline(
        _selectedBytes!,
        _selectedFileName ?? 'arecanut_photo.jpg',
        localeService.currentLanguage,
      );

      // Save to local history (capped at 8 items)
      await historyService.addResult(result);

      if (!mounted) return;
      setState(() {
        _isLoading = false;
      });

      // Navigate to Result screen
      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (ctx) => ResultScreen(
            result: result,
            onAskAboutResult: (cls) {
              Navigator.pop(ctx);
              widget.onNavigateTab?.call(2); // Ask tab index
            },
          ),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _isLoading = false;
        _errorMessage =
            'Screening failed. Please check your connection or server URL in Settings.\nDetails: $e';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final locale = context.watch<LocaleService>();

    return Scaffold(
      appBar: AppBar(
        title: const Text('ArecaLens Screening'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Welcome & screening banner
            Card(
              color: AppTheme.surfaceGreen,
              child: Padding(
                padding: const EdgeInsets.all(14),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: const [
                        Icon(Icons.eco, color: AppTheme.primaryGreen, size: 24),
                        SizedBox(width: 8),
                        Text(
                          'Arecanut Health Screening',
                          style: TextStyle(
                            fontSize: 17,
                            fontWeight: FontWeight.bold,
                            color: AppTheme.primaryGreen,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 6),
                    Text(
                      'Capture or upload a clear photo of an arecanut leaf or nut cluster to screen for Koleroga or Yellow Leaf Disease.',
                      style: TextStyle(fontSize: 14, color: Colors.grey.shade800),
                    ),
                    if (locale.isDraftLanguage) ...[
                      const SizedBox(height: 6),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: Colors.amber.shade100,
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: Text(
                          'Language: ${LocaleService.languageShortNames[locale.currentLanguage]} (Draft translation)',
                          style: TextStyle(fontSize: 12, color: Colors.amber.shade900),
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Image Preview Area
            Container(
              height: 260,
              decoration: BoxDecoration(
                color: Colors.grey.shade100,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.grey.shade300, width: 1.5),
              ),
              child: _selectedBytes != null
                  ? ClipRRect(
                      borderRadius: BorderRadius.circular(10),
                      child: Stack(
                        fit: StackFit.expand,
                        children: [
                          Image.memory(_selectedBytes!, fit: BoxFit.contain),
                          Positioned(
                            top: 8,
                            right: 8,
                            child: IconButton(
                              icon: const Icon(Icons.cancel, color: Colors.black54),
                              onPressed: () {
                                setState(() {
                                  _selectedBytes = null;
                                  _selectedFileName = null;
                                  _errorMessage = null;
                                });
                              },
                            ),
                          ),
                        ],
                      ),
                    )
                  : Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.add_photo_alternate_outlined,
                            size: 56, color: Colors.grey.shade400),
                        const SizedBox(height: 8),
                        Text(
                          'No photo selected',
                          style: TextStyle(fontSize: 15, color: Colors.grey.shade600),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          'Tap below to take a photo or choose from gallery',
                          style: TextStyle(fontSize: 13, color: Colors.grey.shade500),
                        ),
                      ],
                    ),
            ),
            const SizedBox(height: 16),

            // Action Buttons: Camera & Gallery
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    icon: const Icon(Icons.camera_alt),
                    label: const Text('Camera'),
                    onPressed: _isLoading ? null : () => _pickImage(ImageSource.camera),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: OutlinedButton.icon(
                    icon: const Icon(Icons.photo_library),
                    label: const Text('Gallery'),
                    onPressed: _isLoading ? null : () => _pickImage(ImageSource.gallery),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),

            // Error Display
            if (_errorMessage != null) ...[
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.red.shade50,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.red.shade200),
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Icon(Icons.error_outline, color: AppTheme.redAlert, size: 20),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        _errorMessage!,
                        style: const TextStyle(fontSize: 13, color: AppTheme.redAlert),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),
            ],

            // Submit Screening Button
            ElevatedButton.icon(
              icon: _isLoading
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                    )
                  : const Icon(Icons.search),
              label: Text(_isLoading ? 'Screening Photo...' : 'Screen Leaf / Nut'),
              onPressed: (_selectedBytes != null && !_isLoading) ? _runScreening : null,
            ),
            const SizedBox(height: 16),

            // Tips card
            Card(
              child: Padding(
                padding: const EdgeInsets.all(14),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Photo Tips for Best Screening:',
                      style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                    ),
                    const SizedBox(height: 8),
                    _buildTip('Fill the frame with the affected leaf or nut cluster'),
                    _buildTip('Ensure good natural lighting; avoid deep shadows'),
                    _buildTip('Keep camera steady to avoid blur'),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTip(String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('• ', style: TextStyle(fontWeight: FontWeight.bold)),
          Expanded(
            child: Text(text, style: TextStyle(fontSize: 13, color: Colors.grey.shade700)),
          ),
        ],
      ),
    );
  }
}
