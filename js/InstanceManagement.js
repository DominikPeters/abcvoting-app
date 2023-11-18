import { state } from './globalState.js';
import { buildTable } from './TableBuilder.js';

export function addVoter() {
    let newVoter = state.N.slice(-1)[0] + 1;
    state.N.push(newVoter);
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
    buildTable();
}

export function setInstance(N_, C_, u_, committeeSize_) {
    state.N = N_;
    state.C = C_;
    state.u = u_;
    document.getElementById('committee-size-input').max = state.C.length - 1;
    document.getElementById('committee-size-range').max = state.C.length - 1;
    setCommitteeSize(committeeSize_);
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
    // check that all lines have the same length
    if (lines.every(line => line.length === lines[0].length)) {
        let numCands = lines[0].length;
        let numVoters = lines.length;
        let N_ = Array.from(Array(numVoters).keys());
        let C_ = Array.from(Array(numCands).keys());
        let u_ = {};
        for (let j of C_) {
            u_[j] = {};
            for (let i of N_) {
                u_[j][i] = parseInt(lines[i][j]);
            }
        }
        setInstance(N_, C_, u_, state.committeeSize);
        return true;
    } else {
        return false;
    }
}
