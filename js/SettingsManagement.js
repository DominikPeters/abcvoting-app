import { settings } from "./globalState.js";
import { buildTable } from "./TableBuilder.js";
import { rulesDontSupportWeight, calculateRules } from './CalculateRules.js';

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

export function changeUseWeightSetting() {
    let useWeights = document.getElementById("weights");
    useWeights.addEventListener("change", function () {
        var weightCells = document.getElementsByClassName("weight-cell");
        if (!useWeights.checked) {
            for (let i = 1; i < weightCells.length; i++) {
                if (weightCells[i].children[0] && weightCells[i].children[0].value != 1) {
                    alert("Weight values must be set to 1 in order to remove them")
                    useWeights.checked = true;
                    return;
                }
            }
        }
        settings.useWeights = useWeights.checked;
        document.body.classList.toggle("using-weights", useWeights.checked);
        buildTable();
        if (window.pyodide) {
            if (useWeights.checked) {
                rulesDontSupportWeight();
            } else {
                calculateRules();
            }
        }
    });
}