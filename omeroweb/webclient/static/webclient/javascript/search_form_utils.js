// global variables declared elsewhere:
// SEARCH_ENGINE_URL
// resources_data
// query_mode
// cached_key_values - object {'key': ['value'...]} for autocomplete

function set_key_values(key_value, container) {
    // E.g. if user chooses key 'Antibody', we set or load the
    // possible Values for use by auto-complete
    if (key_value == "Any") {
      cached_key_values[key_value] = [];
      set_operator_options(key_value, container);
      return;
    }
  
    container.querySelector(".valueFields").value = "";
    const resource = get_resource(key_value);
    set_operator_options(key_value, container);
    if (cached_key_values[key_value] === undefined) {
      let url =
        SEARCH_ENGINE_URL +
        "resources/" +
        encodeURIComponent(resource) +
        "/getannotationvalueskey/?key=" +
        encodeURIComponent(key_value);
      fetch(url).then(function (response) {
        {
          response.json().then(function (data) {
            data.sort();
            cached_key_values[key_value] = data;
          });
        }
      });
    }
  }
  
  //As main attributes supports equals and not equals only
  //This function restrict the use to these two operators
  function set_operator_options(key_value, container) {
    condition = container.querySelector(".condition");
  
    condition.value = condition.options[0].text;
  
    for (i = 0; i < condition.length; i++) {
      if (main_attributes.includes(key_value)) {
        if (
          condition.options[i].text != "equals" &&
          condition.options[i].text != "not equals"
        )
          condition.options[i].style.display = "none";
      } else {
        condition.options[i].style.display = "block";
      }
    }
  }
  
  async function load_resources(mode) {
    let url;
    if (mode == "advanced") {
      url = SEARCH_ENGINE_URL + "resources/all/keys/";
    } else {
      url_ = SEARCH_ENGINE_URL + "resources/all/keys/";
      url = url_ + "?mode=" + encodeURIComponent(mode);
    }
    return await fetch(url).then((response) => response.json());
  }
  
  function get_resource(key) {
    // e.g. find if 'Antibody' key comes from 'image', 'project' etc
    for (resource in resources_data) {
      if (resources_data[resource].includes(key)) {
        return resource;
      }
    }
  }
  
  function get_current_query(form_id = "search_form") {
    let and_conditions = [];
    let or_conditions = [];
    //get and condition1
  
    let queryandnodes = document.querySelectorAll(`#${form_id} .and_clause`);
    for (let i = 0; i < queryandnodes.length; i++) {
      query_dict = {};
  
      let node = queryandnodes[i];
      // handle each OR...
      let ors = node.querySelectorAll(".search_or_row");
  
      let or_dicts = [...ors].map((orNode) => {
        return {
          name: orNode.querySelector(".keyFields").value,
          value: orNode.querySelector(".valueFields").value,
          operator: orNode.querySelector(".condition").value,
          resource: get_resource(orNode.querySelector(".keyFields").value),
        };
      });
      if (or_dicts.length > 1) {
        or_conditions.push(or_dicts);
      } else {
        and_conditions.push(or_dicts[0]);
      }
    }
  
    query_details = {};
    var query = {
      resource: "image",
      query_details: query_details,
    };
  
    query_details["and_filters"] = and_conditions;
    query_details["or_filters"] = or_conditions;
    query_details["case_sensitive"] =
      document.getElementById("case_sensitive").checked;
    query["mode"] = query_mode;
    return query;
  }
  