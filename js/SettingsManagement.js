import { state, settings } from "./globalState.js";
import { buildTable } from "./TableBuilder.js";
import { rulesDontSupportWeight, calculateRules } from './CalculateRules.js';
import { setInstance } from './InstanceManagement.js';

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
    const useWeightsCheckbox = document.getElementById("weights");
    useWeightsCheckbox.addEventListener("change", function () {
        if (useWeightsCheckbox.checked == settings.useWeights) {
            return; // no change
        }
        if (!useWeightsCheckbox.checked) {
            if (Object.values(state.w).some(w => w != 1)) {
                // attempting to turn off weights when some are not 1
                // ask user for choice of action
                useWeightsCheckbox.checked = true;
                window.modals.open("#turn-off-weights-modal");
                return;
            }
        }
        settings.useWeights = useWeightsCheckbox.checked;
        document.body.classList.toggle("using-weights", useWeightsCheckbox.checked);
        buildTable();
        if (window.pyodide) {
            if (useWeightsCheckbox.checked) {
                rulesDontSupportWeight();
            } else {
                calculateRules();
            }
        }
    });
    // turn off weights action choice modal
    document.getElementById("all-weights-1-button").addEventListener("click", function () {
        for (let voter in state.w) {
            state.w[voter] = 1;
        }
        const useWeightsCheckbox = document.getElementById("weights");
        useWeightsCheckbox.checked = false;
        useWeightsCheckbox.dispatchEvent(new Event('change'));
        window.modals.close();
    });
    document.getElementById("duplicate-voters-button").addEventListener("click", function () {
        let result = JSON.parse(window.pyodide.runPython(`
        profile.convert_to_unit_weights()
        u = {j : {i : 0 for i in range(len(profile))} for j in range(${state.C.length})}
        for i, voter in enumerate(profile):
            for candidate in voter.approved:
                u[candidate][i] = 1
        w = {i : voter.weight for i, voter in enumerate(profile)}
        json.dumps({'N': list(range(len(profile))), 'u': u, 'w': w})`));
        setInstance(result.N, state.C, result.u, state.committeeSize, result.w);
        const useWeightsCheckbox = document.getElementById("weights");
        useWeightsCheckbox.checked = false;
        useWeightsCheckbox.dispatchEvent(new Event('change'));
        window.modals.close();
    });
}