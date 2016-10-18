#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import render_template, jsonify, current_app, request
from werkzeug.utils import secure_filename

from flask_login import current_user, login_required
from . import main
from ...models import File, User
from ... import db

@main.route('/', methods=['GET'])
@login_required
def index():
    return render_template('index.html', user=current_user)





