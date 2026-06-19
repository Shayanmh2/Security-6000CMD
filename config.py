import os
from datetime import timedelta

class Config:
    "Base configuration class"
    
    #flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(24)
    
    # Database settings
    DATABASE_NAME = 'ecommerce.db'
    
    # session settings
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    
    # security headers 
    FORCE_HTTPS = False  # Set to True in production
    
    # Rate limiting 
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URL = 'memory://'
    
    # Password requirements
    MIN_PASSWORD_LENGTH = 6
    
class DevelopmentConfig(Config):
    "Development environment configuration"
    DEBUG = True
    TESTING = False
    
class ProductionConfig(Config):
    "Production environment configuration"
    DEBUG = False
    TESTING = False
    FORCE_HTTPS = True
    SESSION_COOKIE_SECURE = True  # Only send cookies over HTTPS
    
class TestingConfig(Config):
    "Testing environment configuration"
    DEBUG = True
    TESTING = True
    DATABASE_NAME = 'test_ecommerce.db'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}