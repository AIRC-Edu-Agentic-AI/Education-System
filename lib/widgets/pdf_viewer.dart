import 'package:flutter/material.dart';
import 'package:pdfx/pdfx.dart';
import 'package:student_agent/core/theme/app_theme.dart';

class PdfViewer extends StatefulWidget {
  final String filePath;
  
  const PdfViewer({
    super.key,
    required this.filePath,
  });

  @override
  State<PdfViewer> createState() => _PdfViewerState();
}

class _PdfViewerState extends State<PdfViewer> {
  late PdfController _pdfController;
  bool _isLoading = true;
  int _totalPages = 0;
  int _currentPage = 1;

  @override
  void initState() {
    super.initState();
    _initPdf();
  }

  Future<void> _initPdf() async {
    try {
      // Mở document - trả về Future<PdfDocument>
      final document = await PdfDocument.openFile(widget.filePath);
      _totalPages = document.pagesCount;
      
      // Tạo controller với document đã mở
      _pdfController = PdfController(
        document: _pdfController.document,
      );
      
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    } catch (e) {
      print('PDF Error: $e');
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Lỗi tải PDF: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  @override
  void dispose() {
    _pdfController.dispose();
    super.dispose();
  }

  void _goToPage(int page) {
    if (page >= 1 && page <= _totalPages) {
      _pdfController.jumpToPage(page);
      setState(() {
        _currentPage = page;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Center(
        child: CircularProgressIndicator(),
      );
    }

    return Column(
      children: [
        // Page controls
        if (_totalPages > 1)
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                IconButton(
                  icon: const Icon(Icons.chevron_left, size: 24),
                  onPressed: _currentPage > 1 
                      ? () => _goToPage(_currentPage - 1) 
                      : null,
                  color: AppTheme.primaryBlue,
                ),
                Text(
                  'Trang $_currentPage / $_totalPages',
                  style: const TextStyle(
                    color: Colors.black87,
                    fontSize: 14,
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.chevron_right, size: 24),
                  onPressed: _currentPage < _totalPages 
                      ? () => _goToPage(_currentPage + 1) 
                      : null,
                  color: AppTheme.primaryBlue,
                ),
              ],
            ),
          ),
        
        // PDF viewer
        Expanded(
          child: PdfView(
            controller: _pdfController,
            onPageChanged: (page) {
              setState(() {
                _currentPage = page;
              });
            },
          ),
        ),
      ],
    );
  }
}