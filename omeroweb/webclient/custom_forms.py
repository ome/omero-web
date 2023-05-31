#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#
# Copyright (C) 2011 University of Dundee & Open Microscopy Environment.
# All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import re

from django import forms
from django.forms.widgets import SelectMultiple, MultipleHiddenInput

from django.forms.fields import Field
from django.forms import ModelChoiceField, ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils.encoding import smart_str
from django.core.validators import EMPTY_VALUES

from omero_model_FileAnnotationI import FileAnnotationI
from omero_model_TagAnnotationI import TagAnnotationI
from omero_model_LongAnnotationI import LongAnnotationI

##################################################################
# Fields


class MultiEmailField(forms.Field):
    def clean(self, value):
        if not value:
            raise forms.ValidationError("No email.")
        if value.count(" ") > 0:
            raise forms.ValidationError('Use only separator ";". Remove every space.')
        emails = value.split(";")
        for email in emails:
            if not self.is_valid_email(email):
                raise forms.ValidationError(
                    '%s is not a valid e-mail address. Use separator ";"' % email
                )
        return emails

    def is_valid_email(self, email):
        email_pat = re.compile(
            r"(?:^|\s)[-a-z0-9_.]+@(?:[-a-z0-9]+\.)+[a-z]{2,6}(?:\s|$)", re.IGNORECASE
        )
        return email_pat.match(email) is not None


class UrlField(forms.Field):
    def clean(self, value):
        if not value:
            raise forms.ValidationError("No url.")
        if not self.is_valid_url(value):
            raise forms.ValidationError("%s is not a valid url" % value)
        return value

    def is_valid_url(self, url):
        url_pat = re.compile(
            r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|"
            "(?:%[0-9a-fA-F][0-9a-fA-F]))+",
            re.IGNORECASE,
        )
        return url_pat.match(url) is not None


##################################################################
# Metadata queryset iterator for group form


class MetadataQuerySetIterator(object):
    def __init__(self, queryset, empty_label):
        self.queryset = queryset
        self.empty_label = empty_label

    def __iter__(self):
        if self.empty_label is not None:
            yield ("", self.empty_label)
        for obj in self.queryset:
            yield (obj.value, smart_str(obj.value))


class MetadataModelChoiceField(ModelChoiceField):
    @property
    def choices(self):
        # If self._choices is set, then somebody must have manually set
        # the property self.choices. In this case, just return self._choices.
        if hasattr(self, "_choices"):
            return self._choices
        # Otherwise, execute the QuerySet in self.queryset to determine the
        # choices dynamically. Return a fresh QuerySetIterator that has not
        # been consumed. Note that we're instantiating a new QuerySetIterator
        # *each* time _get_choices() is called (and, thus, each time
        # self.choices is accessed) so that we can ensure the QuerySet has not
        # been consumed.
        return MetadataQuerySetIterator(self.queryset, self.empty_label)

    def _set_queryset(self, queryset):
        self._queryset = queryset
        self.widget.choices = self.choices

    queryset = property(ModelChoiceField._get_queryset, _set_queryset)

    def clean(self, value):
        Field.clean(self, value)
        if value in EMPTY_VALUES:
            return None
        res = False
        for q in self.queryset:
            if int(value) == q.id:
                res = True
        if not res:
            raise ValidationError(self.error_messages["invalid_choice"])
        return value


class AnnotationQuerySetIterator(object):
    def __init__(self, queryset, empty_label):
        self.queryset = queryset
        self.empty_label = empty_label

    def __iter__(self):
        if self.empty_label is not None:
            yield ("", self.empty_label)
        for obj in self.queryset:
            textValue = None
            if isinstance(obj._obj, FileAnnotationI):
                file_name = obj.getFileName()
                if not file_name:
                    textValue = "No name. ID %s" % obj.id
                else:
                    textValue = (
                        len(file_name) < 45 and file_name or (file_name[:42] + "...")
                    )
            elif isinstance(obj._obj, TagAnnotationI):
                if obj.textValue is not None:
                    if obj.ns is not None and obj.ns != "":
                        textValue = (
                            (len(obj.textValue) < 45)
                            and ("%s (tagset)" % obj.textValue)
                            or ("%s (tagset)" % obj.textValue[:42] + "...")
                        )
                    else:
                        textValue = (
                            (len(obj.textValue) < 45)
                            and (obj.textValue)
                            or (obj.textValue[:42] + "...")
                        )
            elif isinstance(obj._obj, LongAnnotationI):
                textValue = obj.longValue
            else:
                textValue = obj.textValue

            if isinstance(textValue, str):
                length = len(textValue)
                if length > 55:
                    textValue = "%s..." % textValue[:55]
            oid = obj.id
            yield (oid, smart_str(textValue))


class AnnotationModelChoiceField(ModelChoiceField):
    @property
    def choices(self):
        # If self._choices is set, then somebody must have manually set
        # the property self.choices. In this case, just return self._choices.
        if hasattr(self, "_choices"):
            return self._choices
        # Otherwise, execute the QuerySet in self.queryset to determine the
        # choices dynamically. Return a fresh QuerySetIterator that has not
        # been consumed. Note that we're instantiating a new QuerySetIterator
        # *each* time _get_choices() is called (and, thus, each time
        # self.choices is accessed) so that we can ensure the QuerySet has not
        # been consumed.
        return AnnotationQuerySetIterator(self.queryset, self.empty_label)

    def _set_queryset(self, queryset):
        self._queryset = queryset
        self.widget.choices = self.choices

    queryset = property(ModelChoiceField._get_queryset, _set_queryset)

    def clean(self, value):
        Field.clean(self, value)
        if value in EMPTY_VALUES:
            return None
        res = False
        for q in self.queryset:
            if int(value) == q.id:
                res = True
        if not res:
            raise ValidationError(self.error_messages["invalid_choice"])
        return value


class AnnotationModelMultipleChoiceField(AnnotationModelChoiceField):
    """A MultipleChoiceField whose choices are a model QuerySet."""

    hidden_widget = MultipleHiddenInput
    default_error_messages = {
        "list": _("Enter a list of values."),
        "invalid_choice": _(
            "Select a valid choice. That choice is not one" " of the available choices."
        ),
    }

    def __init__(
        self,
        queryset,
        required=True,
        widget=SelectMultiple,
        label=None,
        initial=None,
        help_text=None,
        *args,
        **kwargs
    ):
        super(AnnotationModelMultipleChoiceField, self).__init__(
            queryset=queryset,
            empty_label=None,
            required=required,
            widget=widget,
            label=label,
            initial=initial,
            help_text=help_text,
            *args,
            **kwargs,
        )

    def clean(self, value):
        if self.required and not value:
            raise ValidationError(self.error_messages["required"])
        elif not self.required and not value:
            return []
        if not isinstance(value, (list, tuple)):
            raise ValidationError(self.error_messages["list"])
        final_values = []
        for val in value:
            try:
                int(val)
            except Exception:
                raise ValidationError(self.error_messages["invalid_choice"])
            else:
                res = False
                for q in self.queryset:
                    if int(val) == q.id:
                        res = True
                if not res:
                    raise ValidationError(self.error_messages["invalid_choice"])
                else:
                    final_values.append(val)
        return final_values


# Object queryset iterator for group form
class ObjectQuerySetIterator(object):
    def __init__(self, queryset, empty_label):
        self.queryset = queryset
        self.empty_label = empty_label

    def __iter__(self):
        if self.empty_label is not None:
            yield ("", self.empty_label)
        for obj in self.queryset:
            if hasattr(obj.id, "val"):
                yield (obj.id.val, smart_str(obj.id.val))
            else:
                yield (obj.id, smart_str(obj.id))


class ObjectModelChoiceField(ModelChoiceField):
    @property
    def choices(self):
        # If self._choices is set, then somebody must have manually set
        # the property self.choices. In this case, just return self._choices.
        if hasattr(self, "_choices"):
            return self._choices
        # Otherwise, execute the QuerySet in self.queryset to determine the
        # choices dynamically. Return a fresh QuerySetIterator that has not
        # been consumed. Note that we're instantiating a new QuerySetIterator
        # *each* time _get_choices() is called (and, thus, each time
        # self.choices is accessed) so that we can ensure the QuerySet has not
        # been consumed.
        return ObjectQuerySetIterator(self.queryset, self.empty_label)

    def _set_queryset(self, queryset):
        self._queryset = queryset
        self.widget.choices = self.choices

    queryset = property(ModelChoiceField._get_queryset, _set_queryset)

    def clean(self, value):
        Field.clean(self, value)
        if value in EMPTY_VALUES:
            return None
        res = False
        for q in self.queryset:
            if hasattr(q.id, "val"):
                if int(value) == q.id.val:
                    res = True
            else:
                if int(value) == q.id:
                    res = True
        if not res:
            raise ValidationError(self.error_messages["invalid_choice"])
        return value


class ObjectModelMultipleChoiceField(ObjectModelChoiceField):
    """A MultipleChoiceField whose choices are a model QuerySet."""

    hidden_widget = MultipleHiddenInput
    default_error_messages = {
        "list": _("Enter a list of values."),
        "invalid_choice": _(
            "Select a valid choice. That choice is not one" " of the available choices."
        ),
    }

    def __init__(
        self,
        queryset,
        required=True,
        widget=SelectMultiple,
        label=None,
        initial=None,
        help_text=None,
        *args,
        **kwargs
    ):
        super(ObjectModelMultipleChoiceField, self).__init__(
            queryset=queryset,
            empty_label=None,
            required=required,
            widget=widget,
            label=label,
            initial=initial,
            help_text=help_text,
            *args,
            **kwargs,
        )

    def clean(self, value):
        if self.required and not value:
            raise ValidationError(self.error_messages["required"])
        elif not self.required and not value:
            return []
        if not isinstance(value, (list, tuple)):
            raise ValidationError(self.error_messages["list"])
        final_values = []
        for val in value:
            try:
                int(val)
            except Exception:
                raise ValidationError(self.error_messages["invalid_choice"])
            else:
                res = False
                for q in self.queryset:
                    if hasattr(q.id, "val"):
                        if int(val) == q.id.val:
                            res = True
                    else:
                        if int(val) == q.id:
                            res = True
                if not res:
                    raise ValidationError(self.error_messages["invalid_choice"])
                else:
                    final_values.append(val)
        return final_values


# Custom widget and validation for multiple file uploads
# See https://docs.djangoproject.com/en/3.2/topics/http/
# file-uploads/#uploading-multiple-files
class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result
