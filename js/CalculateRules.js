import { settings, state } from './globalState.js';
import { rules, properties } from './constants.js';
import { startLog, getLog, storedLogs } from './logger.js';

function computeTiedCommittees() {
    let rule = document.getElementById("compute-tied-committees-button").dataset.rule;
    let result = _calculateRule(rule, true)[0];
    let pre = document.getElementById("committee-info-modal-all-committees");
    pre.innerHTML = "";
    pre.innerHTML = result.map(committee => committee.join(",")).join("\n");
}

function populateCommitteeInfoModal(rule) {
    document.getElementById("committee-info-modal-log").innerHTML = storedLogs[rule].join("\n");
    document.getElementById("compute-tied-committees-button").dataset.rule = rule;
    document.getElementById("compute-tied-committees-button").addEventListener("click", computeTiedCommittees);
    let pre = document.getElementById("committee-info-modal-all-committees");
    pre.innerHTML = "";
    // compute properties
    setTimeout(() => {
        let propList = document.getElementById("committee-info-modal-properties-list");
        propList.innerHTML = "";
        for (let prop in properties) {
            startLog();
            let result = window.pyodide.runPython(`
                properties.check("${prop}", profile, ${JSON.stringify(state.storedCommittee[rule])})
            `);
            let info = getLog();
            let details = document.createElement("details");
            let summary = document.createElement("summary");
            if (result) {
                summary.classList.add("satisfied");
                summary.innerHTML = properties[prop].fullName + ": ✓ satisfied";
            } else {
                summary.classList.add("failed");
                summary.innerHTML = properties[prop].fullName + ": ✗ failed";
            }
            details.appendChild(summary);
            let pre = document.createElement("pre");
            pre.innerHTML = info.join("\n");
            details.appendChild(pre);
            propList.appendChild(details);
        }
    }, 0);
}

function _calculateRule(rule, forceIrresolute = false) {
    startLog();
    let result;
    if (settings.resolute && !forceIrresolute) {
        result = window.pyodide.runPython(`
            raw_results = abcrules.compute(
                "${rule}", 
                profile, 
                committeesize=${state.committeeSize}, 
                resolute=True,
                preferfractions=${settings.useFractions ? "True" : "False"},
            )
            results = [[c for c in committee] for committee in raw_results]
            json.dumps(results)
        `);
    } else {
        result = window.pyodide.runPython(`
            raw_results = abcrules.compute(
                "${rule}", 
                profile, 
                committeesize=${state.committeeSize}, 
                resolute=False,
                max_num_of_committees=10,
                preferfractions=${settings.useFractions ? "True" : "False"},
            )
            results = [[c for c in committee] for committee in raw_results]
            json.dumps(results)
        `);
    }
    let info = getLog();
    result = JSON.parse(result);
    return [result, info];
}

export async function calculateRules() {
    if (!settings.liveMode) {
        return;
    }
    // from u, make a profile string of the form
    // {0, 1, 2}, {3}, {0, 1, 2, 3}, {0, 1, 2, 4}, {0, 1}, {4}
    if (!settings.useWeights){
        let profileString = "[";
        for (let i of state.N) {
            let voterString = "{";
            for (let j of state.C) {
                if (state.u[j][i] == 1) {
                    voterString += j + ",";
                }
            }
            voterString = voterString.slice(0, -1); // remove trailing comma
            voterString += "}";
            if (voterString != '}') {
                profileString += voterString + ",";
            }
        }
        profileString = profileString.slice(0, -1) + "]"; // remove trailing comma
        window.pyodide.runPython(`
            profile = Profile(num_cand=${state.C.length})
            profile.add_voters(${profileString})
        `);
    } else {
        let profileString = "[";
        for (let i of state.N) {
            let voterString = "([";
            for (let j of state.C) {
                if (state.u[j][i] == 1) {
                    voterString += j + ",";
                }
            }
            voterString = voterString.slice(0, -1); // remove trailing comma
            voterString += "], ";
            voterString += state.w[i] + ")"
            if (voterString != '(], 1)') {
                profileString += voterString + ",";
            }
        }
        profileString = profileString.slice(0, -1) + "]"; // remove trailing comma
        window.pyodide.runPython(`
            profile = Profile(num_cand=${state.C.length})
            for values, weight in ${profileString}:
                profile.add_voter(Voter(values, weight=weight))
        `);
    }
    
    
    
    let table = document.getElementById("profile-table");
    let tBody = table.getElementsByTagName("tbody")[0];
    for (let rule in rules) {
        if (!rules[rule].active) {
            continue;
        }
        if (handleRuleDoesntSupportWeight(rule)){
            continue;
        }
        if (settings.resolute) {
            setTimeout(() => {
                let computeReturn = _calculateRule(rule);
                let result = computeReturn[0];
                let info = computeReturn[1];
                storedLogs[rule] = info;
                for (let committee of result) {
                    state.storedCommittee[rule] = committee;
                    for (let j of state.C) {
                        let cell = document.getElementById("rule-" + rule + "-candidate-" + j + "-cell");
                        if (committee.includes(j)) {
                            cell.innerHTML = "✓";
                            cell.classList.add("in-committee");
                        } else {
                            cell.innerHTML = "";
                            cell.classList.add("not-in-committee");
                        }
                    }
                }
                let row = document.getElementById("rule-" + rule + "-row");
                row.dataset.hystmodal = "#committee-info-modal";
                row.onclick = function () {
                    populateCommitteeInfoModal(rule);
                };
                if (settings.showPropertyinTable) {
                    setTimeout(() => {
                        let cell = document.getElementById("rule-" + rule + "-property-cell");
                        let result = window.pyodide.runPython(`
                            properties.check("${settings.showPropertyinTable}", profile, ${JSON.stringify(state.storedCommittee[rule])})
                        `);
                        if (result) {
                            let span = document.createElement("span");
                            span.classList.add("property-cell-satisfied");
                            span.innerHTML = "✓ " + properties[settings.showPropertyinTable].shortName;
                            cell.appendChild(span);
                        } else {
                            let span = document.createElement("span");
                            span.classList.add("property-cell-failed");
                            span.innerHTML = "✗ " + properties[settings.showPropertyinTable].shortName;
                            cell.appendChild(span);
                        }
                    }, 0);
                }
            }, 0);
        } else {
            let computeReturn = await _calculateRule(rule);
            let result = computeReturn[0];
            let info = computeReturn[1];
            // add to table
            for (let committee of result) {
                // need to add rows
                let row = tBody.insertRow();
                let cell = row.insertCell();
                let span = document.createElement("span");
                span.innerHTML = rules[rule].shortName;
                tippy(span, {
                    content: rules[rule].fullName,
                    theme: "light",
                });
                cell.appendChild(span);
                for (let j of state.C) {
                    let cell = row.insertCell();
                    if (committee.includes(j)) {
                        cell.innerHTML = "✓";
                    } else {
                        cell.innerHTML = "";
                    }
                }
            }
        }
    }
    return true;
}

export async function rulesDontSupportWeight(){
    if (!settings.liveMode) {
        return;
    }
    for (let rule in rules) {
        if (!rules[rule].active) {
            continue;
        }
        handleRuleDoesntSupportWeight(rule)
    }
}

function handleRuleDoesntSupportWeight(rule){
    if (settings.useWeights && !rules[rule].weight){
        for (let j of state.C) {
            let cell = document.getElementById("rule-" + rule + "-candidate-" + j + "-cell");
            cell.innerHTML = "";
            cell.className = "";
        }
        let row = document.getElementById("rule-" + rule + "-row");
        row.classList.remove("rule-row")
        return true
    }
    return false
}