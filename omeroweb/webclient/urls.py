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
from django.urls import re_path

from omeroweb.webclient import views
from omeroweb.webgateway import views as webgateway
from omeroweb.webclient.webclient_gateway import defaultThumbnail
from django.urls import get_callable

viewer_view = get_callable(settings.VIEWER_VIEW)

urlpatterns = [
    # Home page is the main 'Data' page
    re_path(r"^$", views.load_template, {"menu": "userdata"}, name="webindex"),
    # render main template
    re_path(
        r"^(?P<menu>(userdata|public|history|search|help|usertags))/$",
        views.load_template,
        name="load_template",
    ),
    re_path(r"^userdata/$", views.load_template, {"menu": "userdata"}, name="userdata"),
    re_path(r"^history/$", views.load_template, {"menu": "history"}, name="history"),
    re_path(r"^login/$", views.WebclientLoginView.as_view(), name="weblogin"),
    re_path(r"^logout/$", views.logout, name="weblogout"),
    re_path(r"^active_group/$", views.change_active_group, name="change_active_group"),
    # The content of group/users drop-down menu
    re_path(
        r"^group_user_content/$", views.group_user_content, name="group_user_content"
    ),
    # update, display activities, E.g. delete queues, scripts etc.
    re_path(r"^activities/", views.activities, name="activities"),
    re_path(
        r"^activities_json/",
        views.activities,
        {"template": "json"},
        name="activities_json",
    ),
    re_path(
        r"^activities_update/(?:(?P<action>clean)/)?$",
        views.activities_update,
        name="activities_update",
    ),
    # loading data
    re_path(
        r"^load_plate/(?:(?P<o1_type>"
        r"(plate|acquisition))/)"
        r"?(?:(?P<o1_id>[0-9]+)/)?$",
        views.load_plate,
        name="load_plate",
    ),
    # chgrp. Load potential target groups, then load target P/D within chosen
    # group
    re_path(
        r"^load_chgrp_groups/$", views.load_chgrp_groups, name="load_chgrp_groups"
    ),  # Query E.g. ?Image=1,2&Dataset=3
    re_path(
        r"^load_chgrp_target/(?P<group_id>[0-9]+)/"
        r"(?P<target_type>(project|dataset|screen))/$",
        views.load_chgrp_target,
        name="load_chgrp_target",
    ),
    # load history
    re_path(
        r"^load_calendar/(?:(\d{4})/(\d{1,2})/)?$",
        views.load_calendar,
        name="load_calendar",
    ),
    re_path(
        r"^load_history/(?:(\d{4})/(\d{1,2})/(\d{1,2})/)?$",
        views.load_history,
        name="load_history",
    ),
    # load search
    re_path(
        r"^load_searching/(?:(?P<form>(form))/)?$",
        views.load_searching,
        name="load_searching",
    ),
    # metadata
    re_path(
        r"^metadata_details/(?:(?P<c_type>[a-zA-Z]+)/"
        r"(?P<c_id>[0-9]+)/)?(?:(?P<share_id>[0-9]+)/)?$",
        views.load_metadata_details,
        name="load_metadata_details",
    ),
    re_path(
        r"^metadata_acquisition/(?P<c_type>[a-zA-Z]+)/"
        r"(?P<c_id>[0-9]+)/(?:(?P<share_id>[0-9]+)/)?$",
        views.load_metadata_acquisition,
        name="load_metadata_acquisition",
    ),
    re_path(
        r"^metadata_preview/(?P<c_type>(image|well))/"
        r"(?P<c_id>[0-9]+)/(?:(?P<share_id>[0-9]+)/)?$",
        views.load_metadata_preview,
        name="load_metadata_preview",
    ),
    re_path(
        r"^metadata_hierarchy/(?P<c_type>[a-zA-Z]+)/"
        r"(?P<c_id>[0-9]+)/(?:(?P<share_id>[0-9]+)/)?$",
        views.load_metadata_hierarchy,
        name="load_metadata_hierarchy",
    ),
    re_path(
        r"^get_thumbnails/(?:(?P<share_id>[0-9]+)/)?$",
        webgateway.get_thumbnails_json,
        name="get_thumbnails_json",
    ),
    re_path(
        r"^get_thumbnail/(?P<iid>[0-9]+)/" r"(?:(?P<share_id>[0-9]+)/)?$",
        webgateway.get_thumbnail_json,
        {"_defcb": defaultThumbnail},
        name="get_thumbnail_json",
    ),
    re_path(
        r"^render_thumbnail/(?P<iid>[0-9]+)/" r"(?:(?P<share_id>[0-9]+)/)?$",
        webgateway.render_thumbnail,
        {"_defcb": defaultThumbnail},
        name="render_thumbnail",
    ),
    re_path(
        r"^render_thumbnail/size/(?P<w>[0-9]+)/"
        r"(?P<iid>[0-9]+)/(?:(?P<share_id>[0-9]+)/)?$",
        webgateway.render_thumbnail,
        {"_defcb": defaultThumbnail},
        name="render_thumbnail_resize",
    ),
    re_path(
        r"^edit_channel_names/(?P<imageId>[0-9]+)/$",
        views.edit_channel_names,
        name="edit_channel_names",
    ),
    # image webgateway extention
    re_path(
        r"^(?:(?P<share_id>[0-9]+)/)?render_image_region/"
        r"(?P<iid>[0-9]+)/(?P<z>[0-9]+)/(?P<t>[0-9]+)/$",
        webgateway.render_image_region,
        name="web_render_image_region",
    ),
    re_path(
        r"^(?:(?P<share_id>[0-9]+)/)?render_birds_eye_view/"
        r"(?P<iid>[0-9]+)/(?:(?P<size>[0-9]+)/)?$",
        webgateway.render_birds_eye_view,
        name="web_render_birds_eye_view",
    ),
    re_path(
        r"^(?:(?P<share_id>[0-9]+)/)?render_image/(?P<iid>[0-9]+)/"
        r"(?:(?P<z>[0-9]+)/)?(?:(?P<t>[0-9]+)/)?$",
        webgateway.render_image,
        name="web_render_image",
    ),
    re_path(
        r"^(?:(?P<share_id>[0-9]+)/)?render_image_download/"
        r"(?P<iid>[0-9]+)/(?:(?P<z>[0-9]+)/)?(?:(?P<t>[0-9]+)/)?$",
        webgateway.render_image,
        {"download": True},
        name="web_render_image_download",
    ),
    re_path(
        r"^(?:(?P<share_id>[0-9]+)/)?img_detail/(?P<iid>[0-9]+)/$",
        viewer_view,
        name="web_image_viewer",
    ),
    re_path(
        r"^(?:(?P<share_id>[0-9]+)/)?imgData/(?P<iid>[0-9]+)/$",
        webgateway.imageData_json,
        name="web_imageData_json",
    ),
    re_path(
        r"^(?:(?P<share_id>[0-9]+)/)?render_row_plot/(?P<iid>[0-9]+)/"
        r"(?P<z>[0-9]+)/(?P<t>[0-9]+)/(?P<y>[0-9]+)/(?:(?P<w>[0-9]+)/)?$",
        webgateway.render_row_plot,
        name="web_render_row_plot",
    ),
    re_path(
        r"^(?:(?P<share_id>[0-9]+)/)?render_col_plot/(?P<iid>[0-9]+)/"
        r"(?P<z>[0-9]+)/(?P<t>[0-9]+)/(?P<x>[0-9]+)/(?:(?P<w>[0-9]+)/)?$",
        webgateway.render_col_plot,
        name="web_render_col_plot",
    ),
    re_path(
        r"^(?:(?P<share_id>[0-9]+)/)?render_split_channel/"
        r"(?P<iid>[0-9]+)/(?P<z>[0-9]+)/(?P<t>[0-9]+)/$",
        webgateway.render_split_channel,
        name="web_render_split_channel",
    ),
    re_path(
        r"^saveImgRDef/(?P<iid>[0-9]+)/$",
        webgateway.save_image_rdef_json,
        name="web_save_image_rdef_json",
    ),
    re_path(
        r"^(?:(?P<share_id>[0-9]+)/)?getImgRDef/$",
        webgateway.get_image_rdef_json,
        name="web_get_image_rdef_json",
    ),
    re_path(
        r"^(?:(?P<share_id>[0-9]+)/)?copyImgRDef/$",
        webgateway.copy_image_rdef_json,
        name="copy_image_rdef_json",
    ),
    re_path(
        r"^(?:(?P<share_id>[0-9]+)/)?luts/$",
        webgateway.listLuts_json,
        name="web_list_luts",
    ),
    # Fileset query (for delete or chgrp dialogs) obj-types and ids in REQUEST
    # data
    re_path(
        r"^fileset_check/(?P<action>(delete|chgrp))/$",
        views.fileset_check,
        name="fileset_check",
    ),
    # chgrp/chown dry run - 'group/owner_id', obj-types and ids in POST data.
    # E.g. Dataset=1,2,3 & Fileset=4. Multiple datatypes in one chgrp.
    re_path(
        r"^chgrpDryRun/$",
        views.dryRun,
        {"action": "chgrp"},
        name="chgrpDryRun",
    ),
    re_path(
        r"^chownDryRun/$",
        views.dryRun,
        {"action": "chown"},
        name="chownDryRun",
    ),
    # chgrp dry run - 'group_id', obj-types and ids in POST data.
    # E.g. Dataset=1,2,3 & Fileset=4. Multiple datatypes in one chgrp.
    re_path(r"^chgrpDryRun/$", views.chgrpDryRun, name="chgrpDryRun"),
    # Popup for downloading original archived files for images
    re_path(
        r"^download_placeholder/$",
        views.download_placeholder,
        name="download_placeholder",
    ),
    # chgrp - 'group_id', obj-types and ids in POST data
    re_path(r"^chgrp/$", views.chgrp, name="chgrp"),
    # chown - 'owner_id', obj-types and ids in POST data
    re_path(r"^chown/$", views.chown, name="chown"),
    # annotations
    re_path(
        r"^action/(?P<action>[a-zA-Z]+)/(?:(?P<o_type>[a-zA-Z]+)/)"
        r"?(?:(?P<o_id>[0-9]+)/)?$",
        views.manage_action_containers,
        name="manage_action_containers",
    ),
    re_path(r"^batch_annotate/$", views.batch_annotate, name="batch_annotate"),
    re_path(r"^annotate_tags/$", views.annotate_tags, name="annotate_tags"),
    re_path(
        r"^marshal_tagging_form_data/$",
        views.marshal_tagging_form_data,
        name="marshal_tagging_form_data",
    ),
    re_path(r"^annotate_rating/$", views.annotate_rating, name="annotate_rating"),
    re_path(r"^annotate_comment/$", views.annotate_comment, name="annotate_comment"),
    re_path(r"^annotate_file/$", views.annotate_file, name="annotate_file"),
    re_path(r"^annotate_map/$", views.annotate_map, name="annotate_map"),
    re_path(
        r"^annotation/(?P<annId>[0-9]+)/$",
        views.download_annotation,
        name="download_annotation",
    ),
    re_path(
        r"^load_original_metadata/(?P<imageId>[0-9]+)/" r"(?:(?P<share_id>[0-9]+)/)?$",
        views.load_original_metadata,
        name="load_original_metadata",
    ),
    re_path(
        r"^download_orig_metadata/(?P<imageId>[0-9]+)/$",
        views.download_orig_metadata,
        name="download_orig_metadata",
    ),
    re_path(
        r"^omero_table/(?P<file_id>[0-9]+)/(?:(?P<mtype>(json|csv))/)?$",
        views.omero_table,
        name="omero_table",
    ),
    re_path(r"^avatar/(?P<oid>[0-9]+)/$", views.avatar, name="avatar"),
    # scripting service urls
    re_path(
        r"^list_scripts/$", views.list_scripts, name="list_scripts"
    ),  # returns html list of scripts - click to run
    re_path(
        r"^script_ui/(?P<scriptId>[0-9]+)/$", views.script_ui, name="script_ui"
    ),  # shows a form for running a script
    re_path(
        r"^script_run/(?P<scriptId>[0-9]+)/$", views.script_run, name="script_run"
    ),  # runs the script - parameters in POST
    re_path(r"^script_upload/$", views.script_upload, name="script_upload"),
    re_path(
        r"^get_original_file/(?:(?P<fileId>[0-9]+)/)?$",
        views.get_original_file,
        name="get_original_file",
    ),  # for stderr, stdout etc
    re_path(
        r"^download_original_file/(?:(?P<fileId>[0-9]+)/)?$",
        views.get_original_file,
        {"download": True},
        name="download_original_file",
    ),  # for stderr, stdout etc
    re_path(
        r"^figure_script/(?P<scriptName>" r"(SplitView|Thumbnail|MakeMovie))/$",
        views.figure_script,
        name="figure_script",
    ),  # shows a form for running a script
    # ome_tiff_script: generate OME-TIFF and attach to image (use script
    # service). Must be POST
    re_path(
        r"^ome_tiff_script/(?P<imageId>[0-9]+)/$",
        views.ome_tiff_script,
        name="ome_tiff_script",
    ),
    re_path(
        r"^ome_tiff_info/(?P<imageId>[0-9]+)/$",
        views.ome_tiff_info,
        name="ome_tiff_info",
    ),
    # ping OMERO server to keep session alive
    re_path(r"^keepalive_ping/$", views.keepalive_ping, name="keepalive_ping"),
    # Load data, but with JSON.
    # re_path(r'^api/$', None, name='api'),
    re_path(r"^api/groups/$", views.api_group_list, name="api_groups"),
    re_path(
        r"^api/experimenters/(?P<experimenter_id>-?\d+)/$",
        views.api_experimenter_detail,
        name="api_experimenter",
    ),
    # Generic container list. This is necessary as an experimenter may have
    # datasets/etc which do not belong to any project
    re_path(r"^api/containers/$", views.api_container_list, name="api_containers"),
    # re_path(r'^api/projects/$', views.api_project_list, name='api_projects'),
    # re_path(r'^api/projects/(?P<pk>[0-9]+)/$', views.api_project_detail),
    re_path(r"^api/datasets/$", views.api_dataset_list, name="api_datasets"),
    # re_path(r'^api/datasets/(?P<pk>[0-9]+)/$', views.api_dataset_detail),
    re_path(r"^api/images/$", views.api_image_list, name="api_images"),
    # special case: share_id not allowed in query string since we
    # just want to allow share connection for this url ONLY.
    re_path(
        r"^api/share_images/(?P<share_id>[0-9]+)/$",
        views.api_image_list,
        name="api_share_images",
    ),
    re_path(r"^api/plates/$", views.api_plate_list, name="api_plates"),
    # re_path(r'^api/plates/(?P<pk>[0-9]+)/$', views.api_plate_detail),
    re_path(
        r"^api/plate_acquisitions/$",
        views.api_plate_acquisition_list,
        name="api_plate_acquisitions",
    ),
    # re_path(r'^api/plate_acquisitions/(?P<pk>[0-9]+)/$',
    #     views.api_plate_acquisitions_detail),
    # POST to create link, DELETE to remove.
    # links in request.body json, e.g. {"dataset":{"10":{"image":[1,2,3]}}}
    re_path(r"^api/links/$", views.api_links, name="api_links"),
    # re_path(r'^api/tags/$', views.api_tag_list, name='api_tags'),
    # re_path(r'^api/tags/(?P<pk>[0-9]+)/$', views.api_tag_detail),
    # Retrieve paths to an object
    re_path(
        r"^api/paths_to_object/$", views.api_paths_to_object, name="api_paths_to_object"
    ),
    # Get parents of 1 or more objects. ?image=1,2&dataset=3
    re_path(r"^api/parent_links/$", views.api_parent_links, name="api_parent_links"),
    re_path(r"^api/tags/$", views.api_tags_and_tagged_list, name="api_tags_and_tagged"),
    re_path(r"^api/annotations/$", views.api_annotations, name="api_annotations"),
    re_path(r"^api/shares/$", views.api_share_list, name="api_shares"),
]
