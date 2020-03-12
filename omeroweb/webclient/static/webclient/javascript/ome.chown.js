

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
        var datatree = $.jstree.reference('#dataTree');
        var dataOwners = datatree.get_selected(true).map(function(s){return s.data.obj.ownerId});

        // Need to find users we can move selected objects to.
        // Object owner must be member of current group.
        var gid = WEBCLIENT.active_group_id;
        var url = WEBCLIENT.URLS.api_base + "m/experimentergroups/" + gid + "/experimenters/";
        $.getJSON(url, function(data) {
            // Other group members (ignore current owner if just 1)
            var exps = data.data;
            if (dataOwners.length === 1) {
                exps = exps.filter(function(exp){
                    return exp['@id'] != dataOwners[0];
                });
            }
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
            if (data.length === 0) {
                OME.alert_dialog("Please choose target user.");
                return false;
            }
        },
        success: function(data) {
            // If we're viewing 'All Members' we don't need to change anything in the tree
            if (WEBCLIENT.active_user.id != -1) {
                // Otherwise, we need to remove selected nodes
                var inst = $.jstree.reference('#dataTree');
                inst.get_selected(true).forEach(function(node){
                    console.log('delete', node);
                    inst.delete_node(node);
                });
            }
            $chownform.dialog( "close" );
            OME.showActivities();
        }
    });

});
