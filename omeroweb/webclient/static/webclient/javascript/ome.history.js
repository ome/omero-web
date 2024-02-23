
function setQueryStringParameter(name, value, data) {
    const params = new URLSearchParams(window.location.search);
    params.set(name, value);
    data = data || {};
    window.history.pushState(data, "", decodeURIComponent(`${window.location.pathname}?${params}`));
}

(function(){
    let listening = true;

    // on selection change, update history
    $("body").on("selection_change.ome", function(event) {
        if (!listening) return;
        var selected = $("body").data("selected_objects.ome");
        let show = selected.map(obj => obj.id).join("|")
        setQueryStringParameter("show", show, {selected: selected});
    });

    // Handle forward/back buttons
    window.addEventListener("popstate", (event) => {
        if (event.state) {
            const {selected} = event.state;
            console.log("popstate selected...", selected);
            if (selected.length == 0) {
                return;
            }
            var inst = $.jstree.reference('#dataTree');
            inst.deselect_all(true);

            // disable history above, otherwise it adds to pushState,
            // wipes out any 'forward' history etc.
            listening = false;
            
            selected.forEach((obj) => {
                var obj_id = obj.id;
                var node = inst.locate_node(obj_id)[0];
                if (node) {
                    inst.select_node(node);
                    // we also focus the node, to scroll to it and setup hotkey events
                    $("#" + node.id).children('.jstree-anchor').trigger('focus');
                } else {
                    // TODO: not handled 'Well'
                    console.log("HISTORY node not found ", obj_id);
                }
            });
            // once we're done, start listening again
            setTimeout(() => {listening = true}, 500);
        }
    });

})();
