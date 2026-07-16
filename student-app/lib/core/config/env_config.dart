import 'package:flutter_dotenv/flutter_dotenv.dart';

class EnvConfig {
  static String get apiBaseUrl =>
      dotenv.env['API_BASE_URL'] ?? 'http://localhost:8000';

  static String get auth0Domain =>
      dotenv.env['AUTH0_DOMAIN'] ?? '';

  static String get auth0ClientId =>
      dotenv.env['AUTH0_CLIENT_ID'] ?? '';

  static String get auth0Audience =>
      dotenv.env['AUTH0_AUDIENCE'] ?? '';

  static bool get useMockData =>
      dotenv.env['USE_MOCK_DATA'] == 'true';

  static bool get isDemoEnv =>
      dotenv.env['ENVIRONMENT'] == 'demo';

  static int get pollingIntervalSeconds =>
      int.tryParse(dotenv.env['POLLING_INTERVAL_SECONDS'] ?? '30') ?? 30;
}
