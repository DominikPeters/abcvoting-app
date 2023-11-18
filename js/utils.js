export function debounce(func, timeout = 500) {
    let timer;
    return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => {
            func.apply(this, args);
        }, timeout);
    };
}

export function sum(xs) {
    return xs.reduce((a, b) => a + b, 0);
}

export function round2(x) {
    return Math.round(x * 100) / 100;
}

export function profileToMatrix(state) {
    var text = "";
    // turn instance into 0/1 matrix, one row per voter
    for (let i of state.N) {
        for (let j of state.C) {
            text += state.u[j][i];
        }
        text += "\n";
    }
    return text;
}