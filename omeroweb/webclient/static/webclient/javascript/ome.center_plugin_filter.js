
function MapAnnFilter(image_ids, $element, callback, filterObjects) {

    this.image_ids = image_ids;
    this.filterText = "";
    this.moreLess = "more";
    this.filterObjects = filterObjects;

    var $filter = $('<div class="imagefilter filtersearch" style="width:100%">' +
        '<select class="choose_map_key">' +
        '</select>' +
        '<select class="map_more_less" style="width: 40px; display:none">' +
            '<option value="more">&gt;</option>' +
            '<option value="less">&lt;</option>' +
            '<option value="moreequal">&ge;</option>' +
            '<option value="lessequal">&le;</option>' +
            '<option value="equal">=</option>' +
        '</select>' +
        '<input class="filter_map_value" style="float:left; margin:2px; position:relative" />' +
        '<span class="filter_map_units" style="float:left; margin: 5px; font-size: 12px"></span>' +
        '<span title="Remove filter" class="removefilter" style="float:left; margin-left:5px">X</span>' +
    '</div>');

    $element.append($filter);
    $filter.show();

    // Bind event handlers to UI
    $(".choose_map_key", $filter).on('change', function(event){
        var $this = $(event.target);
        this.currentFilterKey = $this.val();
        if (this.currentFilterKey == '-') {
            this.currentKeyValues = undefined;
            this.keyisNumber = false;
        } else {
            this.currentKeyValues = this.usedKeyValues[this.currentFilterKey].values;
            this.keyisNumber = this.usedKeyValues[this.currentFilterKey].type === 'number';
            this.keyUnits = this.usedKeyValues[this.currentFilterKey].units;
        }
        if (this.keyisNumber) {
            $(".map_more_less", $filter).show();
        } else {
            $(".map_more_less", $filter).hide();
        }
        if (!this.keyUnits) {
            $(".filter_map_units", $filter).text("");
        } else {
            $(".filter_map_units", $filter).text(this.keyUnits.escapeHTML());
        }
        var placeholder = 'filter text';
        if (this.keyisNumber) {
            let min = this.usedKeyValues[this.currentFilterKey].min;
            let max = this.usedKeyValues[this.currentFilterKey].max;
            placeholder = min + '-' + max;
            $(".filter_map_value", $filter).autocomplete({disabled: true})
        } else {
            var autocompVals = [];
            for (var values of Object.values(this.currentKeyValues)) {
                for(var v=0; v<values.length; v++) {
                    if (autocompVals.indexOf(values[v]) === -1){
                        autocompVals.push(values[v]);
                    }
                }
            }
            autocompVals.sort();
            var self = this;
            $(".filter_map_value", $filter).autocomplete({
                disabled: false,
                minLength: 0,
                source: autocompVals,
                select: function( event, ui ) {
                    self.filterText = ui.item.value;
                    if (callback) {
                        callback();
                    }
                }
            });
            // When user clicks on auto-complete, show ALL options (search: "")
            $(".filter_map_value", $filter)
            .on('click', function (event) {
                $(this).autocomplete("search", "");
            })
            .focus()    // immediately focus and 'click' to show auto-complete
            .click();

        }
        $('.filter_map_value', $filter).attr('placeholder', placeholder)
            .attr('title', placeholder)
            .val('');   // clear filter
        this.filterText = "";
        if (callback) {
            callback();
        }
    }.bind(this));

    $(".filter_map_value", $filter).on('input', function(event){
        var val = $(event.target).val();
        if (this.keyisNumber) {
            // remove non-number characters. Allow . or - or 0-9
            val = val.split("").filter(function(c){c = c.charCodeAt(); return c == 45 || c == 46 || (c > 47 && c < 58)}).join('');
            $(event.target).val(val);
            if (isNaN(val)) {
                val = '';
            }
        }
        this.filterText = val;

        if (callback) {
            callback();
        }
    }.bind(this));

    $(".map_more_less", $filter).on('change', function(event){
        this.moreLess = $(event.target).val();
        if (callback) {
            callback();
        }
    }.bind(this));

    $(".removefilter", $filter).on('click', function() {
        let i = filterObjects.indexOf(this);
        // remove this filter from array
        filterObjects.splice(i, 1);
        // and remove from DOM
        $filter.remove();
        // re-filter
        if (callback) {
            callback();
        }
    }.bind(this));

    // Finally, load Map annotations and render
    this.loadAnnotations(function() {
        // {key: {'values':{'imageId': 'val1, val2'}, 'type': 'number'}
        // Render Tag filter chooser, without current filter tags
        var keyList = Object.keys(this.usedKeyValues);
        keyList.sort();
        var html = keyList.map(function(k){
            k = k.escapeHTML();
            return "<option value='" + k + "'>" + k + "</option>";
        }).join("");
        html = "<option value='-'>Choose Key</option>" + html;
        $(".choose_map_key", $filter).html(html);
    }.bind(this));
}

MapAnnFilter.prototype.isImageVisible = function(iid) {
    // Visible if number or string matches
    var visible;
    var text = this.filterText;
    // If image doesn't have matching key, hide
    if (!this.currentKeyValues) {
        visible = true;
    } else if (!this.currentKeyValues[iid]) {
        visible = false;
    } else if (text.length === 0) {
        visible = true;
    } else if (this.keyisNumber) {
        let cutoff = parseFloat(text);
        this.currentKeyValues[iid].forEach(function(v){
            v = parseFloat(v);
            // compare: more, less, moreequal, lessequal, equal
            if (v == cutoff && this.moreLess.indexOf('equal') > -1) {
                visible = true;
            } else if (v > cutoff && this.moreLess.indexOf('more') === 0) {
                visible = true;
            } else if (v < cutoff && this.moreLess.indexOf('less') === 0) {
                visible = true;
            }
        }.bind(this));
    } else {
        this.currentKeyValues[iid].forEach(function(v){
            if (v.indexOf(text) > -1) {
                visible = true;
            }
        });
    }
    return visible;
}


MapAnnFilter.prototype.loadAnnotations = function(callback) {

    var query = "image=" + this.image_ids.join("&image=");
    var url = WEBCLIENT.URLS.webindex + 'api/annotations/?type=map&' + query;
    $.getJSON(url, function(data){
        // map imageId to... {key: {'values':{'imageId': 'val1, val2'}, 'type': 'number'}
        this.usedKeyValues = data.annotations.reduce(function(prev, ann){
            let values = ann.values;
            let iid = ann.link.parent.id;
            for (let i=0; i<values.length; i++) {
                let key = values[i][0];
                let val = values[i][1];
                if (val.length == 0) continue;

                if (!prev[key]) {
                    prev[key] = {
                        values: {},
                        type: 'number',
                        units: undefined,   // just a suffix e.g 'mM' for 10mM
                        min: Infinity,
                        max: -Infinity,
                    };
                }
                // if type is NOT string, check if val is a number...
                if (prev[key].type !== 'string') {
                    // If 'units' are a string (not empty), value must be number+units
                    var num = undefined;
                    if (prev[key].units) {
                        // We remove units and strictly check it's a number...
                        let digits = val.replace(prev[key].units, '');
                        if (isNaN(digits) || isNaN(parseFloat(val))) {
                            // If not - we treat data as a string
                            prev[key].type = 'string';
                            prev[key].units = undefined
                        } else {
                            num = parseFloat(val);
                        }
                    // We haven't defined units yet... Check if NaN
                    } else if (isNaN(parseFloat(val))) {
                        // Can't cast to a number - bail!
                        prev[key].type = 'string';
                    } else {
                        // it IS a number - and we don't have any units yet...
                        num = parseFloat(val);
                        prev[key].units = val.replace(num, '').trim();   // '10 mM' -> 'mM'
                    }
                    // update min/max
                    if (num != undefined) {
                        prev[key].min = Math.min(num, prev[key].min);
                        prev[key].max = Math.max(num, prev[key].max);
                    }
                }
                if (!prev[key].values[iid]) {
                    prev[key].values[iid] = [val];
                } else {
                    prev[key].values[iid].push(val);
                }
            }
            return prev;
        }, {});

        if (callback) {
            callback();
        }
    }.bind(this));
}