5.15.0 (August 2022)
--------------------

## Minor features

- Show Fileset ID [#385](https://github.com/ome/omero-web/pull/385)
- Show table header when scrolling OMERO.table [#392](https://github.com/ome/omero-web/pull/392)

## Bug fixes

- Don't need ?server=1 query parameter if only 1 server [#386](https://github.com/ome/omero-web/pull/386)
- Fix zoom buttons overlaying popup panels [#389](https://github.com/ome/omero-web/pull/389)
- Fix activities panel display of long messages [#378](https://github.com/ome/omero-web/pull/378)


5.14.1 (June 2022)
------------------

## Bug fixes

- Fix Download of multiple images as png/tiff/jpeg [#369](https://github.com/ome/omero-web/pull/369)
- Fix type error for `omero.web.wsgi_threads` configuration  [#372](https://github.com/ome/omero-web/pull/372). Thanks to [Michael Barrett](https://github.com/barrettMCW)
- Update `conda create` instructions in the README [#374](https://github.com/ome/omero-web/pull/374)

5.14.0 (March 2022)
-------------------

## Documentation

- Add instructions on how to update OMERO.web plugins to Django 3.2.x ([#363](https://github.com/ome/omero-web/pull/363))


5.14.0.rc1 (March 2022)
-----------------------

## Features

- Update to Django 3.2.x ([#356](https://github.com/ome/omero-web/pull/356))
- Install Django-cors-headers by default ([#359](https://github.com/ome/omero-web/pull/359))

## Documentation

- Fix build year ([#360](https://github.com/ome/omero-web/pull/360))

5.13.0 (February 2022)
----------------------

## Features

- Handle multiple OMERO.tables on Image or Well containers ([#352](https://github.com/ome/omero-web/pull/352))
- Show sizeT in table-view of webclient centre panel ([#329](https://github.com/ome/omero-web/pull/329))
- Improve OMERO.table display, including a link to table as JSON ([#343](https://github.com/ome/omero-web/pull/343))
- OMERO.table DatasetColumn links to Dataset ([#355](https://github.com/ome/omero-web/pull/355))

## Bug fixes

- Fix non-owned data being shown in user's data usage stats ([#331](https://github.com/ome/omero-web/pull/331))
- Fix default-group dropdown chooser in User Settings ([#344](https://github.com/ome/omero-web/pull/344))
- Handle commas in OMERO.table download as CSV ([#342](https://github.com/ome/omero-web/pull/342))
- Fix link in setting documentation string ([#345](https://github.com/ome/omero-web/pull/345))
- Fix keep-alive response content-type ([#347](https://github.com/ome/omero-web/pull/347))
- Fix "Remove all filters" for Key-Value pairs ([#349](https://github.com/ome/omero-web/pull/349))

5.12.1 (December 2021)
---------------------

## Documentation

- Fix redirected link to Referrer Policy ([#345](https://github.com/ome/omero-web/pull/345))

5.12.0 (November 2021)
---------------------

## New features

- Add option to hide "Forgot password" on login page ([#313](https://github.com/ome/omero-web/pull/313))
- Add URL endpoint to return OMERO.table query as a bitmask ([#308](https://github.com/ome/omero-web/pull/308))

## Bug fixes

- Rendering settings Save-To-All includes Z and T indices ([#328](https://github.com/ome/omero-web/pull/328))
- Fix purging of Activities backlog ([#325](https://github.com/ome/omero-web/pull/325))

5.11.0 (October 2021)
---------------------

- Security vulnerability fixes for
  [2021-SV3](https://www.openmicroscopy.org/security/advisories/2021-SV3)

5.11.0.rc1 (September 2021)
---------------------------

## New features

- Plate layout improvements and configuration. See PR for details ([#270](https://github.com/ome/omero-web/pull/270))
- Configure custom favicon ([#311](https://github.com/ome/omero-web/pull/311))
- OMERO.table Shapes link to OMERO.iviewer ([#310](https://github.com/ome/omero-web/pull/310))
- URL /webgateway/table/FILE_ID/query supports col_names filter ([#305](https://github.com/ome/omero-web/pull/305))
- Improve OMERO.table download usability ([#300](https://github.com/ome/omero-web/pull/300))
- Configure default user and group for search ([#297](https://github.com/ome/omero-web/pull/297))
- Add /shape/ID endpoint to JSON API ([#291](https://github.com/ome/omero-web/pull/291))

## Bug fixes

- Fix Shift-click to multi-select Wells ([#296](https://github.com/ome/omero-web/pull/296))
- Handle parent not found on POST webclient/api/links ([#294](https://github.com/ome/omero-web/pull/294))
- Display time-stamps in local time ([#303](https://github.com/ome/omero-web/pull/303))
- Public login button uses configured login page ([#312](https://github.com/ome/omero-web/pull/312))

## Dependencies Updates

- Upgrade Underscore to 1.13.1 ([#317](https://github.com/ome/omero-web/pull/317))
- Upgrade jquery to 3.5.1, jquery.chosen to 1.8.7, jquery.form to 4.3.0, jquery.ui to 1.12.1, jstree 3.3.10 ([#180](https://github.com/ome/omero-web/pull/180))

5.9.2 (May 2021)
----------------

## Bug fixes

- Fix invalid Z/T values in webclient render_image URL ([#272](https://github.com/ome/omero-web/pull/272))
- Active group switch handles invalid group ([#273](https://github.com/ome/omero-web/pull/273))
- Fix delete of user's photo ([#274](https://github.com/ome/omero-web/pull/274))
- Don't log missing script params as Error ([#275](https://github.com/ome/omero-web/pull/275))
- Handle ?show=object-id in invalid group ([#276](https://github.com/ome/omero-web/pull/276))
- OMERO.table query case insensitive ([#277](https://github.com/ome/omero-web/pull/277))
- Fix changes that cause bugs in OMERO.mapr ([#282](https://github.com/ome/omero-web/pull/282))
- Fix User Settings page when in 'All Members' context ([#285](https://github.com/ome/omero-web/pull/285))

## New features
- Add metadata support to webgateway table endpoint ([#283](https://github.com/ome/omero-web/pull/283))


5.9.1 (March 2021)
------------------

## Bug fixes

- Fix regression introduced in 5.9.0 ([#278](https://github.com/ome/omero-web/pull/278))

5.9.0 (March 2021)
------------------

## New features

- Webclient UI supports Change Owner ([#149](https://github.com/ome/omero-web/pull/149))
- Filtering by Key-Value pairs supports autocomplete ([#250](https://github.com/ome/omero-web/pull/250))
- Support URLs as output from scripts ([#233](https://github.com/ome/omero-web/pull/233))]
- Improved install info in README ([#239](https://github.com/ome/omero-web/pull/239))]
- Migrate CI to use GitHub actions ([#240](https://github.com/ome/omero-web/pull/240))]
- Improve performance of OMERO.table loading ([#243](https://github.com/ome/omero-web/pull/243))
- OMERO.table ROI column links to ROI in OMERO.iviewer ([#264](https://github.com/ome/omero-web/pull/264))
- Disable placeholder URL popup on tree ([#257](https://github.com/ome/omero-web/pull/257))
- Add an option to set SESSION_COOKIE_PATH ([#271]https://github.com/ome/omero-web/pull/271). Thanks to [Andrey Yudin](https://github.com/andreyyudin)

## Bug fixes

- Fix Open_with handling of callbacks in right panel ([#232](https://github.com/ome/omero-web/pull/232))
- Fix /webgateway/dataset/ID/children/ URL (Thanks to [Johannes Dewender](https://github.com/JonnyJD)) ([#245](https://github.com/ome/omero-web/pull/245))
- Remove broken 'Create Shares' dialog ([#265](https://github.com/ome/omero-web/pull/265))
- Fix API ?childCount=true when zero objects found ([#249](https://github.com/ome/omero-web/pull/249))
- Fix partial loading of annotations ([#256](https://github.com/ome/omero-web/pull/256))
- Fix ignored limit in webgateway/table endpoint ([#268](https://github.com/ome/omero-web/pull/268))

- Security vulnerability fixes for
  [2021-SV1](https://www.openmicroscopy.org/security/advisories/2021-SV1),
  [2021-SV2](https://www.openmicroscopy.org/security/advisories/2021-SV2)

5.8.1 (September 2020)
----------------------

## Bug fixes

- Restore Python 3.5 compatibility ([#228](https://github.com/ome/omero-web/pull/228))

## Other updates

- Add more details to README for release process ([#220](https://github.com/ome/omero-web/pull/220))
- Run tox in travis instead of Docker ([#219](https://github.com/ome/omero-web/pull/219))
- Run black autoformatter, add pre-commit hook ([#218](https://github.com/ome/omero-web/pull/218))

5.8.0 (September 2020)
----------------------

- webclient:
   - Disable large zip file creation for data download ([#197](https://github.com/ome/omero-web/pull/197))
   - Fix 'Move to Group' when data owner not in origin group ([#212](https://github.com/ome/omero-web/pull/212))
   - History results page supports browse to data ([#206](https://github.com/ome/omero-web/pull/206))
   - Fix shortening of Companion file names ([#198](https://github.com/ome/omero-web/pull/198))
   - Fix pagination in history page and omero_table ([#203](https://github.com/ome/omero-web/pull/203))
   - Link ownership matches child owner ([#199](https://github.com/ome/omero-web/pull/199))
   - Improve download of OMERO.table as csv performance ([#192](https://github.com/ome/omero-web/pull/192))
   - Fix display of disk usage for very small percentages ([#211](https://github.com/ome/omero-web/pull/211))

- API changes:
   - @login_required(doConnectionCleanup=False) will close connection unless streaming ([#191](https://github.com/ome/omero-web/pull/191))
   - Return 404 for webgateway/imgData/ID if image not found ([#209](https://github.com/ome/omero-web/pull/209))

- Other:
   - Handle missing config for 'scripts to ignore' ([#195](https://github.com/ome/omero-web/pull/195))
   - Cap pytest-xdist to avoid psutil Travis failures ([#201](https://github.com/ome/omero-web/pull/201))

5.7.1 (July 2020)
-----------------

- webgateway

   - Always marshal tile metadata on presence of pyramid ([#193](https://github.com/ome/omero-web/pull/193))

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
