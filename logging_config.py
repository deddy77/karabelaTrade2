"""Logging configuration for KarabelaTrade Bot"""
import os
import logging.config
from datetime import datetime

def get_logging_config():
    """Get logging configuration dictionary"""
    
    # Ensure log directories exist
    log_dirs = ['logs', 'logs/trades', 'logs/analysis', 'logs/diagnostics']
    for directory in log_dirs:
        os.makedirs(directory, exist_ok=True)
    
    # Get current date for log files
    current_date = datetime.now().strftime("%Y%m%d")
    
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            },
            'detailed': {
                'format': '%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',
                'formatter': 'standard',
                'stream': 'ext://sys.stdout'
            },
            'file_main': {
                'class': 'logging.FileHandler',
                'level': 'INFO',
                'formatter': 'detailed',
                'filename': 'logs/karabela.log',
                'mode': 'a'
            },
            'file_trades': {
                'class': 'logging.FileHandler',
                'level': 'INFO',
                'formatter': 'detailed',
                'filename': f'logs/trades/trades_{current_date}.log',
                'mode': 'a'
            },
            'file_analysis': {
                'class': 'logging.FileHandler',
                'level': 'INFO',
                'formatter': 'detailed',
                'filename': f'logs/analysis/analysis_{current_date}.log',
                'mode': 'a'
            },
            'file_diagnostics': {
                'class': 'logging.FileHandler',
                'level': 'INFO',
                'formatter': 'detailed',
                'filename': f'logs/diagnostics/diagnostics_{current_date}.log',
                'mode': 'a'
            },
            'file_errors': {
                'class': 'logging.FileHandler',
                'level': 'ERROR',
                'formatter': 'detailed',
                'filename': 'logs/errors.log',
                'mode': 'a'
            }
        },
        'loggers': {
            '': {  # Root logger
                'handlers': ['console', 'file_main', 'file_errors'],
                'level': 'INFO',
                'propagate': True
            },
            'trades': {
                'handlers': ['file_trades'],
                'level': 'INFO',
                'propagate': True
            },
            'analysis': {
                'handlers': ['file_analysis'],
                'level': 'INFO',
                'propagate': True
            },
            'diagnostics': {
                'handlers': ['file_diagnostics'],
                'level': 'INFO',
                'propagate': True
            }
        }
    }
    
    return config

def setup_logging():
    """Configure logging for the application"""
    config = get_logging_config()
    logging.config.dictConfig(config)
    
    # Create root logger
    logger = logging.getLogger()
    logger.info("Logging system initialized")
    
    # Test all loggers
    trades_logger = logging.getLogger('trades')
    analysis_logger = logging.getLogger('analysis')
    diagnostics_logger = logging.getLogger('diagnostics')
    
    trades_logger.info("Trade logging system initialized")
    analysis_logger.info("Analysis logging system initialized")
    diagnostics_logger.info("Diagnostics logging system initialized")
