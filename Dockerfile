FROM docker.io/library/ubuntu:20.04 as baseimage

RUN apt-get update && \
    apt-get install -y -q \
        curl \
        python3 \
        python3-venv && \
    rm -rf /var/lib/apt/lists/* && \
    curl -sfLo /usr/local/bin/dumb-init \
        https://github.com/Yelp/dumb-init/releases/download/v1.2.2/dumb-init_1.2.2_amd64 && \
    chmod +x /usr/local/bin/dumb-init

RUN useradd -d /opt/omero/web/OMERO.web/var -m --system omero-web && \
    mkdir -p \
        /opt/omero/web/OMERO.web/bin \
        /opt/omero/web/OMERO.web/etc/grid \
        /opt/omero/web/config && \
    chown -R omero-web /opt/omero/web/OMERO.web/etc

############################################################

FROM baseimage as builder

RUN apt-get update && \
    apt-get install -y -q \
        git && \
    rm -rf /var/lib/apt/lists/*

RUN python3 -mvenv /opt/omero/web/venv3 && \
    /opt/omero/web/venv3/bin/python -m pip install --no-cache-dir \
        wheel \
        https://github.com/ome/zeroc-ice-ubuntu2004/releases/download/0.2.0/zeroc_ice-3.6.5-cp38-cp38-linux_x86_64.whl

COPY \
    .pre-commit-config.yaml \
    MANIFEST.in \
    README.rst \
    pytest.ini \
    setup.py \
    tox.ini \
    /src/
COPY .git /src/.git
COPY omero /src/omero
COPY omeroweb /src/omeroweb
COPY test /src/test

RUN /opt/omero/web/venv3/bin/python -m pip install --no-cache-dir \
        /src \
        git+https://github.com/manics/omero-cli-externalconfig.git

############################################################
# To use this as the output image run
# docker build --target=devtest

FROM builder as devtest

RUN /opt/omero/web/venv3/bin/python -m pip install --no-cache-dir \
        tox
WORKDIR /src
RUN /opt/omero/web/venv3/bin/tox -e docker
ENTRYPOINT bash

############################################################
# This is the default output image

FROM baseimage as production

COPY --from=builder /opt/omero/web/venv3 /opt/omero/web/venv3
RUN /opt/omero/web/venv3/bin/python -m pip list

COPY docker/entrypoint.sh /usr/local/bin/
COPY \
    docker/50-config.sh \
    docker/98-cleanprevious.sh \
    docker/99-run.sh /startup/
COPY docker/bin-omero.sh /opt/omero/web/OMERO.web/bin/omero
COPY docker/00-omero-web.omero /opt/omero/web/config/

USER omero-web
WORKDIR /opt/omero/web
EXPOSE 4080
ENV LANG=C.UTF-8
ENV OMERODIR=/opt/omero/web/OMERO.web/

VOLUME ["/opt/omero/web/OMERO.web/var"]
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
