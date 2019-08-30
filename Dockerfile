FROM centos:centos7
RUN yum install -y python-setuptools python-virtualenv git
RUN virtualenv /v && /v/bin/pip install twine restructuredtext-lint
RUN /v/bin/pip install https://github.com/ome/zeroc-ice-py-centos7/releases/download/0.1.0/zeroc_ice-3.6.4-cp27-cp27mu-linux_x86_64.whl
RUN /v/bin/pip install omero-py
COPY . /src
WORKDIR /src
RUN /v/bin/rst-lint README.rst
RUN /v/bin/python setup.py sdist
RUN /v/bin/pip install dist/omero-web*gz
