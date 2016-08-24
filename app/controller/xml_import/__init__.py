#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Blueprint

xml_import = Blueprint('xml_import', __name__)

from . import views
