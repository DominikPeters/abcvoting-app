import { settings } from "./globalState.js";
import { buildTable } from "./TableBuilder.js";

async function changeSetting() {
    // settings.resolute = document.getElementById('resolute').checked;
    settings.liveMode = document.getElementById('live-mode').checked;
    settings.useFractions = document.getElementById('fractions').checked;
    if (!document.getElementById('showPropertyinTable').checked) {
        settings.showPropertyinTable = false;
    } else {
        settings.showPropertyinTable = document.getElementById('propertyToShow').value;
    }
    if (settings.liveMode) {
        buildTable();
    }
}

export function addSettingChangeHandlers() {
    const elementIDs = ["live-mode", "fractions", "showPropertyinTable"];
    for (let id of elementIDs) {
        document.getElementById(id).addEventListener('change', changeSetting);
    }
    document.getElementById("propertyToShow").addEventListener('change', () => {
        document.getElementById('showPropertyinTable').checked = true;
        changeSetting();
    });
}