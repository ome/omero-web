
# 5.6.0 (January 2020)

- Remove support for Python 2 ([#103](https://github.com/ome/omero-web/pull/103))
- Remove requirement files ([#107](https://github.com/ome/omero-web/pull/107))
- Use BytesIO for default Thumbnail ([#104](https://github.com/ome/omero-web/pull/104))
- omero-web requires OMERODIR ([#100](https://github.com/ome/omero-web/pull/100))
- Ignore OMERO_HOME in settings.py ([#98](https://github.com/ome/omero-web/pull/98))
- Better exception handling of custom settings ([#94](https://github.com/ome/omero-web/pull/94))
- Add support for extra NGINX server configuration ([#90](https://github.com/ome/omero-web/pull/90))
- Fix ROI maks and thumbnails ([#92](https://github.com/ome/omero-web/pull/92))
- Fix script result failures ([#87](https://github.com/ome/omero-web/pull/87))
- Fix download of multiple images in a zip ([#76](https://github.com/ome/omero-web/pull/76))
- Fix race condition while closing tables ([#25](https://github.com/ome/omero-web/pull/25))
- Fix `omero_ext.path` import ([#77](https://github.com/ome/omero-web/pull/77))
- Add `omero.web.nginx_server_extra_config` property ([#80](https://github.com/ome/omero-web/pull/80))
- Use cached config.xml in `omero.webgateway.getClientSettings` ([#83](https://github.com/ome/omero-web/pull/83))
- Fix dialogs for thumbnail figure and split-view figure scripts ([#73](https://github.com/ome/omero-web/pull/73))
- Loosen version checks to support 5.5 with 5.6 ([#32](https://github.com/ome/omero-web/pull/32))

## API changes

- OMERO.web now fails to start when `<app>.urls` fails to import ([#79](https://github.com/ome/omero-web/pull/79))
- OMERO.web uses Django 1.11, upgraded from Django 1.8.
- omeroweb.http renamed to omeroweb.httprsp to avoid import name
  clashes with Django http.
- URLs must be referenced by `name` not path.to.view.method (previously
  some webgateway URLS lacked a name). For example, instead of
  `{% url 'webgateway.views.render_image' image_id theZ theT %}`, use
  `{% url 'webgateway_render_image' image_id theZ theT %}`.


# 5.5.dev2 (August 2019)

- Improve README
- Add omeroweb.version
- Move templates to omeroweb/
- Bump to omero-py 5.5.1.dev1
- Extract code from ome/openmicroscopy
- Make minimal changes for a functioning `python setup.py` ([#1](https://github.com/ome/omero-web/pull/1))
