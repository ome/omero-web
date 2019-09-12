FROM centos:centos7
RUN localedef -i en_US -f UTF-8 en_US.UTF-8
ENV LANG='en_US.UTF-8' LANGUAGE='en_US:en' LC_ALL='en_US.UTF-8'
RUN yum install -y centos-release-scl \
 && yum install -y rh-python36 \
 && yum install -y python-virtualenv \
 && yum install -y openssl-devel git \
 && virtualenv /py2 && /py2/bin/pip install -U pip tox future wheel
ENV PATH=/opt/rh/rh-python36/root/bin/:$PATH
RUN python -m venv /py3 && /py3/bin/pip install -U pip tox future wheel

ENV VIRTUAL_ENV=/py3
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Optimize for fixing tests
COPY *.py /src/
COPY README.rst /src
COPY MANIFEST.in /src
COPY omero /src/omero
COPY omeroweb /src/omeroweb
WORKDIR /src

# Copy test-related files and run
COPY *.ini /src/
COPY test /src/test
ENTRYPOINT ["/py3/bin/tox"]