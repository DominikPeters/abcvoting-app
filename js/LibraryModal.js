import { setRuleActive } from './RuleSelection.js';
import { buildTable } from './TableBuilder.js'; 
import { setInstance } from './InstanceManagement.js';

export function populateLibraryModal() {
    for (let button of document.querySelectorAll("#library-list button")) {
        button.addEventListener('click', function () {
            let numCands = parseInt(this.dataset.numCands);
            let k = parseInt(this.dataset.k);
            let result = JSON.parse(window.pyodide.runPython(`
                profile = Profile(num_cand=${numCands})
                profile.add_voters(${this.dataset.profile})
                u = {j : {i : 0 for i in range(profile.totalweight())} for j in range(${numCands})}
                for i, voter in enumerate(profile):
                    for candidate in voter.approved:
                        u[candidate][i] = 1
                json.dumps({"n" : profile.totalweight(), "u" : u})
            `));
            let u_ = result.u;
            let N_ = Array.from(Array(result.n).keys());
            let C_ = Array.from(Array(numCands).keys());
            setInstance(N_, C_, u_, k);
            if (this.dataset.activateRule) {
                setRuleActive(this.dataset.activateRule, true);
            }
            buildTable();
            window.modals.close();
        });
    }
}