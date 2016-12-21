from manage import celery
import os
from requests import post
import xml.etree.ElementTree as ET
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


class FTPError(Exception):
    def __init__(self, message):
        super(Exception, self).__init__()
        # Send E-Mail notification
        import smtplib
        logger.info("error in FTP")
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        server = smtplib.SMTP(celery.conf.SMTP_SERVER, 587)
        server.starttls()
        server.login(celery.conf.SMTP_USER, celery.conf.SMTP_PASSWORD)
        subject = 'Error in importing new XML File'
        sender = celery.conf.SENDER
        msg = "From: 'Propmatch <{sender}>' \r\nTo: 'Sender <{to}>' \r\nSubject: {subject}\r\n{msg}".format(
            subject=subject,
            sender=sender,
            to=celery.conf.TO,
            msg=message)

        server.sendmail(sender, celery.conf.TO, "{}".format(msg))
        server.quit()


@celery.task
def import_xml(file_id, strongest_site_id, user_id=None, url=None):
    """
    Import data from xml file into our ads database
    :param file_id:            The id of the downloaded file
    :param strongest_site_id:  The id of the company which we do not overwrite 
                               if we have multiple entries of the
                               same property
    :param user_id:            The user id. Should only be set when the user
                               startet the import from hand
    :param url:                The url to send the update
    :return:
    """
    import datetime
    from app.models import Time, Location, Ad, File
    from app import db

    logger.info("Start importing file")
    today = datetime.datetime.today()

    xml_file = db.session.query(File).filter(File.id == file_id).first()
    # Ignore not founded file
    if not xml_file:
        logger.error("The file with id {} was not found in the database".format(file_id))
        return

    logger.debug("Read XML file with id {}".format(xml_file.path))
    try:
        tree = ET.parse(xml_file.path)
        ads = tree.getroot()
    except Exception as e:
        logger.error("Could not read XML file " + e)
        xml_file.error = True
        xml_file.error_message = "{}".format(e)
        db.session.add(xml_file)
        db.session.commit()
        return

    # insert the actual date:
    logger.info("Prepare Time object")
    t = db.session.query(Time).filter(Time.date == today.date()).first()
    if t is None:
        business_day = True if today.weekday() < 5 else False
        quarter = (today.month - 1) // 3 + 1
        t = Time(day=today.day,
                 month=today.month,
                 year=today.year,
                 business_day=business_day,
                 quarter=quarter,
                 date=today)
        db.session.add(t)
        db.session.commit()

    # Prepare locations for fast import
    locations = {}
    db_locations = db.session.query(Location).all()
    for loc in db_locations:
        locations[loc.plz] = loc

    updated_ads = 0
    inserted_ads = 0
    not_updated_ads = set()

    # Prepare once the data dict
    data = {'userid': user_id,
            'file_id': file_id,
            'current': None,
            'total': len(ads)}
    logger.info("Start inserting ads")
    for i, ad in enumerate(ads):
        if ad[10] and ad[11].text != strongest_site_id:
            not_updated_ads.add((ad, "DUPLICATE"))
            continue

        # Check if this advertisement already exists in our database
        advertisement = db.session.query(Ad).filter(Ad.id == ad[0].text).first()
        if advertisement is None:
            # insert new add
            try:
                location = locations[int(ad[6].text)]
            except KeyError:
                # We could not find this location in our database
                not_updated_ads.add((ad, "LOCATION"))
                continue

            inserted_ads += 1
            advertisement = Ad(id=ad[0].text,
                               title=ad[1].text,
                               type=ad[2].text,
                               area=ad[3].text,
                               price=ad[4].text.replace(',', '.'),
                               rooms=ad[5].text.replace(',', '.'),
                               location=location,
                               created=t,
                               ended=t,
                               site_id=ad[11].text)
        else:  # Update ad if its newer
            if advertisement.ended.date > t.date:
                # Ignore this ad cause we have newer data
                logger.info("Outdated add")
                not_updated_ads.add((ad, "OUTDATED"))
                continue

            updated_ads += 1
            advertisement.ended = t
            # Replace price
            advertisement.price = ad[4].text.replace(',', '.')

        # Add advertisement to session
        db.session.add(advertisement)

        # Commit after 10000 entries
        if i % 5000 is 0:
            db.session.commit()

            # Only send update if user started import
            if user_id and url:
                data['current'] = i
                post(url, json=data)

    db.session.commit()
    logger.info("There are {} ads which were not inserted. "
                "{} new and {} updated".format(len(not_updated_ads),
                                               inserted_ads, updated_ads))

    # update file
    xml_file.imported = datetime.date.today()
    db.session.add(xml_file)
    db.session.commit()

    # Only send update if user started import
    if user_id and url:
        data['current'] = len(ads)
        post(url, json=data)


@celery.task
def download_file(url, user, password, filename, dest, strongest_site_id):
    """
    Download a specific file. If the file is already
    downloaded ask the user if the file shoule be downloaded again
    """
    from ftplib import FTP
    from datetime import date
    from app.models import File
    from app import db

    name = '{}.xml'.format(date.today())
    dest = '{}'.format(os.path.join(dest, name))
    f = File(name=name, path=dest)

    try:
        ftp = FTP(host=url,
                  user=user,
                  passwd=password)
    except Exception as e:
        logger.error("There was an error when loggin to ftp server {}".format(e))
        f.error = True
        f.error_message = "{}".format(e)
        db.session.add(f)
        db.session.commit()
        raise FTPError(e)

    logger.debug("Filename: {}".format(filename))
    cmd = 'RETR {}'.format(filename)
    logger.debug("CMD {}".format(cmd))

    logger.info("Start Downloading file {}".format(filename))
    file = open(dest, 'wb')
    try:
        ftp.retrbinary(cmd, file.write, blocksize=2048)
    except Exception as e:
        f.error = True
        f.error_message = "{}".format(e)
        db.session.add(f)
        db.session.commit()
        raise FTPError(e)

    logger.info("File successfully downloaded")
    f.error = False
    db.session.add(f)
    db.session.commit()

    # Import file
    import_xml.delay(f.id, strongest_site_id)
    logger.info("Start import the downloaded file")
