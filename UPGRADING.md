# Upgrading OMERO.web

This document highlights steps that may need to be taken by developers
when upgrading OMERO.web to ensure plugins or other customizations
continue to function as expected.

## OMERO.web 5.22.0

### Django 4.2 support

OMERO.web 5.22.0 supports Django versions 3.2 to 4.2.

Django 4.2 will be required in the next minor release.

## OMERO.web 5.19.0

### Partial channel lists in render_image and render_image_region web API calls

When requesting images via the `render_image` and `render_image_region` web API
calls, the desired channel rendering settings may be omitted (to use the
default rendering settings), fully specified (to use custom settings), or 
partially specified (to combine custom settings with default rendering 
settings).  The latter method of partially specifying channel rendering settings
is now considered deprecated and should not be used in any new or updated
applications and plugins.

New API calls for requesting images using fully specified channel rendering
settings are now available as `render_image_rdef` and 
`render_image_region_rdef`.

Documentation for these API calls is available at
https://omero.readthedocs.io/en/stable/developers/Web/WebGateway.html.

## OMERO.web 5.18.0

### Connector storage in Django sessions

To prepare for upcoming Django upgrades, this upgrade changes how Connector 
objects are stored to a "persist and rehydration" strategy similar to how the 
Django authentication middleware handles model objects. 

Any downstream implementation which was directly assigning and/or retrieving 
`request.session["connector"]` will need to update their codebase:

- all usages of `request.session.get("connector")` should be replaced 
  by `Connector.from_session(request)`
- all usages of `request.session["connector"] = connector` should be 
  replaced by `connector.to_session(request)`

More information at https://github.com/ome/omero-web/pull/435

Due to the serialization change, the sessions store must be cleared before
restarting OMERO.web following this upgrade - see
https://omero.readthedocs.io/en/stable/sysadmins/omeroweb-upgrade.html#clear-the-sessions-store-optional
for more information.

### Third-party JavaScript libraries

If your plugin or customizations depend on any of the following libraries, please
make sure to check for breaking API or CSS changes.

| Library           | Previous Version | Upgraded to | Link                                                                                                                           |
|-------------------|------------------|-------------|--------------------------------------------------------------------------------------------------------------------------------|
| d3                | 3.5.17           | 7.7.0       | [https://d3js.org/](https://d3js.org/)                                                                                         |
| hammer            | 2.0.2            | 2.0.8       | [https://hammerjs.github.io/](https://hammerjs.github.io/)                                                                     |
| jquery            | 3.5.1            | 3.6.2       | [https://jquery.com/download/](https://jquery.com/download/)                                                                   |
| jquery-ui         | 1.12.1           | 1.13.2      | [https://jqueryui.com/download/](https://jqueryui.com/download/)                                                               |
| jquery.jstree     | 3.3.10           | 3.3.12      | [https://www.jstree.com/](https://www.jstree.com/)                                                                             |
| jquery.mousewheel | 3.0.6            | 3.1.12      |                                                                                                                                |
| raphael           | 2.1.0            | 2.3.0       | [https://dmitrybaranovskiy.github.io/raphael/](https://dmitrybaranovskiy.github.io/raphael/)                                   |
| underscore        | 1.13.1           | 1.13.6      | [https://underscorejs.org/](https://underscorejs.org/)                                                                         |

More information at https://github.com/ome/omero-web/pull/433

## OMERO.web 5.14.0 plugin migration guide

### Introduction

Django 3.2.x is now the major version that OMERO.web depends upon. For system administrators, the installation of `omero-web==5.14.0` will also upgrade Django and Django-cors-headers as required.
You will also need to upgrade your `omero-web` plugin apps to versions compatible with Django 3.2.
Popular apps such as `omero-iviewer`, `omero-figure`, `omero-parade`, `omero-mapr`
and `omero-webtagging` have been updated accordingly.

You many need to uninstall other Django apps such as https://pypi.org/project/django-cookies-samesite/ which is not needed for `Django 3.1+`.

The remainder of this guide is for `omero-web` plugin developers.

All the way back to 5.6.0, this was previously Django 1.11.x. This Django version conservatism has helped us establish a very fertile, stable environment for plugin developers. However, while the usage of the plethora of Django functionality available in core OMERO.web is quite limited, upgrading your plugin to support this new version requires careful consideration.

### Background

All plugin developers are encouraged to review the release notes, in particular the *Backwards incompatible* and *Features deprecated* for all major Django versions since 1.11.x to ensure they can be compliant with the new APIs. They are as follows:

* https://docs.djangoproject.com/en/4.0/releases/2.0/
* https://docs.djangoproject.com/en/4.0/releases/2.1/
* https://docs.djangoproject.com/en/4.0/releases/2.2/
* https://docs.djangoproject.com/en/4.0/releases/3.0/
* https://docs.djangoproject.com/en/4.0/releases/3.1/
* https://docs.djangoproject.com/en/4.0/releases/3.2/

### Affected areas of core OMERO.web

#### Django 2.0.x / 2.1.x

* `django.core.urlresolvers` package (deprecated since 1.10) has been replaced with `django.urls`
* Removal of case insensitive URL matching (deprecated since 1.11)
* Refactor use of QuerySet semantics in `ModelChoiceField` subclasses

#### Django 3.0.x

* `django.contrib.staticfiles.templatetags` package (deprecated since 2.1) has been replaced with `django.templatetags.static`
* Update to the new field ordering style for forms

#### Django 3.1.x

* Update to the new internal settings cleansing API
* Use the new package (`django.core.validators`) for empty value definitions

### Backwards compatibility

There is only one major backwards incompatible change affecting OMERO.web 5.14.0 and that is the removal of support for case insensitive URL matching. You can recognize your use of this feature by examining your `urls.py` packages for the use of `(?i)` in your matching regular expressions. If your plugin makes use of case insensitivity in URL matching, which has been deprecated since Django 1.11, we recommend that you first consider if you really need this feature. If you do you can consult the [Django 1.11 release notes](https://docs.djangoproject.com/en/4.0/releases/1.11/) for some suggested solutions on mitigation.

Apart from the aforementioned major issue, the vast majority of plugin developers will be able to remain compatible with pre and post 5.14.0 OMERO.web just by switching their use of the `django.core.urlresolvers` package to `django.urls`. This new package was present in Django 1.11.

If you are making subclasses of the OMERO.web form `ModelChoiceField` subclasses or making subclasses of your own you will likely not be able to remain backwards compatible. The same goes for if you have subclassed any OMERO.web Django forms or have created any of our own. This is especially true if you are relying on a specific form field ordering.

Finally, some of the internal Django APIs have changed substantially either in semantics or in package location. You will not likely be able to remain backwards compatible if you rely on these APIs.

### Migration examples

#### `django.core.urlresolvers` package

```
-    from django.core.urlresolvers import reverse
+    from django.urls import reverse
```

#### Removal of case insensitive URL matching

```
-    url(r"^(?i)webgateway/", include("omeroweb.webgateway.urls")),
+    url(r"^webgateway/", include("omeroweb.webgateway.urls")),
```

#### `django.contrib.staticfiles.templatetags` package

```
-    from django.contrib.staticfiles.templatetags.staticfiles import static
+    from django.templatetags.static import static
```

#### Update to the new field ordering style for forms

```
-    self.fields.keyOrder = ["server", "username", "password"]
+    self.field_order = ["server", "username", "password"]
```

#### Use the new package for empty value definitions

```
-    from django.forms.fields import ChoiceField, EMPTY_VALUES
+    from django.forms.fields import ChoiceField

-    from django.core.validators import validate_email
+    from django.core.validators import validate_email, EMPTY_VALUES
```
