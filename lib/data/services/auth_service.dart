import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:student_agent/core/config/env_config.dart';
import 'package:student_agent/models/auth_state.dart';

class AuthService {
  static const _tokenKey = 'auth_token';
  static const _studentIdKey = 'auth_student_id';

  Future<AuthState> loadSession() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString(_tokenKey);
    final studentId = prefs.getInt(_studentIdKey);
    if (token != null && studentId != null) {
      return AuthState(isAuthenticated: true, studentId: studentId, token: token);
    }
    return const AuthState();
  }

  Future<AuthState> login(int studentId, String password) async {
    if (EnvConfig.useMockData || EnvConfig.isDemoEnv) {
      return _saveSession(studentId, 'demo_$studentId');
    }

    try {
      final dio = Dio(BaseOptions(
        baseUrl: EnvConfig.apiBaseUrl,
        connectTimeout: const Duration(seconds: 5),
      ));
      final res = await dio.post('/auth/login', data: {
        'student_id': studentId,
        'password': password,
      });
      final token = res.data['access_token'] as String;
      return _saveSession(studentId, token);
    } on DioException catch (e) {
      final status = e.response?.statusCode;
      if (status == 401 || status == 404) {
        throw const AuthException('Mã sinh viên hoặc mật khẩu không đúng.');
      }
      // Backend unreachable — allow demo login
      return _saveSession(studentId, 'demo_$studentId');
    }
  }

  Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_tokenKey);
    await prefs.remove(_studentIdKey);
  }

  Future<AuthState> _saveSession(int studentId, String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_tokenKey, token);
    await prefs.setInt(_studentIdKey, studentId);
    return AuthState(isAuthenticated: true, studentId: studentId, token: token);
  }
}

class AuthException implements Exception {
  final String message;
  const AuthException(this.message);
  @override
  String toString() => message;
}
