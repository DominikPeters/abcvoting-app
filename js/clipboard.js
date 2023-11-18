import { state } from './globalState.js';
import { profileToMatrix } from './utils.js';
import { loadMatrix } from './InstanceManagement.js';
import { buildTable } from './TableBuilder.js';

export function pasteMatrix(event) {
    let paste = (event.clipboardData || window.clipboardData).getData('text');
    // throw away all characters except 0, 1, and \n
    paste = paste.replace(/[^01\n]/g, '');
    if (paste.match(/^[01\n]+$/)) {
        loadMatrix(paste);
        buildTable();
    }
    event.preventDefault();
}

export function copyMatrix() {
    let button = document.getElementById("copy-button");
    let originalHTML = button.innerHTML;
    navigator.clipboard.writeText(profileToMatrix(state)).then(() => {
        button.innerHTML = "✓ Copied!";
        setTimeout(function () {
            button.innerHTML = originalHTML;
        }, 1000);
    }, (err) => {
        console.error('Could not copy text: ', err);
        console.log(profileToMatrix(state));
    });
}