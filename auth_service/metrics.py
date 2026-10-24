from prometheus_client import Counter

REGISTRATIONS = Counter("carlog_auth_registrations", "Зарегистрировано пользователей")
LOGINS = Counter("carlog_auth_logins", "Попытки входа", ["result"])

LOGINS.labels("success")
LOGINS.labels("failed")
