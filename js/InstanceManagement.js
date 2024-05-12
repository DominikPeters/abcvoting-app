import { state, settings } from './globalState.js';
import { buildTable } from './TableBuilder.js';

export function addVoter() {
    let newVoter = state.N.slice(-1)[0] + 1;
    state.N.push(newVoter);
    state.w[newVoter] = 1;
    for (let j of state.C) {
        state.u[j][newVoter] = 0;
    }
    buildTable();
}

export function addCandidate() {
    let newCandidate = state.C.slice(-1)[0] + 1;
    state.C.push(newCandidate);
    state.u[newCandidate] = {};
    for (let i of state.N) {
        state.u[newCandidate][i] = 0;
    }
    document.getElementById('committee-size-input').max = state.C.length - 1;
    buildTable();
}

export function deleteCandidate(candidate) {
    state.C.splice(state.C.indexOf(parseInt(candidate)), 1);
    if (state.committeeSize > state.C.length - 1) {
        setCommitteeSize(state.C.length - 1);
    }
    document.getElementById('committee-size-input').max = state.C.length - 1;
    document.getElementById('committee-size-range').max = state.C.length - 1;
    buildTable();
}

export function deleteVoter(voter) {
    state.N.splice(state.N.indexOf(parseInt(voter)), 1);
    delete state.w[voter];
    for (let j of state.C) {
        delete state.u[j][voter];
    }
    buildTable();
}

export function setInstance(N_, C_, u_, committeeSize_, w_) {
    state.N = N_;
    state.C = C_;
    state.u = u_;
    state.w = w_;
    document.getElementById('committee-size-input').max = state.C.length - 1;
    document.getElementById('committee-size-range').max = state.C.length - 1;
    setCommitteeSize(committeeSize_);
    // if any weight is not 1, use weights
    document.getElementById("weights").checked = settings.useWeights || Object.values(state.w).some(w => w != 1);
}

export function setCommitteeSize(committeeSize_) {
    state.committeeSize = Math.max(Math.min(committeeSize_, state.C.length - 1), 1);
    document.getElementById('committee-size-input').value = state.committeeSize;
    document.getElementById('committee-size-range').value = state.committeeSize;
}

export function loadMatrix(matrix) {
    var lines = matrix.split('\n');
    // remove empty lines
    lines = lines.filter(line => line.length > 0);
    if (lines.length == 0) {
        return;
    }
    // check that all lines have the same length
    const numCands = lines[0].indexOf('*') == -1 ? lines[0].length : lines[0].split('*')[1].length;
    const numVoters = lines.length;
    const N_ = Array.from(Array(numVoters).keys());
    const C_ = Array.from(Array(numCands).keys());
    const u_ = {};
    const w_ = {};
    const uStrings = {};
    for (let k in N_) {
        const parts = lines[k].split('*');
        if (parts.length == 2) {
            w_[k] = parseInt(parts[0]);
            uStrings[k] = parts[1];
        } else {
            w_[k] = 1;
            uStrings[k] = lines[k];
        }
        if (uStrings[k].length != numCands) {
            throw new Error("Inconsistent number of candidates");
        }
    }
    for (let j of C_) {
        u_[j] = {};
        for (let i of N_) {
            u_[j][i] = parseInt(uStrings[i][j]);
        }
    }
    setInstance(N_, C_, u_, state.committeeSize, w_);
}
