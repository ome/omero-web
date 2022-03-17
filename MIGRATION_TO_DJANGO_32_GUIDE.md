# OMERO.web 5.14.0 plugin migration guide

## Introduction

Django 3.2.x is now the major version that OMERO.web depends upon. All the way back to 5.6.0, this was previously Django 1.11.x. This Django version conservatism has helped us establish a very fertile, stable environment for plugin developers. However, while the usage of the plethora of Django functionality available in core OMERO.web is quite limited, upgrading your plugin to support this new version requires careful consideration.

## Background

All plugin developers are encouraged to review the release notes, in particular the *Backwards incompatible* and *Features deprecated* for all major Django versions since 1.11.x to ensure they can be compliant with the new APIs. They are as follows:

* https://docs.djangoproject.com/en/4.0/releases/2.0/
* https://docs.djangoproject.com/en/4.0/releases/2.1/
* https://docs.djangoproject.com/en/4.0/releases/2.2/
* https://docs.djangoproject.com/en/4.0/releases/3.0/
* https://docs.djangoproject.com/en/4.0/releases/3.1/
* https://docs.djangoproject.com/en/4.0/releases/3.2/

## Affected areas of core OMERO.web

### Django 2.0.x / 2.1.x

* `django.core.urlresolvers` package (deprecated since 1.10) has been replaced with `django.urls`
* Removal of case insensitive URL matching (deprecated since 1.11)
* Refactor use of QuerySet semantics in `ModelChoiceField` subclasses

### Django 3.0.x

* `django.contrib.staticfiles.templatetags` package (deprecated since 2.1) has been replaced with `django.templatetags.static`
* Update to the new field ordering style for forms

### Django 3.1.x

* Update to the new internal settings cleansing API
* Use the new package (`django.core.validators`) for empty value definitions

## Backwards compatibility

There is only one major backwards incompatible change affecting OMERO.web 5.14.0 and that is the removal of support for case insensitive URL matching. You can recognize your use of this feature by examining your `urls.py` packages for the use of `(?i)` in your matching regular expressions. If your plugin makes use of case insensitivity in URL matching, which has been deprecated since Django 1.11, we recommend that you first consider if you really need this feature. If you do you can consult the [Django 1.11 release notes](https://docs.djangoproject.com/en/4.0/releases/1.11/) for some suggested solutions on mitigation.

Apart from the aforementioned major issue, the vast majority of plugin developers will be able to remain compatible with pre and post 5.14.0 OMERO.web just by switching their use of the `django.core.urlresolvers` package to `django.urls`. This new package was present in Django 1.11.

If you are making subclasses of the OMERO.web form `ModelChoiceField` subclasses or making subclasses of your own you will likely not be able to remain backwards compatible. The same goes for if you have subclassed any OMERO.web Django forms or have created any of our own. This is especially true if you are relying on a specific form field ordering.

Finally, some of the internal Django APIs have changed substantially either in semantics or in package location. You will not likely be able to remain backwards compatible if you rely on these APIs.

## Migration examples

### `django.core.urlresolvers` package

```
-    from django.core.urlresolvers import reverse
+    from django.urls import reverse
```

### Removal of case insensitive URL matching

```
-    url(r"^(?i)webgateway/", include("omeroweb.webgateway.urls")),
+    url(r"^webgateway/", include("omeroweb.webgateway.urls")),
```

### `django.contrib.staticfiles.templatetags` package

```
-    from django.contrib.staticfiles.templatetags.staticfiles import static
+    from django.templatetags.static import static
```

### Update to the new field ordering style for forms

```
-    self.fields.keyOrder = ["server", "username", "password"]
+    self.field_order = ["server", "username", "password"]
```

### Use the new package for empty value definitions

```
-    from django.forms.fields import ChoiceField, EMPTY_VALUES
+    from django.forms.fields import ChoiceField

-    from django.core.validators import validate_email
+    from django.core.validators import validate_email, EMPTY_VALUES
```