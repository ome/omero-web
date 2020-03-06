

  // Copyright (C) 2020 University of Dundee & Open Microscopy Environment.
  // All rights reserved.

  // This program is free software: you can redistribute it and/or modify
  // it under the terms of the GNU Affero General Public License as
  // published by the Free Software Foundation, either version 3 of the
  // License, or (at your option) any later version.

  // This program is distributed in the hope that it will be useful,
  // but WITHOUT ANY WARRANTY; without even the implied warranty of
  // MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  // GNU Affero General Public License for more details.

  // You should have received a copy of the GNU Affero General Public License
  // along with this program.  If not, see <http://www.gnu.org/licenses/>.


  $(function() {

    if (typeof window.OME === "undefined") { window.OME={}; }

    var webindex_url,
        static_url,
        data_owners,
        chown_type,
        target_type,
        $chownform = $("#chown-form"),
        $group_chooser,
        $move_group_tree,
        $newbtn,
        $okbtn;


    // external entry point, called by jsTree right-click menu
    window.OME.handleChown = function(webindex, staticurl) {
        webindex_url = webindex;
        static_url = staticurl;
        // gid, gname, oid
        $chownform.dialog({"title": "Change Owner",
            height: 450,
            width: 400});
        $chownform.dialog('open');
        $chownform.empty();

        // Need to find users we can move selected objects to.
        // Object owner must be member of target group.
        var url = webindex_url + "load_chown_groups/?" + OME.get_tree_selection();
        $.getJSON(url, function(data){
            data_owners = data.owners;  // save for later
            var ownernames = [];
            for (var o=0; o<data.owners.length; o++) {ownernames.push(data.owners[o][1]);}
            var headerTxt = "<p>Move data owned by " + ownernames.join(", ") + ".</p>" +
                            "<h1>Please choose target group below:</h1>";
            $group_chooser.append(headerTxt);

            // List the target groups...
            var html = "";
            for (var i=0; i<data.groups.length; i++){
                var g = data.groups[i];
                html += "<div class='chownGroup' data-gid='"+ g.id + "'>";
                html += "<img src='" + permsIcon(g.perms) + "'/>";
                html += g.name + "<hr></div>";
            }
            // If no target groups found...
            if (data.groups.length === 0) {
                html = "<hr><p>No target groups found</p><hr>";
                if (data.owners.length === 1) {
                    html += "Owner of the data may only be in 1 group.";
                } else {
                    html += "Owners of the data may only be in 1 group,";
                    html += "or they are not all in any common groups to move data to.";
                }
            }
            $group_chooser.append(html);
        });
    };

    // set-up the dialog
    $chownform.dialog({
        dialogClass: 'chown_confirm_dialog',
        autoOpen: false,
        resizable: true,
        height: 350,
        width:520,
        modal: true,
        buttons: {
            "OK": function() {
                var $thisBtn = $('.chown_confirm_dialog .ui-dialog-buttonset button:nth-child(2) span');
                // If we have split filesets, first submission is to confirm 'Move All'?
                // We hide the split_filesets info panel and rename submit button to 'OK'
                if ($(".split_filesets_info .split_fileset", $chownform).length > 0 && $thisBtn.text() == 'Move All') {
                    $("#group_chooser").show();
                    $(".split_filesets_info", $chownform).hide();
                    $thisBtn.text('OK');
                    return false;
                }
                $chownform.submit();
            },
            "Cancel": function() {
                $( this ).dialog( "close" );
            }
        }
    });

    // handle chown 
    $chownform.ajaxForm({
        beforeSubmit: function(data, $form){
            // Don't submit if we haven't populated the form with group etc.
            if (data.length === 0) {
                OME.alert_dialog("Please choose target group.");
                return false;
            }
            if ($("input[name='group_id']", $form).length === 0) return false;
            $chownform.dialog("close");
            var chown_target = $("#move_group_tree a.jstree-clicked");
            if (chown_target.length == 1){
                data.push({'name':'target_id', 'value': chown_target.parent().attr('id')});
            }
        },
        success: function(data) {
            var inst = $.jstree.reference('#dataTree');
            var remove = data.update.remove;
            var childless = data.update.childless;

            var removalClosure = [];
            var unremovedParentClosure;
            var removeType = function(type, ids) {
                $.each(ids, function(index, id) {
                    var removeLocated = inst.locate_node(type + '-' + id);
                    if (removeLocated) {
                        $.each(removeLocated, function(index, val) {
                            if (unremovedParentClosure !== undefined &&
                                val.id === unremovedParentClosure.id) {
                                // The new selection is also to be deleted, so select its parent
                                unremovedParentClosure = inst.get_node(inst.get_parent(val));
                            }
                            else if (inst.is_selected(val)) {
                                // This node was selected, mark its parent to be selected instead
                                unremovedParentClosure = inst.get_node(inst.get_parent(val));
                            }
                        // Accumulate nodes for deletion so the new selection can occur before delete
                        removalClosure.push(val);
                        });
                    }
                });
            };

            // Find and remove
            // This is done in a specific order so that the correct node can be selected
            var typeOrder = ['image', 'acquisition', 'dataset', 'plate', 'project', 'screen'];
            $.each(typeOrder, function(index, type) {
                if (remove.hasOwnProperty(type)) {
                    removeType(type, remove[type]);
                }
            });

            // Select the closest parent that was not part of the chown
            inst.deselect_all(true);
            inst.select_node(unremovedParentClosure);

            // Update the central panel in case chown removes an icon
            $.each(removalClosure, function(index, node) {
                inst.delete_node(node);
                var e = {'type': 'delete_node'};
                var data = {'node': node,
                            'old_parent': inst.get_parent(node)};
                update_thumbnails_panel(e, data);
            });

            function markChildless(ids, dtype) {
                $.each(ids, function(index, id) {
                    var childlessLocated = inst.locate_node(property + '-' + id);
                    // If some nodes were found, make them childless
                    if (childlessLocated) {
                        $.each(childlessLocated, function(index, node) {
                            node.state.loaded = true;
                            inst.redraw_node(node);
                        });

                    }
                });
            }

            // Find and mark childless
            for (var property in childless) {
                if (childless.hasOwnProperty(property)) {
                    markChildless(childless[property], property);
                }

            }

            OME.showActivities();
        }
    });

});
