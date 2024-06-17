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
  const dialog = $('<div><span class="spinner"></span>&nbsp;' + (message || 'Please wait') + '</div>')
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
    
    .ome-modal-progress .spinner {
      background-image: url("data:image/gif;base64,R0lGODlhEAAQAPIAAP///zxKW9HU2G95hjxKW4eQmqCnr6yyuSH5BAkKAAAAIf4aQ3JlYXRlZCB3aXRoIGFqYXhsb2FkLmluZm8AIf8LTkVUU0NBUEUyLjADAQAAACwAAAAAEAAQAAADMwi63P4wyklrE2MIOggZnAdOmGYJRbExwroUmcG2LmDEwnHQLVsYOd2mBzkYDAdKa+dIAAAh+QQJCgAAACwAAAAAEAAQAAADNAi63P5OjCEgG4QMu7DmikRxQlFUYDEZIGBMRVsaqHwctXXf7WEYB4Ag1xjihkMZsiUkKhIAIfkECQoAAAAsAAAAABAAEAAAAzYIujIjK8pByJDMlFYvBoVjHA70GU7xSUJhmKtwHPAKzLO9HMaoKwJZ7Rf8AYPDDzKpZBqfvwQAIfkECQoAAAAsAAAAABAAEAAAAzMIumIlK8oyhpHsnFZfhYumCYUhDAQxRIdhHBGqRoKw0R8DYlJd8z0fMDgsGo/IpHI5TAAAIfkECQoAAAAsAAAAABAAEAAAAzIIunInK0rnZBTwGPNMgQwmdsNgXGJUlIWEuR5oWUIpz8pAEAMe6TwfwyYsGo/IpFKSAAAh+QQJCgAAACwAAAAAEAAQAAADMwi6IMKQORfjdOe82p4wGccc4CEuQradylesojEMBgsUc2G7sDX3lQGBMLAJibufbSlKAAAh+QQJCgAAACwAAAAAEAAQAAADMgi63P7wCRHZnFVdmgHu2nFwlWCI3WGc3TSWhUFGxTAUkGCbtgENBMJAEJsxgMLWzpEAACH5BAkKAAAALAAAAAAQABAAAAMyCLrc/jDKSatlQtScKdceCAjDII7HcQ4EMTCpyrCuUBjCYRgHVtqlAiB1YhiCnlsRkAAAOw==");
      width: 16px;
      height: 16px;
      display: inline-block;
    }
  `;
  document.head.appendChild(styleSheet);
})();