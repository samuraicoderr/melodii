import os


REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
FAIL_IF_REDIS_IS_NOT_AVAILABLE = (
	os.getenv("FAIL_IF_REDIS_IS_NOT_AVAILABLE", "True") == "True"
)

try:
	import redis as _redis

	_client = _redis.from_url(REDIS_URL)
	_client.ping()
	_REDIS_AVAILABLE = True
except Exception as exc:
	_REDIS_AVAILABLE = False
	if FAIL_IF_REDIS_IS_NOT_AVAILABLE:
		raise RuntimeError(
			"Redis is not available and "
			"FAIL_IF_REDIS_IS_NOT_AVAILABLE=True. "
			f"Error: {exc}"
		) from exc


BROKER_URL = REDIS_URL if _REDIS_AVAILABLE else "memory://"
CELERY_RESULT_BACKEND = REDIS_URL if _REDIS_AVAILABLE else "cache+memory://"

CHANNEL_LAYERS = (
	{
		"default": {
			"BACKEND": "channels_redis.core.RedisChannelLayer",
			"CONFIG": {"hosts": [REDIS_URL + "/1"]},
		}
	}
	if _REDIS_AVAILABLE
	else {
		"default": {
			"BACKEND": "channels.layers.InMemoryChannelLayer",
		}
	}
)

CACHES = (
	{
		"default": {
			"BACKEND": "django_redis.cache.RedisCache",
			"LOCATION": REDIS_URL + "/2",
			"OPTIONS": {
				"CLIENT_CLASS": "django_redis.client.DefaultClient",
			},
		}
	}
	if _REDIS_AVAILABLE
	else {
		"default": {
			"BACKEND": "django.core.cache.backends.locmem.LocMemCache",
			"LOCATION": "melodii-local-cache",
		}
	}
)


CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
