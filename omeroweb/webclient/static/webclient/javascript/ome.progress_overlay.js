/* globals OME, $ */

/**
 * Create an overlay that blocks the user from interacting with the UI,
 * for example to prevent a long-running action from being interrupted
 * or repeated before it is completed.
 * @param promise When this promise resolves (successfully or otherwise) the overlay closes
 * @param message The optional message to display (defaults to "Please wait")
 * @returns {*|jQuery} The jQuery element holding the dialog; no need to do anything with it
 */
OME.progress_overlay = function (promise, message) {
  'use strict';
  const dialog = $('<div>' + (message || 'Please wait') + '</div>')
    .appendTo(document.body)
    .dialog({
      modal: true,
      autoOpen: true,
      closeOnEscape: false,
      draggable: false,
      resizable: false,
      classes: {
        'ui-dialog': 'ome-modal-progress',
      }
    });
  promise.finally(() => dialog.dialog('destroy').remove());
  return dialog;
};
