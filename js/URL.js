import { state, settings } from './globalState.js';
import { profileToMatrix } from './utils.js';
import { loadMatrix } from './InstanceManagement.js';
import { buildTable } from './TableBuilder.js';

function writeURL() {
    let profileMatrix =  profileToMatrix(state, settings.useWeights);
    let stateString = `${state.committeeSize}&` + profileMatrix.replaceAll("\n", "&").slice(0, -1);
    if (stateString != window.location.search.substring(1)) {
        window.history.pushState({}, "", window.location.origin + window.location.pathname + "?" + stateString);
    }
}

export function copyURL() {
    let profileMatrix = profileToMatrix(state, settings.useWeights);
    let stateString = `${state.committeeSize}&` + profileMatrix.replaceAll("\n", "&").slice(0, -1);
    let URL = window.location.origin + window.location.pathname + "?" + stateString;
    let button = document.getElementById("copy-url-button");
    let originalHTML = button.innerHTML;
    try {
        navigator.clipboard.writeText(URL).then(function () {
            button.innerHTML = "✓ Copied!";
            setTimeout(function () {
                button.innerHTML = originalHTML;
            }, 1000);
        });
    } catch (e) {
        console.error(e);
        button.innerHTML = "✗ Copy failed";
        setTimeout(function () {
            button.innerHTML = originalHTML;
        }, 1000);
        console.log("URL: " + URL);
    }
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
            let info = stateString.split("&");
            let matrix = info.slice(1).join("\n");
            let committeeSize_ = parseInt(info[0]);
            if (matrix.includes('*')){
                settings.useWeights = true;
                let useWeights = document.getElementById("weights");
                useWeights.checked = true;
            }
            
            state.committeeSize = committeeSize_;
            try {
                loadMatrix(matrix)
            } catch (e) {
                console.error(e);
                loadStandardInstance();
            }
        } catch (e) {
            console.error(e);
            loadStandardInstance();
        }
        buildTable();
    }
}