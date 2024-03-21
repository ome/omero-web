/* globals OME, $ */

/**
 * Create an overlay that blocks the user from interacting with the UI,
 * for example to prevent a long-running action from being interrupted
 * or repeated before it is completed.
 * @param promise When this promise resolves (successfully or otherwise) the overlay closes
 * @param message The optional message to display (defaults to "Please wait")
 * @param quiet Don't print timing to console
 * @returns {*|jQuery} The jQuery element holding the dialog; no need to do anything with it
 */
OME.progress_overlay = function (promise, message, quiet) {
  'use strict';
  const startTime = new Date().getTime();
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
  promise.finally(() => {
    dialog.dialog('destroy').remove();
    if (!quiet) {
      window.console.log('UI blocked for ' + (new Date().getTime() - startTime).toString() + 'ms');
    }
  });
  return dialog;
};

// add styles
(function () {
  'use strict';
  const styleSheet = document.createElement("style");
  styleSheet.innerText = `
    .ome-modal-progress button {
        display: none;
    }
    
    .ome-modal-progress .ui-dialog-content {
        justify-content: center;
        align-items: center;
        font-size: larger;
        display: flex;
    }
  `;
  document.head.appendChild(styleSheet);
})();