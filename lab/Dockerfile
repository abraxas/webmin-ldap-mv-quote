FROM debian:bookworm-slim

# Pin: webmin/webmin tag 2.670 commit 3a2b2b8671c0669c129f5275b3dd1853106ae02b
LABEL version="2.670" \
      lab.pin="2.670" \
      lab.commit="3a2b2b8671c0669c129f5275b3dd1853106ae02b"

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
    WEBMIN_CONFIG=/etc/webmin \
    WEBMIN_VAR=/var/webmin

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates openssl perl \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/perl /usr/local/bin/perl

COPY . /usr/share/webmin
WORKDIR /usr/share/webmin

RUN set -eux; \
    mkdir -p /etc/webmin /var/webmin; \
    export config_dir=/etc/webmin \
           var_dir=/var/webmin \
           perl=/usr/bin/perl \
           autoos=3 \
           port=10000 \
           login=root \
           password=labroot \
           ssl=0 \
           atboot=0 \
           nostart=1 \
           noportcheck=1 \
           nochown=1 \
           nouninstall=1; \
    /bin/sh ./setup.sh; \
    test "$(cat /etc/webmin/version)" = "2.670"; \
    grep -q '^ssl=0' /etc/webmin/miniserv.conf; \
    echo "nofork=1" >> /etc/webmin/miniserv.conf

EXPOSE 10000
CMD ["/usr/bin/perl", "/usr/share/webmin/miniserv.pl", "--nofork", "/etc/webmin/miniserv.conf"]
