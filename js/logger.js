let logs = [];

export let storedLogs = {};

export function logger(verbosity, msg) {
    logs.push(msg);
}

export function startLog() {
    logs = [];
}

export function getLog() {
    return logs;
}