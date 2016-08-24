#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SECRET_KEY = os.environ.get('SECRET_KEY', "1234")

    # SQL Alchemy
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DATABASE_USER = 'nicolas'
    DATABASE_PASSWORD = ''
    #SQLALCHEMY_DATABASE_URI = 'sqlite:///{}'.format(os.path.join(BASE_DIR, 'avisum.sqlite'))
    SQLALCHEMY_DATABASE_URI = 'postgresql://localhost/reanalytics'

    # Avisum
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    REPORT_DIR = os.path.join(BASE_DIR, 'reports')
    STRONGEST_SITE_ID = 36

    # FTP
    FTP_URL = os.environ.get('FTP_URL', 'server36.cyon.ch')
    FTP_USER = os.environ.get('FTP_USER')
    FTP_PASSWORD = os.environ.get('FTP_PASSWORD')
    FTP_FILE_NAME = os.environ.get('FTP_FILE_NAME', 'allesralle.xml')
    FTP_INITIAL_FILE_NAME = os.environ.get('FTP_INITIAL_FILE_NAME', 'allesralle_full.xml')

    # SMTP
    SMTP_SERVER = os.environ.get('SMTP_SERVER')
    SMTP_USER = os.environ.get('SMTP_USER')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')

    # Celery
    # - - - - - - - - - - - - - - - - - - - - - - - -
    BROKER_USER = os.environ.get('BROKER_USER')
    BROKER_PASSWORD = os.environ.get('BROKER_PASSWORD')
    BORKER_VIRTUALHOST = os.environ.get('BROKER_VIRTUALHOST')
    BROKER_URL = 'amqp://{user}:{passwd}@localhost/{host}'.format(user=BROKER_USER,
                                                                  passwd=BROKER_PASSWORD,
                                                                  host=BORKER_VIRTUALHOST)
    CELERY_RESULT_BACKEND = 'rpc://'

    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_TIMEZONE = 'Europe/Zurich'
    CELERY_ENABLE_UTC = True

    CELERY_SCHEDULE_HOUR = 11
    CELERY_SCHEDULE_MINUTE = 30

    from celery.schedules import crontab

    CELERYBEAT_SCHEDULE = {
        # Executes every day morning at 11:30 A.M
        'download-xml-every-day': {
            'task': 'celery_module.tasks.download_file',
            'schedule': crontab(hour=CELERY_SCHEDULE_HOUR, minute=CELERY_SCHEDULE_MINUTE),
            'options': {'expires': 3600},
            'args': (FTP_URL, FTP_USER, FTP_PASSWORD, FTP_FILE_NAME, DATA_DIR, STRONGEST_SITE_ID),
        },
    }

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    ASSETS_DEBUG = True
    

class TestConfig(Config):
    DEBUG = True
    ASSETS_DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')


class ProductionConfig(Config):
    # TODO: Use Postgres
    ASSETS_DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data.sqlite')


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'test': TestConfig,
    'default': DevelopmentConfig
}
