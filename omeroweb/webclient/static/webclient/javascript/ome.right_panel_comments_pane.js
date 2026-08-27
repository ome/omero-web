//   Copyright (C) 2016 University of Dundee & Open Microscopy Environment.
//   All rights reserved.

//   This program is free software: you can redistribute it and/or modify
//   it under the terms of the GNU Affero General Public License as
//   published by the Free Software Foundation, either version 3 of the
//   License, or (at your option) any later version.

//   This program is distributed in the hope that it will be useful,
//   but WITHOUT ANY WARRANTY; without even the implied warranty of
//   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//   GNU Affero General Public License for more details.

//   You should have received a copy of the GNU Affero General Public License
//   along with this program.  If not, see <http://www.gnu.org/licenses/>.


var CommentsPane = function CommentsPane($element, opts) {

    var $header = $element.children('h1'),
        $body = $element.children('div'),
        $comments_container = $("#comments_container"),
        objects = opts.selected;
    var self = this;

    var tmplText = $('#comments_template').html();
    var commentsTempl = _.template(tmplText);


    var initEvents = (function initEvents() {

        $header.on('click', function(){
            $header.toggleClass('closed');
            $body.slideToggle();

            var expanded = !$header.hasClass('closed');
            OME.setPaneExpanded('comments', expanded);

            if (expanded && $comments_container.is(":empty")) {
                this.render();
            }
        }.bind(this));
    }).bind(this);

    // Comment field - show/hide placeholder and submit button.
    $("#add_comment_wrapper label").inFieldLabels();
    $("#id_comment")
        .on('blur', function(event){
            setTimeout(function(){
                $("#add_comment_form input[type='submit']").hide();
            }, 200);    // Delay allows clicking on the submit button!
        })
        .on('focus', function(){
            $("#add_comment_form input[type='submit']").show();
        });

    // bind removeItem to various [-] buttons
    $("#comments_container").on("click", ".removeComment", function(event){
        var url = $(this).attr('url');
        var objId = objects.join("|");
        OME.removeItem(event, ".ann_comment_wrapper", url, objId);
        return false;
    });

    // handle submit of Add Comment form
    $("#add_comment_form").ajaxForm({
        beforeSubmit: function(data, $form, options) {
            $("#add_comment_form input[type='submit']").hide();
            $("#comments_spinner").show();
            var textArea = $('#add_comment_form textarea');
            if (textArea.val().trim().length === 0) return false;
            // here we specify what objects are to be annotated
            objects.forEach(function(o){
                var dtypeId = o.split("-");
                data.push({"name": dtypeId[0], "value": dtypeId[1]});
            });
        },
        success: function(html) {
            $("#id_comment").val("");
            self.render();
        },
    });

    var compareParentName = function(a, b){
        if (!a.parent.name || !b.parent.name) {
            return 1;
        }
        return a.parent.name.toLowerCase() > b.parent.name.toLowerCase() ? 1 : -1;
    };


    this.render = function render() {

        if ($comments_container.is(":visible")) {

            if ($comments_container.is(":empty")) {
                $("#comments_spinner").show();
            }

            var request = objects.map(function(o){
                return o.replace("-", "=");
            });
            request = request.join("&");

            $.getJSON(WEBCLIENT.URLS.webindex + "api/annotations/?parents=true&type=comment&" + request, function(data){


                // manipulate data...
                // make an object of eid: experimenter
                var experimenters = data.experimenters.reduce(function(prev, exp){
                    prev[exp.id + ""] = exp;
                    return prev;
                }, {});

                // Populate experimenters within anns
                var anns = data.annotations.map(function(ann){
                    ann.owner = experimenters[ann.owner.id];
                    if (ann.link && ann.link.owner) {
                        ann.link.owner = experimenters[ann.link.owner.id];
                    }
                    ann.addedBy = [ann.link.owner.id];
                    return ann;
                });

                var inh_anns = []
                if (data.hasOwnProperty("parents")){
                    inh_anns = data.parents.annotations.map(function(ann) {
                        ann.owner = experimenters[ann.owner.id];
                        if (ann.link && ann.link.owner) {
                            ann.link.owner = experimenters[ann.link.owner.id];
                        }
                        ann.addedBy = [ann.link.owner.id];
                        let class_ = ann.link.parent.class;
                        let id_ = '' + ann.link.parent.id;
                        children = data.parents.lineage[class_][id_];
                        class_ = children[0].class;
                        ann.childClass = class_.substring(0, class_.length - 1);
                        ann.childNames = [];
                        if (children[0].hasOwnProperty("name")){
                            for(j = 0; j < children.length; j++){
                                ann.childNames.push(children[j].name);
                            }
                        }
                        return ann;
                    });
                }

                // If we are batch annotating multiple objects, we show a summary of each ann
                if (objects.length > 1) {

                    // Map ann.id to summary for that ann
                    var summary = {};
                    anns.forEach(function(ann){
                        var annId = ann.id,
                            linkOwner = ann.link.owner.id;
                        if (summary[annId] === undefined) {
                            ann.canRemove = false;
                            ann.canRemoveCount = 0;
                            ann.links = [];
                            ann.addedBy = [];
                            summary[annId] = ann;
                        }
                        // Add link to list...
                        var l = ann.link;
                        // slice parent class 'ProjectI' > 'Project'
                        l.parent.class = l.parent.class.slice(0, -1);
                        summary[annId].links.push(l);

                        // ...and summarise other properties on the ann
                        if (l.permissions.canDelete) {
                            summary[annId].canRemoveCount += 1;
                        }
                        summary[annId].canRemove = summary[annId].canRemove || l.permissions.canDelete;
                        if (summary[annId].addedBy.indexOf(linkOwner) === -1) {
                            summary[annId].addedBy.push(linkOwner);
                        }
                    });

                    // convert summary back to list of 'anns'
                    anns = [];
                    for (var annId in summary) {
                        if (summary.hasOwnProperty(annId)) {
                            summary[annId].links.sort(compareParentName);
                            anns.push(summary[annId]);
                        }
                    }

                    // Map ann.id to summary for that ann
                    summary = {};
                    inh_anns.forEach(function(ann){
                        var annId = ann.id,
                            linkOwner = ann.link.owner.id;
                        if (summary[annId] === undefined) {
                            ann.canRemove = false;
                            ann.canRemoveCount = 0;
                            ann.links = [];
                            ann.addedBy = [];
                            summary[annId] = ann;
                        }
                        // Add link to list...
                        var l = ann.link;
                        // slice parent class 'ProjectI' > 'Project'
                        l.parent.class = l.parent.class.slice(0, -1);
                        summary[annId].links.push(l);

                        // ...and summarise other properties on the ann
                        if (summary[annId].addedBy.indexOf(linkOwner) === -1) {
                            summary[annId].addedBy.push(linkOwner);
                        }
                        for(j = 0; j < ann.childNames; j++){
                            summary[annId].childNames.push(ann.childNames[j]);
                        }
                    });

                    // convert summary back to list of 'anns'
                    inh_anns = [];
                    for (var annId in summary) {
                        if (summary.hasOwnProperty(annId)) {
                            summary[annId].links.sort(compareParentName);
                            inh_anns.push(summary[annId]);
                        }
                    }
                }

                // Show most recent comments at the top
                anns.sort(function(a, b) {
                    return a.date < b.date ? 1 : -1;
                });
                hierarchy = {"ProjectI":0, "DatasetI":1, "ScreenI":2, "PlateI":3, "PlateAcquisitionI":4, "WellI":5}
                inh_anns.sort(function(a, b) {
                    if (hierarchy[a.link.parent.class] != hierarchy[b.link.parent.class]){
                        return hierarchy[a.link.parent.class] > hierarchy[b.link.parent.class] ? 1 : -1;
                    } else{
                        return a.date < b.date ? 1 : -1;
                    }
                });

                // Update html...
                var html = "";
                if (anns.length > 0) {
                    html = commentsTempl({'anns': anns,
                                          'static': WEBCLIENT.URLS.static_webclient,
                                          'webindex': WEBCLIENT.URLS.webindex,
                                          'userId': WEBCLIENT.USER.id,
                                          'isInherited': false});
                }
                if (inh_anns.length > 0) {
                    html = html + commentsTempl({'anns': inh_anns,
                                                  'static': WEBCLIENT.URLS.static_webclient,
                                                  'webindex': WEBCLIENT.URLS.webindex,
                                                  'userId': WEBCLIENT.USER.id,
                                                  'isInherited': true});
                }


                $("#comments_spinner").hide();
                $comments_container.html(html);

                // Finish up...
                OME.linkify_element($( ".commentText" ));
                OME.filterAnnotationsAddedBy();
                $(".tooltip", $comments_container).tooltip_init();
            });
        }
    };


    initEvents();

    if (OME.getPaneExpanded('comments')) {
        $header.toggleClass('closed');
        $body.show();
    }

    this.render();
};