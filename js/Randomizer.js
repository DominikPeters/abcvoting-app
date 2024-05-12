import { state, settings } from './globalState.js';
import { buildTable } from './TableBuilder.js';
import { setInstance } from './InstanceManagement.js';

export function populateRandomizerModal(attachListeners=false) {
    for (let radio of document.getElementsByName('randomize')) {
        let parentLi = radio.parentElement;
        let randomizer = { id: radio.value };
        for (let div of parentLi.getElementsByTagName('div')) {
            div.style.display = radio.checked ? 'block' : 'none';
            // inputs
            for (let input of div.getElementsByTagName('input')) {
                let key = input.id.split('-').slice(-1)[0];
                randomizer[key] = input.value;
                if (attachListeners) {
                    input.addEventListener('change', function () {
                        populateRandomizerModal();
                    });
                }
            }
            // selects
            for (let select of div.getElementsByTagName('select')) {
                let key = select.id.split('-').slice(-1)[0];
                randomizer[key] = select.value;
                if (attachListeners) {
                    select.addEventListener('change', function () {
                        populateRandomizerModal();
                    });
                }
            }
        }
        if (radio.value == "Euclidean VCR") {
            randomizer["voter_radius"] = `${randomizer["radius"] / 2}`;
            randomizer["candidate_radius"] = `${randomizer["radius"] / 2}`;
            delete randomizer["radius"];
        }
        if (radio.checked) {
            // Check Euclidean integrity
            document.getElementById("Euclidean VCR-warning").style.display = "none";
            document.getElementById("Euclidean fixed-size-warning").style.display = "none";
            if (radio.value == "Euclidean VCR" &&
                document.getElementById("Euclidean VCR-voter_prob_distribution").value.includes("1d") != document.getElementById("Euclidean VCR-candidate_prob_distribution").value.includes("1d")) {
                randomizer["voter_prob_distribution"] = "1d_interval";
                randomizer["candidate_prob_distribution"] = "1d_interval";
                document.getElementById("Euclidean VCR-warning").style.display = "block";
            }
            if (radio.value == "Euclidean fixed-size" &&
                document.getElementById("Euclidean fixed-size-voter_prob_distribution").value.includes("1d") != document.getElementById("Euclidean fixed-size-candidate_prob_distribution").value.includes("1d")) {
                randomizer["voter_prob_distribution"] = "1d_interval";
                randomizer["candidate_prob_distribution"] = "1d_interval";
                document.getElementById("Euclidean fixed-size-warning").style.display = "block";
            }
            // Set randomizer
            settings.randomizer = randomizer;
        }
        if (attachListeners) {
            radio.addEventListener('change', function () {
                populateRandomizerModal();
            });
        }
    }
}

export function randomize() {
    let result = JSON.parse(window.pyodide.runPython(`
        prob_distribution = ${JSON.stringify(settings.randomizer)}
        # go through fields in prob_distribution and replace strings with floats or ints if possible
        for field in prob_distribution:
            if "distribution" in field:
                prob_distribution[field] = PointProbabilityDistribution(prob_distribution[field])
                continue
            if "." in prob_distribution[field]:
                prob_distribution[field] = float(prob_distribution[field])
            else:
                try:
                    prob_distribution[field] = int(prob_distribution[field])
                except ValueError:
                    pass
        profile = random_profile(num_voters=${state.N.length}, num_cand=${state.C.length}, prob_distribution=prob_distribution)
        u = {j : {i : 0 for i in range(${state.N.length})} for j in range(${state.C.length})}
        for i, voter in enumerate(profile):
            for candidate in voter.approved:
                u[candidate][i] = 1
        w = {i : voter.weight for i, voter in enumerate(profile)}
        json.dumps({'u': u, 'w': w})
    `));
    let u_ = result.u;
    let w_ = result.w;
    setInstance(state.N, state.C, u_, state.committeeSize, w_);
    buildTable();
}