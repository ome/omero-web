/**
 * gs_utils - Common functions library
 *
 * Copyright (c) 2007, 2008, 2009 Glencoe Software, Inc. All rights reserved.
 * 
 * This software is distributed under the terms described by the LICENCE file
 * you can find at the root of the distribution bundle, which states you are
 * free to use it only for non commercial purposes.
 * If the file is missing please request a copy by contacting
 * jason@glencoesoftware.com.
 *
 * Author: Carlos Neves <carlos(at)glencoesoftware.com>
 */

var gs_static_location_prefix=''; //configure it to access static files, used with 3rdparty/jquery.blockUI-2.66.0.js

/**
 * Given a string that may contain an RGB, RRGGBB or the previous with a # prefix,
 * returns the #RRGGBB counterpart, or if the parse fails, the default value (or null if no default)
 */
function sanitizeHexColor (color, def) {
  color = toRGB(color, def);
  if (color === def || color === null) {
    return color;
  }
  return '#' + OME.rgbToHex(color);
}

/**
 * Converts a color into rgb(r,g,b) notation, right now only hex RGB or RRGGBB inputs.
 */
function toRGB (color, def) {
  if (color.substring(0,4) == 'rgb(') {
    return color;
  }
  if (color.substring(0,1) == '#') {
    color = color.substring(1);
  }
  var r,g,b;
  if (color.length == 3) {
    r = parseInt(color.substring(0,1), 16);
    g = parseInt(color.substring(1,2), 16);
    b = parseInt(color.substring(2,3), 16);
    r += r*0x10;
    g += g*0x10;
    b += b*0x10;
  } else if (color.length == 6) {
    r = parseInt(color.substring(0,2), 16);
    g = parseInt(color.substring(2,4), 16);
    b = parseInt(color.substring(4,6), 16);
  }
  if (r === undefined || isNaN(r) || isNaN(g) || isNaN(b)) {
    return def != undefined ? def : null;
  }
  return 'rgb('+r+','+g+','+b+')';
}

/**
 * parse the URL query string. Shamelessly stolen from thickbox.
 */
function parseQuery (q) {
  var query;
  if (q === undefined) {
    query = location.href.replace(/^[^\?]+\??/,'');
  } else {
    query = q.replace(/^\??/,'');
  }
  var Params = {};
  if ( ! query ) {return Params;}// return empty object
  var Pairs = query.split(/[;&]/);
  for ( var i = 0; i < Pairs.length; i++ ) {
    var KeyVal = Pairs[i].split('=');
    if ( ! KeyVal || KeyVal.length != 2 ) {continue;}
    var key = decodeURIComponent( KeyVal[0] );
    var val = decodeURIComponent( KeyVal[1] );
    val = val.replace(/\+/g, ' ');
    Params[key] = val;
  }
  return Params;
}

/**
 * Lazy loader for the blockUI plugin.
 */

function gs_loadBlockUI (callback) {
  if (jQuery.blockUI === undefined) {
    jQuery.getScript(gs_static_location_prefix + '3rdparty/jquery.blockUI-2.66.0.js', callback);
    return false;
  }
  return true;
}

function gs_choiceModalDialog (message, choices, callback, blockui_opts, cancel_callback, _modal_cb) {
  if (!gs_loadBlockUI (function () {gs_choiceModalDialog(message, choices, callback, blockui_opts, cancel_callback,_modal_cb);})) {
    return;
  }
  if (_modal_cb) {
    gs_modal_cb = _modal_cb;
  } else {
    gs_modal_cb = function (idx) {
      jQuery.unblockUI();
      if (choices[idx].data != null) {
        callback(choices[idx].data);
      } else if (cancel_callback) {
        cancel_callback();
      }
      return false;
    }
  }
  for (var i=0; i < choices.length; i++) {
    message += '<input type="button" onclick="return gs_modal_cb('+i+');" value="'+choices[i].label+'" />'
  }
  if (!blockui_opts) {
    blockui_opts = {};
  }
  jQuery.blockUI({message: message, css: blockui_opts.css});
  return;
}

function gs_json (url, data, callback) {
  var cb = function (result) {
    return function (data, textStatus, errorThrown) {
      if (callback) {
        callback (result, result ? data : errorThrown || textStatus);
      }
    }
  }

  return jQuery.ajax({
      type: data ? "POST":"GET",
        url: url,
        data: data,
        success: cb(true),
        error: cb(false),
        dataType: "jsonp",
        traditional: true
        });
}
