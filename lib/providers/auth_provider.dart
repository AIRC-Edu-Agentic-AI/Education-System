import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:student_agent/data/services/auth_service.dart';
import 'package:student_agent/models/auth_state.dart';

class AuthNotifier extends ChangeNotifier {
  final AuthService _service;
  AuthState _state = const AuthState();
  bool _initialized = false;
  String? _error;

  AuthNotifier(this._service);

  AuthState get state => _state;
  bool get initialized => _initialized;
  String? get error => _error;

  Future<void> init() async {
    _state = await _service.loadSession();
    _initialized = true;
    notifyListeners();
  }

  Future<bool> login(int studentId, String password) async {
    _error = null;
    notifyListeners();
    try {
      _state = await _service.login(studentId, password);
      notifyListeners();
      return true;
    } on AuthException catch (e) {
      _error = e.message;
      notifyListeners();
      return false;
    } catch (_) {
      _error = 'Đã xảy ra lỗi. Vui lòng thử lại.';
      notifyListeners();
      return false;
    }
  }

  Future<void> logout() async {
    await _service.logout();
    _state = const AuthState();
    notifyListeners();
  }

  void clearError() {
    _error = null;
    notifyListeners();
  }
}

final authServiceProvider = Provider<AuthService>((_) => AuthService());

final authNotifierProvider = ChangeNotifierProvider<AuthNotifier>((ref) {
  final notifier = AuthNotifier(ref.read(authServiceProvider));
  notifier.init();
  return notifier;
});
