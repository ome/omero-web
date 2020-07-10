5.7.0 (July 2020)
-----------------

- webclient:
   - Preserve whitespace and linebreaks in Comments ([#150](https://github.com/ome/omero-web/pull/150))
   - Improve filtering Images by numerical Key-Value pairs ([#147](https://github.com/ome/omero-web/pull/147))
   - Fix editing of 'Shares' in webclient ([#162](https://github.com/ome/omero-web/pull/162))
   - Fix error when user logged-out and public user configured ([#154](https://github.com/ome/omero-web/pull/154))
   - No longer ignore the default thumbnail size from the configuration ([#165](https://github.com/ome/omero-web/pull/165))
   - Fix moving data in webclient tree in Python 3.5 ([#170](https://github.com/ome/omero-web/pull/170))
   - Handle no 'callback' in request.session ([#186](https://github.com/ome/omero-web/pull/186))

- API changes:
   - Add ROI support to `paths_to_object` ([#159](https://github.com/ome/omero-web/pull/159))
   - Add Shape support to `paths_to_object` ([#178](https://github.com/ome/omero-web/pull/178))
   - Add JSON API support for Experimenters and Groups ([#148](https://github.com/ome/omero-web/pull/148))

- Other:
   - Fix `render_roi_thumbnail` for unset Z/T index ([#157](https://github.com/ome/omero-web/pull/157))
   - `omero-web` now requires `omero-py 5.7.0`
   - Add doc for APPLICATION_SERVER_HOST to settings ([#177](https://github.com/ome/omero-web/pull/177))
   - Set sign_tags to True by default in .bumpversion.cfg ([#176](https://github.com/ome/omero-web/pull/176))
   - Fix new flake8 warnings ([#174](https://github.com/ome/omero-web/pull/174))
   - Add `omero-web-docker` to release process instructions ([#156](https://github.com/ome/omero-web/pull/156))


5.6.3 (March 2020)
------------------

- `omero.web.root_application`: allow "/" to be overridden ([#123](https://github.com/ome/omero-web/pull/123))
- Close sessions where user is anonymous but `is_valid_public_url` is false ([#151](https://github.com/ome/omero-web/pull/151))

5.6.2 (February 2020)
---------------------

- Fix shape_thumbnail using integer division ([#137](https://github.com/ome/omero-web/pull/137))
- Use chosen plugin for script UI values ([#135](https://github.com/ome/omero-web/pull/135))
- Rating post only ([#132](https://github.com/ome/omero-web/pull/132))
- Fix feedback url encode ([#131](https://github.com/ome/omero-web/pull/131))
- Script GUI file upload ([#128](https://github.com/ome/omero-web/pull/128))
- Script upload ([#126](https://github.com/ome/omero-web/pull/126))
- Fix webadmin search firefox ([#125](https://github.com/ome/omero-web/pull/125))
- Delete check parent links ([#124](https://github.com/ome/omero-web/pull/124))
- Map ann parent ID ([#119](https://github.com/ome/omero-web/pull/119))
- Confine projections to no more than 256MiB of raw data ([#115](https://github.com/ome/omero-web/pull/115))
- Fix color picker hex input box ([#114](https://github.com/ome/omero-web/pull/114))
- Fix and expand "open with" plugin support ([#113](https://github.com/ome/omero-web/pull/113))
- Table download ([#3](https://github.com/ome/omero-web/pull/3))

5.6.1 (January 2020)
--------------------

- Quick fix of the show downloads regex ([#109](https://github.com/ome/omero-web/pull/109))

5.6.0 (January 2020)
--------------------

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


5.5.dev2 (August 2019)
----------------------

- Improve README
- Add omeroweb.version
- Move templates to omeroweb/
- Bump to omero-py 5.5.1.dev1
- Extract code from ome/openmicroscopy
- Make minimal changes for a functioning `python setup.py` ([#1](https://github.com/ome/omero-web/pull/1))
