class AuthState {
  final bool isAuthenticated;
  final int? studentId;
  final String? token;

  const AuthState({
    this.isAuthenticated = false,
    this.studentId,
    this.token,
  });

  AuthState copyWith({bool? isAuthenticated, int? studentId, String? token}) {
    return AuthState(
      isAuthenticated: isAuthenticated ?? this.isAuthenticated,
      studentId: studentId ?? this.studentId,
      token: token ?? this.token,
    );
  }
}
