FROM python:3-alpine

MAINTAINER Igor Giovannini <info@igorgiovannini.ch>

COPY . /usr/src/app/
WORKDIR /usr/src/app/
RUN   apk add --no-cache ffmpeg && \
  pip install -r ./requirements.txt && \
  rm -rf /var/lib/apt/lists/* && \
  chmod +x ./startup.sh && \
  echo 'http://nl.alpinelinux.org/alpine/edge/main' > /etc/apk/repositories && \
  echo 'http://nl.alpinelinux.org/alpine/edge/community' >> /etc/apk/repositories && \
  echo 'http://nl.alpinelinux.org/alpine/edge/testing' >> /etc/apk/repositories && \
  apk update && apk upgrade && apk add \
	bash redis apache2 php7-apache2 curl ca-certificates php7 php7-phar php7-json php7-iconv php7-openssl tzdata openntpd nano && \
  apk add \
	php7-ftp \
	php7-xdebug \
	php7-mcrypt \
	php7-soap \
	php7-gmp \
	php7-pdo_odbc \
	php7-dom \
	php7-pdo \
	php7-zip \
	php7-bcmath \
	php7-gd \
	php7-odbc \
	php7-gettext \
	php7-xmlreader \
	php7-xmlrpc \
	php7-bz2 \
	php7-pdo_dblib \
	php7-curl \
	php7-ctype \
	php7-session \
	php7-redis && \
	cp /usr/bin/php7 /usr/bin/php && \
  rm -f /var/cache/apk/*

# Add apache to run and configure
RUN mkdir /run/apache2 \
    && sed -i "s/#LoadModule\ rewrite_module/LoadModule\ rewrite_module/" /etc/apache2/httpd.conf \
    && sed -i "s/#LoadModule\ session_module/LoadModule\ session_module/" /etc/apache2/httpd.conf \
    && sed -i "s/#LoadModule\ session_cookie_module/LoadModule\ session_cookie_module/" /etc/apache2/httpd.conf \
    && sed -i "s/#LoadModule\ session_crypto_module/LoadModule\ session_crypto_module/" /etc/apache2/httpd.conf \
    && sed -i "s/#LoadModule\ deflate_module/LoadModule\ deflate_module/" /etc/apache2/httpd.conf \
    && sed -i "s#^DocumentRoot \".*#DocumentRoot \"/usr/src/app/websrv/downloadlr-wapi\"#g" /etc/apache2/httpd.conf \
    && sed -i "s#/var/www/localhost/htdocs#/usr/src/app/websrv/downloadlr-wapi#" /etc/apache2/httpd.conf \
    && printf "\n<Directory \"/usr/src/app/websrv/downloadlr-wapi\">\n\tAllowOverride All\n</Directory>\n" >> /etc/apache2/httpd.conf

EXPOSE 80
EXPOSE 34567
EXPOSE 6379
VOLUME ["/data"]
VOLUME ["/downloads"]
CMD ["./startup.sh"]
