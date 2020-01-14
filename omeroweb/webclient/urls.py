#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#
#
# Copyright (c) 2008-2016 University of Dundee.
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
# Author: Aleksandra Tarkowska <A(dot)Tarkowska(at)dundee(dot)ac(dot)uk>, 2008.
#
# Version: 1.0
#

from django.conf import settings
from django.conf.urls import url

from omeroweb.webclient import views
from omeroweb.webgateway import views as webgateway
from omeroweb.webclient.webclient_gateway import defaultThumbnail
from django.urls import get_callable, path

viewer_view = get_callable(settings.VIEWER_VIEW)

urlpatterns = [

    # Home page is the main 'Data' page
    path('', views.load_template, {'menu': 'userdata'}, name="webindex"),

    # render main template
    url(r'^(?P<menu>((?i)userdata|public|history|search|help|usertags))/$',
        views.load_template,
        name="load_template"),
    path(
        'userdata/',
        views.load_template, {'menu': 'userdata'},
        name="userdata"),
    path(
        'history/',
        views.load_template, {'menu': 'history'},
        name="history"),

    path('login/', views.WebclientLoginView.as_view(), name="weblogin"),
    path('logout/', views.logout, name="weblogout"),
    path(
        'active_group/',
        views.change_active_group,
        name="change_active_group"),

    # The content of group/users drop-down menu
    path(
        'group_user_content/',
        views.group_user_content,
        name="group_user_content"),

    # update, display activities, E.g. delete queues, scripts etc.
    path('activities/', views.activities, name="activities"),
    path(
        'activities_json/',
        views.activities,
        {'template': 'json'},
        name="activities_json"),
    url(r'^activities_update/(?:(?P<action>clean)/)?$',
        views.activities_update,
        name="activities_update"),

    # loading data
    url(r'^load_plate/(?:(?P<o1_type>'
        r'((?i)plate|acquisition))/)'
        r'?(?:(?P<o1_id>[0-9]+)/)?$',
        views.load_plate,
        name="load_plate"),

    # chgrp. Load potential target groups, then load target P/D within chosen
    # group
    path(
        'load_chgrp_groups/',
        views.load_chgrp_groups,
        name="load_chgrp_groups"),  # Query E.g. ?Image=1,2&Dataset=3
    url(r'^load_chgrp_target/(?P<group_id>[0-9]+)/'
        r'(?P<target_type>((?i)project|dataset|screen))/$',
        views.load_chgrp_target,
        name="load_chgrp_target"),

    # load history
    url(r'^load_calendar/(?:(\d{4})/(\d{1,2})/)?$', views.load_calendar,
        name="load_calendar"),
    url(r'^load_history/(?:(\d{4})/(\d{1,2})/(\d{1,2})/)?$',
        views.load_history, name="load_history"),

    # load search
    url(r'^load_searching/(?:(?P<form>((?i)form))/)?$', views.load_searching,
        name="load_searching"),

    # metadata
    url(r'^metadata_details/(?:(?P<c_type>[a-zA-Z]+)/'
        r'(?P<c_id>[0-9]+)/)?(?:(?P<share_id>[0-9]+)/)?$',
        views.load_metadata_details,
        name="load_metadata_details"),
    url(r'^metadata_acquisition/(?P<c_type>[a-zA-Z]+)/'
        r'(?P<c_id>[0-9]+)/(?:(?P<share_id>[0-9]+)/)?$',
        views.load_metadata_acquisition,
        name="load_metadata_acquisition"),
    url(r'^metadata_preview/(?P<c_type>((?i)image|well))/'
        r'(?P<c_id>[0-9]+)/(?:(?P<share_id>[0-9]+)/)?$',
        views.load_metadata_preview,
        name="load_metadata_preview"),
    url(r'^metadata_hierarchy/(?P<c_type>[a-zA-Z]+)/'
        r'(?P<c_id>[0-9]+)/(?:(?P<share_id>[0-9]+)/)?$',
        views.load_metadata_hierarchy,
        name="load_metadata_hierarchy"),

    url(r'^get_thumbnails/(?:(?P<share_id>[0-9]+)/)?$',
        webgateway.get_thumbnails_json,
        name="get_thumbnails_json"),
    url(r'^get_thumbnail/(?P<iid>[0-9]+)/'
        r'(?:(?P<share_id>[0-9]+)/)?$',
        webgateway.get_thumbnail_json,
        {'_defcb': defaultThumbnail},
        name="get_thumbnail_json"),
    url(r'^render_thumbnail/(?P<iid>[0-9]+)/'
        r'(?:(?P<share_id>[0-9]+)/)?$',
        webgateway.render_thumbnail,
        {'_defcb': defaultThumbnail},
        name="render_thumbnail"),
    url(r'^render_thumbnail/size/(?P<w>[0-9]+)/'
        r'(?P<iid>[0-9]+)/(?:(?P<share_id>[0-9]+)/)?$',
        webgateway.render_thumbnail,
        {'_defcb': defaultThumbnail},
        name="render_thumbnail_resize"),
    path(
        'edit_channel_names/<int:imageId>/',
        views.edit_channel_names,
        name="edit_channel_names"),

    # image webgateway extention
    url(r'^(?:(?P<share_id>[0-9]+)/)?render_image_region/'
        r'(?P<iid>[0-9]+)/(?P<z>[0-9]+)/(?P<t>[0-9]+)/$',
        webgateway.render_image_region,
        name="web_render_image_region"),
    url(r'^(?:(?P<share_id>[0-9]+)/)?render_birds_eye_view/'
        r'(?P<iid>[^/]+)/(?:(?P<size>[^/]+)/)?$',
        webgateway.render_birds_eye_view,
        name="web_render_birds_eye_view"),
    url(r'^(?:(?P<share_id>[0-9]+)/)?render_image/(?P<iid>[^/]+)/'
        r'(?:(?P<z>[^/]+)/)?(?:(?P<t>[^/]+)/)?$',
        webgateway.render_image,
        name="web_render_image"),
    url(r'^(?:(?P<share_id>[0-9]+)/)?render_image_download/'
        r'(?P<iid>[^/]+)/(?:(?P<z>[^/]+)/)?(?:(?P<t>[^/]+)/)?$',
        webgateway.render_image,
        {'download': True},
        name="web_render_image_download"),
    url(r'^(?:(?P<share_id>[0-9]+)/)?img_detail/(?P<iid>[0-9]+)/$',
        viewer_view,
        name="web_image_viewer"),
    url(r'^(?:(?P<share_id>[0-9]+)/)?imgData/(?P<iid>[0-9]+)/$',
        webgateway.imageData_json,
        name="web_imageData_json"),
    url(r'^(?:(?P<share_id>[0-9]+)/)?render_row_plot/(?P<iid>[^/]+)/'
        r'(?P<z>[^/]+)/(?P<t>[^/]+)/(?P<y>[^/]+)/(?:(?P<w>[^/]+)/)?$',
        webgateway.render_row_plot,
        name="web_render_row_plot"),
    url(r'^(?:(?P<share_id>[0-9]+)/)?render_col_plot/(?P<iid>[^/]+)/'
        r'(?P<z>[^/]+)/(?P<t>[^/]+)/(?P<x>[^/]+)/(?:(?P<w>[^/]+)/)?$',
        webgateway.render_col_plot,
        name="web_render_col_plot"),
    url(r'^(?:(?P<share_id>[0-9]+)/)?render_split_channel/'
        r'(?P<iid>[^/]+)/(?P<z>[^/]+)/(?P<t>[^/]+)/$',
        webgateway.render_split_channel,
        name="web_render_split_channel"),
    path(
        'saveImgRDef/<int:iid>/',
        webgateway.save_image_rdef_json,
        name="web_save_image_rdef_json"),
    url(r'^(?:(?P<share_id>[0-9]+)/)?getImgRDef/$',
        webgateway.get_image_rdef_json,
        name="web_get_image_rdef_json"),
    url(r'^(?:(?P<share_id>[0-9]+)/)?copyImgRDef/$',
        webgateway.copy_image_rdef_json,
        name="copy_image_rdef_json"),
    url(r'^(?:(?P<share_id>[0-9]+)/)?luts/$',
        webgateway.listLuts_json,
        name="web_list_luts"),


    # Fileset query (for delete or chgrp dialogs) obj-types and ids in REQUEST
    # data
    url(r'^fileset_check/(?P<action>((?i)delete|chgrp))/$',
        views.fileset_check,
        name="fileset_check"),

    # chgrp dry run - 'group_id', obj-types and ids in POST data.
    # E.g. Dataset=1,2,3 & Fileset=4. Multiple datatypes in one chgrp.
    path('chgrpDryRun/', views.chgrpDryRun, name="chgrpDryRun"),

    # Popup for downloading original archived files for images
    path(
        'download_placeholder/', views.download_placeholder,
        name="download_placeholder"),

    # chgrp - 'group_id', obj-types and ids in POST data
    path('chgrp/', views.chgrp, name="chgrp"),

    # annotations
    url(r'^action/(?P<action>[a-zA-Z]+)/(?:(?P<o_type>[a-zA-Z]+)/)'
        r'?(?:(?P<o_id>[0-9]+)/)?$',
        views.manage_action_containers,
        name="manage_action_containers"),
    path('batch_annotate/', views.batch_annotate, name="batch_annotate"),
    path('annotate_tags/', views.annotate_tags, name="annotate_tags"),
    path('marshal_tagging_form_data/', views.marshal_tagging_form_data,
         name="marshal_tagging_form_data"),
    path(
        'annotate_rating/',
        views.annotate_rating,
        name="annotate_rating"),
    path(
        'annotate_comment/',
        views.annotate_comment,
        name="annotate_comment"),
    path('annotate_file/', views.annotate_file, name="annotate_file"),
    path('annotate_map/', views.annotate_map, name="annotate_map"),
    path(
        'annotation/<int:annId>/',
        views.download_annotation,
        name="download_annotation"),
    url(r'^load_original_metadata/(?P<imageId>[0-9]+)/'
        r'(?:(?P<share_id>[0-9]+)/)?$',
        views.load_original_metadata,
        name="load_original_metadata"),
    path(
        'download_orig_metadata/<int:imageId>/',
        views.download_orig_metadata,
        name="download_orig_metadata"),

    path('avatar/<int:oid>/', views.avatar, name="avatar"),


    # scripting service urls
    path(
        'list_scripts/',
        views.list_scripts,
        name="list_scripts"),  # returns html list of scripts - click to run
    path(
        'script_ui/<int:scriptId>/',
        views.script_ui,
        name='script_ui'),  # shows a form for running a script
    path(
        'script_run/<int:scriptId>/',
        views.script_run,
        name='script_run'),  # runs the script - parameters in POST
    path(
        'get_original_file/<int:fileId>/',
        views.get_original_file,
        name="get_original_file"),  # for stderr, stdout etc
    path(
        'download_original_file/<int:fileId>/',
        views.get_original_file,
        {'download': True},
        name="download_original_file"),  # for stderr, stdout etc
    url(r'^figure_script/(?P<scriptName>'
        r'((?i)SplitView|Thumbnail|MakeMovie))/$',
        views.figure_script,
        name='figure_script'),  # shows a form for running a script

    # ome_tiff_script: generate OME-TIFF and attach to image (use script
    # service). Must be POST
    path(
        'ome_tiff_script/<int:imageId>/',
        views.ome_tiff_script,
        name='ome_tiff_script'),
    path(
        'ome_tiff_info/<int:imageId>/',
        views.ome_tiff_info,
        name='ome_tiff_info'),

    # ping OMERO server to keep session alive
    path('keepalive_ping/', views.keepalive_ping, name="keepalive_ping"),

    # Load data, but with JSON.
    # url(r'^api/$', None, name='api'),
    path(
        'api/groups/', views.api_group_list,
        name='api_groups'),

    path(
        'api/experimenters/', views.api_experimenter_list,
        name='api_experimenters'),
    path(
        'api/experimenters/<int:experimenter_id>/',
        views.api_experimenter_detail, name='api_experimenter'),

    # Generic container list. This is necessary as an experimenter may have
    # datasets/etc which do not belong to any project
    path('api/containers/', views.api_container_list, name='api_containers'),

    path('api/datasets/', views.api_dataset_list, name='api_datasets'),

    path('api/images/', views.api_image_list, name='api_images'),

    # special case: share_id not allowed in query string since we
    # just want to allow share connection for this url ONLY.
    path(
        'api/share_images/<int:share_id>/', views.api_image_list,
        name='api_share_images'),

    path('api/plates/', views.api_plate_list, name='api_plates'),

    path(
        'api/plate_acquisitions/', views.api_plate_acquisition_list,
        name='api_plate_acquisitions'),

    # POST to create link, DELETE to remove.
    # links in request.body json, e.g. {"dataset":{"10":{"image":[1,2,3]}}}
    path('api/links/', views.api_links, name='api_links'),

    # Retrieve paths to an object
    path(
        'api/paths_to_object/', views.api_paths_to_object,
        name='api_paths_to_object'),

    path(
        'api/tags/', views.api_tags_and_tagged_list,
        name='api_tags_and_tagged'),

    path(
        'api/annotations/', views.api_annotations,
        name='api_annotations'),

    path('api/shares/', views.api_share_list, name='api_shares'),
]
