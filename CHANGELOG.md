
## API Changes

 - OMERO.web now uses Django 1.11, upgraded from Django 1.8.

 - Urls must be referenced by ```name``` not path.to.view.method (previously some webgateway URLS lacked a name). For example, instead of ```{% url 'webgateway.views.render_image' image_id theZ theT %}```, use ```{% url 'webgateway_render_image' image_id theZ theT %}```.

# 5.6.dev2 (October 2019)


# 5.6.dev1 (October 2019)


# 5.5.dev2 (August 2019)


# 5.5.dev1 (August 2019)
