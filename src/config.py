"""Configuration management using Pydantic settings."""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field, PostgresDsn, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with validation."""
    
    # Application
    app_name: str = Field(default="lapis-spider", env="APP_NAME")
    app_env: str = Field(default="development", env="APP_ENV")
    app_debug: bool = Field(default=True, env="APP_DEBUG")
    app_host: str = Field(default="0.0.0.0", env="APP_HOST")
    app_port: int = Field(default=8000, env="APP_PORT")
    
    # Database
    postgres_host: str = Field(default="localhost", env="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, env="POSTGRES_PORT")
    postgres_db: str = Field(default="lapis_spider", env="POSTGRES_DB")
    postgres_user: str = Field(default="lapis", env="POSTGRES_USER")
    postgres_password: str = Field(..., env="POSTGRES_PASSWORD")
    
    # MongoDB
    mongodb_host: str = Field(default="localhost", env="MONGODB_HOST")
    mongodb_port: int = Field(default=27017, env="MONGODB_PORT")
    mongodb_url: str = Field(default="mongodb://localhost:27017", env="MONGODB_URL")
    mongodb_uri: Optional[str] = Field(default=None, env="MONGODB_URI")
    mongodb_db: str = Field(default="lapis_spider", env="MONGODB_DB")
    
    # Redis
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    redis_cache_ttl: int = Field(default=3600, env="REDIS_CACHE_TTL")
    
    # Celery
    celery_broker_url: str = Field(default="redis://localhost:6379/1", env="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/2", env="CELERY_RESULT_BACKEND")
    celery_task_time_limit: int = Field(default=3600, env="CELERY_TASK_TIME_LIMIT")
    celery_task_soft_time_limit: int = Field(default=3300, env="CELERY_TASK_SOFT_TIME_LIMIT")
    
    # Authentication
    jwt_secret_key: str = Field(..., env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(default=30, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    jwt_refresh_token_expire_days: int = Field(default=7, env="JWT_REFRESH_TOKEN_EXPIRE_DAYS")
    
    # Gemini AI
    gemini_api_key: Optional[str] = Field(default=None, env="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-1.5-flash", env="GEMINI_MODEL")
    gemini_max_retries: int = Field(default=3, env="GEMINI_MAX_RETRIES")
    gemini_timeout: int = Field(default=30, env="GEMINI_TIMEOUT")
    
    # OpenRouter AI
    openrouter_api_key: Optional[str] = Field(default=None, env="OPENROUTER_API_KEY")
    openrouter_model: str = Field(default="google/gemini-2.0-flash-exp", env="OPENROUTER_MODEL")
    
    # Crawler Settings
    max_pages_per_crawl: int = Field(default=1000, env="MAX_PAGES_PER_CRAWL")
    crawl_timeout_seconds: int = Field(default=3600, env="CRAWL_TIMEOUT_SECONDS")
    user_agent: str = Field(
        default="Lapis-Spider/1.0 (+https://lapis-spider.com/bot)",
        env="USER_AGENT"
    )
    concurrent_requests: int = Field(default=10, env="CONCURRENT_REQUESTS")
    request_timeout: int = Field(default=30, env="REQUEST_TIMEOUT")
    respect_robots_txt: bool = Field(default=True, env="RESPECT_ROBOTS_TXT")
    
    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    rate_limit_per_hour: int = Field(default=1000, env="RATE_LIMIT_PER_HOUR")
    
    # Storage
    storage_retention_days: int = Field(default=90, env="STORAGE_RETENTION_DAYS")
    storage_compression: bool = Field(default=True, env="STORAGE_COMPRESSION")
    
    # Monitoring
    sentry_dsn: Optional[str] = Field(default=None, env="SENTRY_DSN")
    prometheus_enabled: bool = Field(default=True, env="PROMETHEUS_ENABLED")
    prometheus_port: int = Field(default=9090, env="PROMETHEUS_PORT")
    flower_port: int = Field(default=5555, env="FLOWER_PORT")
    
    # Email
    smtp_host: Optional[str] = Field(default=None, env="SMTP_HOST")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_username: Optional[str] = Field(default=None, env="SMTP_USERNAME")
    smtp_password: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    smtp_from_email: str = Field(default="noreply@lapis-spider.com", env="SMTP_FROM_EMAIL")
    smtp_tls: bool = Field(default=True, env="SMTP_TLS")
    
    # Slack
    slack_webhook_url: Optional[str] = Field(default=None, env="SLACK_WEBHOOK_URL")
    
    # Frontend
    frontend_url: str = Field(default="http://localhost:3000", env="FRONTEND_URL")
    frontend_port: int = Field(default=3000, env="FRONTEND_PORT")
    next_public_api_url: Optional[str] = Field(default=None, env="NEXT_PUBLIC_API_URL")
    
    # Security
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        env="CORS_ORIGINS"
    )
    cors_allow_credentials: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    trusted_hosts: List[str] = Field(
        default=["localhost", "127.0.0.1"],
        env="TRUSTED_HOSTS"
    )
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    log_file_path: Optional[str] = Field(default="logs/app.log", env="LOG_FILE_PATH")
    log_max_size: int = Field(default=10485760, env="LOG_MAX_SIZE")  # 10MB
    log_backup_count: int = Field(default=5, env="LOG_BACKUP_COUNT")
    
    @validator("cors_origins", "trusted_hosts", pre=True)
    def parse_comma_separated_list(cls, v):
        """Parse comma-separated string into list."""
        if isinstance(v, str):
            return [item.strip() for item in v.split(",")]
        return v
    
    @property
    def postgres_url(self) -> str:
        """Build PostgreSQL connection URL."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
    
    @property
    def mongodb_connection_url(self) -> str:
        """Build MongoDB connection URL from components if URL not provided."""
        # Prefer mongodb_uri (Atlas), then mongodb_url, then build from components
        if self.mongodb_uri:
            return self.mongodb_uri
        if self.mongodb_url != "mongodb://localhost:27017":
            return self.mongodb_url
        return f"mongodb://{self.mongodb_host}:{self.mongodb_port}"
    
    @property
    def redis_connection_url(self) -> str:
        """Build Redis connection URL from components if URL not provided."""
        if self.redis_url != "redis://localhost:6379/0":
            return self.redis_url
        return f"redis://{self.redis_host}:{self.redis_port}/0"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app_env.lower() == "development"
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Environment-specific settings
class DevelopmentSettings(Settings):
    """Development environment settings."""
    app_debug: bool = True
    log_level: str = "DEBUG"


class ProductionSettings(Settings):
    """Production environment settings."""
    app_debug: bool = False
    log_level: str = "INFO"
    
    @validator("jwt_secret_key")
    def validate_jwt_secret(cls, v):
        """Ensure JWT secret is strong in production."""
        if len(v) < 32:
            raise ValueError("JWT secret key must be at least 32 characters in production")
        return v


class TestSettings(Settings):
    """Test environment settings."""
    app_env: str = "test"
    postgres_db: str = "lapis_spider_test"
    mongodb_db: str = "lapis_spider_test"
    redis_url: str = "redis://localhost:6379/15"
    
    # Use test-specific values
    jwt_secret_key: str = "test-secret-key-for-testing-only"
    postgres_password: str = "test-password"


def get_settings_for_env(env: Optional[str] = None) -> Settings:
    """Get environment-specific settings."""
    env = env or Settings().app_env.lower()
    
    if env == "development":
        return DevelopmentSettings()
    elif env == "production":
        return ProductionSettings()
    elif env == "test":
        return TestSettings()
    else:
        return Settings()


# Export commonly used settings
settings = get_settings()