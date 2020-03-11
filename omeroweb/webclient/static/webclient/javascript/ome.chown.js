

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

    var $chownform = $("#chown-form"),
        $newbtn,
        $okbtn;


    // external entry point, called by jsTree right-click menu
    window.OME.handleChown = function() {
        // gid, gname, oid
        $chownform.dialog({"title": "Change Owner",
            height: 450,
            width: 400});
        $chownform.dialog('open');
        $chownform.empty();

        // Add selected items to chown form as hidden inputs
        var selobjs = OME.get_tree_selection().split("&");  // E.g. Image=1,2&Dataset=3
        for (var i = 0; i < selobjs.length; i++) {
            dtype = selobjs[i].split("=")[0];
            dids = selobjs[i].split("=")[1];
            $("<input name='"+ dtype +"' value='"+ dids +"'/>")
                .appendTo($chownform).hide();
        }

        // Need to find users we can move selected objects to.
        // Object owner must be member of target group.
        var gid = WEBCLIENT.active_group_id;
        var url = WEBCLIENT.URLS.api_base + "m/experimentergroups/" + gid + "/experimenters/";
        $.getJSON(url, function(data) {
            // Other group members (ignore current user)
            var userId = WEBCLIENT.USER.id;
            var exps = data.data.filter(function(exp){
                return exp['@id'] != userId;
            });
            // List the target users...
            var html = exps.map(function(exp) {
                return "<label><input name='owner_id' type='radio' value='" + exp['@id'] + "'/>" + exp.FirstName + " " + exp.LastName + "</label><br/>";
            }).join("");
            // If no target groups found...
            if (html.length === 0) {
                html = "<hr><p>No users found</p><hr>";
            } else {
                html = "<h1>Please choose new owner for the selected data:</h1>" + html;
            }
            $chownform.append(html);
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
            // Don't submit if we haven't populated the form with users etc.
            console.log('beforeSubmit', data);
            if (data.length === 0) {
                OME.alert_dialog("Please choose target user.");
                return false;
            }
        },
        success: function(data) {
            // var inst = $.jstree.reference('#dataTree');
            // var remove = data.update.remove;
            // var childless = data.update.childless;

            // var removalClosure = [];
            // var unremovedParentClosure;
            // var removeType = function(type, ids) {
            //     $.each(ids, function(index, id) {
            //         var removeLocated = inst.locate_node(type + '-' + id);
            //         if (removeLocated) {
            //             $.each(removeLocated, function(index, val) {
            //                 if (unremovedParentClosure !== undefined &&
            //                     val.id === unremovedParentClosure.id) {
            //                     // The new selection is also to be deleted, so select its parent
            //                     unremovedParentClosure = inst.get_node(inst.get_parent(val));
            //                 }
            //                 else if (inst.is_selected(val)) {
            //                     // This node was selected, mark its parent to be selected instead
            //                     unremovedParentClosure = inst.get_node(inst.get_parent(val));
            //                 }
            //             // Accumulate nodes for deletion so the new selection can occur before delete
            //             removalClosure.push(val);
            //             });
            //         }
            //     });
            // };

            // // Find and remove
            // // This is done in a specific order so that the correct node can be selected
            // var typeOrder = ['image', 'acquisition', 'dataset', 'plate', 'project', 'screen'];
            // $.each(typeOrder, function(index, type) {
            //     if (remove.hasOwnProperty(type)) {
            //         removeType(type, remove[type]);
            //     }
            // });

            // // Select the closest parent that was not part of the chown
            // inst.deselect_all(true);
            // inst.select_node(unremovedParentClosure);

            // // Update the central panel in case chown removes an icon
            // $.each(removalClosure, function(index, node) {
            //     inst.delete_node(node);
            //     var e = {'type': 'delete_node'};
            //     var data = {'node': node,
            //                 'old_parent': inst.get_parent(node)};
            //     update_thumbnails_panel(e, data);
            // });

            // function markChildless(ids, dtype) {
            //     $.each(ids, function(index, id) {
            //         var childlessLocated = inst.locate_node(property + '-' + id);
            //         // If some nodes were found, make them childless
            //         if (childlessLocated) {
            //             $.each(childlessLocated, function(index, node) {
            //                 node.state.loaded = true;
            //                 inst.redraw_node(node);
            //             });

            //         }
            //     });
            // }

            // // Find and mark childless
            // for (var property in childless) {
            //     if (childless.hasOwnProperty(property)) {
            //         markChildless(childless[property], property);
            //     }

            // }

            OME.showActivities();
        }
    });

});
