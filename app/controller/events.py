from flask import current_app, request, jsonify, url_for
from flask_login import current_user

from .. import socketio
from ..models import File, User
from .. import db
from flask_socketio import send, emit


@socketio.on('connect', namespace='/events')
def events_connect():
    """
    This function is called when a new client is connected both side
    :return:
    """
    current_app.logger.info("Socket connection")
    try:
        websocket_id = current_user.websocket_id
    except AttributeError:
        current_app.logger.error("User not logged in")
        # User not logged in
        return

    userid = request.sid
    # Store the session to the user
    if current_user.websocket_id == userid:
        emit('userid', {'userid': current_user.id})
        return

    # User made reload
    current_user.websocket_id = request.sid
    current_app.logger.info("New socket id {} for user user {}".format(current_user.name,
                                                                       current_user.websocket_id))
    db.session.add(current_user)
    db.session.commit()
    emit('userid', {'userid': current_user.id})


@socketio.on('import', namespace='/events')
def events_connect(user_id, file_id):
    from celery_module.tasks import import_xml

    file = files = File.query.filter_by(id=file_id).first()
    if file is None:
        current_app.logger.error("File not found")
        return jsonify(error='File not found', successful=False)

    # Check if user exists
    user = User.query.get(user_id)
    if not user:
        current_app.logger.info("User was not found")
        return jsonify(error='You are not allowed', successful=False)

    current_app.logger.info("import file: {} with path: {} for user {}".format(file.id, file.path, user.id))

    import_xml.delay(file_id=file_id, strongest_site_id=current_app.config['STRONGEST_SITE_ID'],
                     user_id=user.id, url=url_for('xml_import.update_client', _external=True))
    return jsonify({}), 202


