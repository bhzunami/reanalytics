#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import render_template, jsonify, current_app, request, redirect, url_for
from werkzeug.utils import secure_filename
import os
from flask_login import current_user, login_required
from . import xml_import
from .forms import UploadForm
from ...models import File, User
from ... import db

@xml_import.route('/', methods=['GET'])
@login_required
def get_imported_files():
    files = File.query.all()
    return render_template('xml_import/main.html', files=files)


@xml_import.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    form = UploadForm()
    if form.validate_on_submit():
        file = request.files['file']
        if file:
            name = secure_filename(file.filename)
            dest = '{}'.format(os.path.join(current_app.config['DATA_DIR'], name))
            f = File(name=name, path=dest)
            # Store file
            file.save(dest)
            db.session.add(f)
            db.session.commit()


            # Import file
            from celery_module.tasks import import_xml
            import_xml.delay(f.id, current_app.config['STRONGEST_SITE_ID'], user_id=current_user.id,
                             url=url_for('xml_import.update_client', _external=True))

        return redirect(url_for('.get_imported_files'))

    return render_template('xml_import/upload.html', form=form)


@xml_import.route('/event', methods=['POST'])
def update_client():
    from ... import socketio

    user = User.query.get(request.json['userid'])
    data = request.json
    current_app.logger.info("Update progress bar {} to user {}".format(data, user.websocket_id))

    socketio.emit('update_progress_bar', data, namespace='/events', room=user.websocket_id)
    return 'ok'

