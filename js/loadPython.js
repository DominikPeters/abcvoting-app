import { calculateRules } from './CalculateRules.js';

export async function loadPython() {
    document.getElementById("loading-container").style.display = "block";
    let loading = document.getElementById("loading-indicator");
    window.highs = await HiGHS();
    loading.innerHTML = "Loading... (20%)";
    window.pyodide = await loadPyodide();
    loading.innerHTML = "Loading... (30%)";
    await window.pyodide.loadPackage("micropip");
    const micropip = window.pyodide.pyimport("micropip");
    loading.innerHTML = "Loading... (40%)";
    // await micropip.install("/pulp-master/dist/PuLP-2.7.0-py3-none-any.whl?" + Math.random(), keep_going = true);
    await micropip.install("pip/PuLP-2.7.0-py3-none-any.whl?1", true);
    loading.innerHTML = "Loading... (50%)";
    await micropip.install("numpy", true);
    loading.innerHTML = "Loading... (60%)";
    await micropip.install("gmpy2", true);
    loading.innerHTML = "Loading... (70%)";
    await window.pyodide.runPython(`
        import micropip
        micropip.install("ruamel.yaml", deps=False)`);
    loading.innerHTML = "Loading... (80%)";
    // await micropip.install("/abcvoting-master/dist/abcvoting-0.0.0-py3-none-any.whl?" + Math.random(), keep_going = true);
    await micropip.install("abcvoting/abcvoting-2.9.0.dev0-py3-none-any.whl", true);
    loading.innerHTML = "Loading... (90%)";
    await window.pyodide.runPython(`
        import js
        import json
        from abcvoting.preferences import Profile
        from abcvoting import abcrules, properties, fileio
        from abcvoting.generate import random_profile, PointProbabilityDistribution
        from abcvoting.output import output, INFO, DETAILS
    `);
    // enable all buttons and inputs
    document.querySelectorAll("button, input").forEach(function (el) {
        el.disabled = false;
    });
    calculateRules();
    loading.innerHTML = "Loading... (100%)";
    // hide loading indicator after 200ms
    setTimeout(function () {
        document.getElementById("loading-container").style.display = "none";
    }, 200);
}