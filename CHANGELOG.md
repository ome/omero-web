# 5.6.dev6 (November 2019)

- Fix `omero_ext.path` import (#77)
- Add `omero.web.nginx_server_extra_config` property (#80)
- Use cached config.xml in `omero.webgateway.getClientSettings` (#83)
- Fix dialogs for thumbnail figure and split-view figure scripts (#73)

## API changes

- OMERO.web now fails to start when `<app>.urls` fails to import (#79)

# 5.6.dev5 (November 2019)

- Moving to production bug fixes

# 5.6.dev4 (November 2019)

- Upgrade minimum requirement to omero-py 5.6.dev4
- Numerous test fixes

# 5.6.dev3 (November 2019)

- Loosen version checks to support 5.5 with 5.6 (#32)
- Numerous test fixes

## API Changes

- OMERO.web now uses Django 1.11, upgraded from Django 1.9.
- omeroweb.http renamed to omeroweb.httprsp to avoid import name
  clashes with Django http.

# 5.6.dev2 (October 2019)

## API Changes

- OMERO.web now uses Django 1.9, upgraded from Django 1.8.
- URLs must be referenced by `name` not path.to.view.method (previously
  some webgateway URLS lacked a name). For example, instead of
  `{% url 'webgateway.views.render_image' image_id theZ theT %}`, use
  `{% url 'webgateway_render_image' image_id theZ theT %}`.

# 5.6.dev1 (October 2019)

- First version of python3 support
- Focus on getting unit tests passing
- Instructions for dev installation

# 5.5.dev2 (August 2019)

- Improve README
- Add omeroweb.version
- Move templates to omeroweb/
- Bump to omero-py 5.5.1.dev1

# 5.5.dev1 (August 2019)

- Extract code from ome/openmicroscopy
- Make minimal changes for a functioning `python setup.py` (#1)
