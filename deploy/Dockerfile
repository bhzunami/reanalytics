FROM ubuntu:latest
MAINTAINER Nicolas Mauchle <nicolas@nicolasmauchle.ch>

RUN apt-get update && apt-get install -y python3-pip git libpq-dev nginx supervisor

COPY reanalytics.conf etc/nginx/sites-available/
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
RUN locale-gen en_US.UTF-8

WORKDIR /root

RUN rm /etc/nginx/sites-enabled/default \
    && ln -s /etc/nginx/sites-available/reanalytics.conf /etc/nginx/sites-enabled/reanalytics.conf \
    && echo "daemon off;" >> /etc/nginx/nginx.conf


# Clone repo
RUN pip3 install --upgrade pip && git clone https://github.com/bhzunami/reanalytics.git


RUN mkdir /root/reanalytics/data \
    && mkdir /root/reanalytics/reports \
    && mkdir /root/reanalytics/logs \
    && pip3 install -r /root/reanalytics/requirements.txt \
    && chown -R www-data:www-data /root/reanalytics \
    && chmod 755 /root/ \
    && chown -R www-data:www-data /var/log

ENV FLASK_CONFIG=production

# FTP
ENV FTP_URL=server36.cyon.ch
ENV FTP_USER=
ENV FTP_PASSWORD=
ENV FTP_FILE_NAME=allesralle.xml
ENV FTP_INITIAL_FILE_NAME=allesralle_full.xml

#Avisum
ENV DEFAULT_USER_EMAIL=
ENV DEFAULT_USER_NAME=
ENV DEFAULT_PASSWORD=

# SMTP
ENV SMTP_SERVER=
ENV SMTP_USER=
ENV SMTP_PASSWORD=

WORKDIR /root/reanalytics

#CMD ["tail", "-f", "/dev/null"]
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
#CMD python3 manage.py initialize && /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
