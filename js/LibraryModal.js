import { setRuleActive } from './RuleSelection.js';
import { buildTable } from './TableBuilder.js'; 
import { setInstance } from './InstanceManagement.js';
import { settings } from './globalState.js';


export function populateLibraryModal() {
    for (let button of document.querySelectorAll("#library-list button")) {
        button.addEventListener('click', function () {
            let numCands = parseInt(this.dataset.numCands);
            let k = parseInt(this.dataset.k)
            let with_weights = this.dataset.weights? "True" : "False"
            let result = JSON.parse(window.pyodide.runPython(`
                profile = Profile(num_cand=${numCands})
                if ${with_weights}:
                    for values, weight in ${this.dataset.profile}:
                        profile.add_voter(Voter(values, weight=weight))
                else:
                    profile.add_voters(${this.dataset.profile})
                u = {j : {i : 0 for i in range(len(profile))} for j in range(${numCands})}
                for i, voter in enumerate(profile):
                    for candidate in voter.approved:
                        u[candidate][i] = 1
                w = {i: voter.weight for i, voter in enumerate(profile)}
                json.dumps({"n" : len(profile), "u" : u, "w" : w })
            `));
            let u_ = result.u;
            let N_ = Array.from(Array(result.n).keys());
            let w_ = result.w
            let C_ = Array.from(Array(numCands).keys());
            if (this.dataset.weights){
                settings.useWeights = true;
                let useWeights = document.getElementById("weights");
                useWeights.checked = true;
            } else {
                settings.useWeights = false;
                let useWeights = document.getElementById("weights");
                useWeights.checked = false;
            }
            setInstance(N_, C_, u_, k,w_);
            if (this.dataset.activateRule) {
                setRuleActive(this.dataset.activateRule, true);
            }
            buildTable();
            window.modals.close();
        });
    }
}