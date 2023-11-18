import { state } from './globalState.js';
import { profileToMatrix } from './utils.js';
import { loadMatrix } from './InstanceManagement.js';
import { buildTable } from './TableBuilder.js';

function writeURL() {
    let stateString = `${state.committeeSize}&` + profileToMatrix(state).replaceAll("\n", "&").slice(0, -1);
    if (stateString != window.location.search.substring(1)) {
        window.history.pushState({}, "", window.location.origin + window.location.pathname + "?" + stateString);
    }
}

export function copyURL() {
    let stateString = `${state.committeeSize}&` + profileToMatrix(state).replaceAll("\n", "&").slice(0, -1);
    let URL = window.location.origin + window.location.pathname + "?" + stateString;
    let button = document.getElementById("copy-url-button");
    let originalHTML = button.innerHTML;
    navigator.clipboard.writeText(URL).then(function () {
        button.innerHTML = "✓ Copied!";
        setTimeout(function () {
            button.innerHTML = originalHTML;
        }, 1000);
    });
}

function loadStandardInstance() {
    let matrix = "111100000000000\n111010000000000\n111001000000000\n000000111000000\n000000000111000\n000000000000111";
    loadMatrix(matrix);
    state.committeeSize = 12;
}

export function readURL() {
    if (window.location.search) {
        try {
            let stateString = window.location.search.substring(1);
            let state = stateString.split("&");
            let matrix = state.slice(1).join("\n");
            let committeeSize_ = parseInt(state[0]);
            state.committeeSize = committeeSize_;
            if (!loadMatrix(matrix)) {
                loadStandardInstance();
            }
        } catch (e) {
            console.error(e);
            loadStandardInstance();
        }
        buildTable();
    }
}