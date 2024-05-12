export const state = {
    N: 0,
    C: 0,
    u: {},
    w: {},
    committeeSize: 12,
    storedCommittee: {}
}

export const settings = {
    resolute: true,
    liveMode: true,
    useWeights: false,
    useFractions: false,
    showPropertyinTable: false,
    randomizer: { id: 'IC', p: 0.5 },
}

export let storedLogs = {};

export let pyodide;
export let highs;
export let micropip;