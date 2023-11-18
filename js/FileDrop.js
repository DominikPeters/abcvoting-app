import { state } from './globalState.js';
import { buildTable } from './TableBuilder.js';
import { setInstance, loadMatrix } from './InstanceManagement.js';

function dragOverHandler(ev) {
    document.getElementById('drop-overlay').style.display = "block";
    ev.preventDefault();
}

function dragStartHandler(ev) {
    document.getElementById('drop-overlay').style.display = "block";
    ev.preventDefault();
}

function dragEndHandler(ev) {
    document.getElementById('drop-overlay').style.display = "none";
    ev.preventDefault();
}

function dropHandler(ev) {
    document.getElementById('drop-overlay').style.display = "none";
    ev.preventDefault();
    if (ev.dataTransfer.items) {
        [...ev.dataTransfer.items].forEach((item, i) => {
            // If dropped items aren't files, reject them
            if (item.kind === "file") {
                let file = item.getAsFile();
                let reader = new FileReader();
                reader.onload = function (e) {
                    let text = e.target.result;
                    if (file.name.endsWith(".txt")) {
                        if (loadMatrix(text)) {
                            buildTable();
                        }
                    } else if (file.name.endsWith(".abc.yaml")) {
                        try {
                            let yamlImport = JSON.parse(window.pyodide.runPython(`
filetext = """${text}"""
profile, committeesize, _, _ = fileio.read_abcvoting_yaml_file(filetext)
return_object = {'num_cand': profile.num_cand, 'num_voter': len(profile), 'committeesize': committeesize}
u = {j : {i : 0 for i in range(len(profile))} for j in range(profile.num_cand)}
for i, voter in enumerate(profile):
for candidate in voter.approved:
u[candidate][i] = 1
return_object['u'] = u
json.dumps(return_object)
                            `));
                            N_ = Array.from(Array(yamlImport.num_voter).keys());
                            C_ = Array.from(Array(yamlImport.num_cand).keys());
                            u_ = yamlImport.u;
                            committeeSize_ = yamlImport.committeesize;
                            setInstance(N_, C_, u_, committeeSize_);
                            buildTable();
                        } catch (e) {
                            console.log(e);
                        }
                    } else if (file.name.endsWith(".soi")
                        || file.name.endsWith(".toi")
                        || file.name.endsWith(".soc")
                        || file.name.endsWith(".toc")) {
                        try {
                            let preflibImport = JSON.parse(window.pyodide.runPython(`
filetext = """${text}"""
profile = fileio.read_preflib_file(filetext)
return_object = {'num_cand': profile.num_cand, 'num_voter': len(profile)}
u = {j : {i : 0 for i in range(len(profile))} for j in range(profile.num_cand)}
for i, voter in enumerate(profile):
for candidate in voter.approved:
u[candidate][i] = 1
return_object['u'] = u
json.dumps(return_object)
                            `));
                            N_ = Array.from(Array(preflibImport.num_voter).keys());
                            C_ = Array.from(Array(preflibImport.num_cand).keys());
                            u_ = preflibImport.u;
                            setInstance(N_, C_, u_, state.committeeSize);
                            buildTable();
                        } catch (e) {
                            console.log(e);
                        }
                    }
                };
                reader.readAsText(file);
            }
        });
    }
}

export function setUpDragDropHandlers() {
    document.body.ondrop = dropHandler;
    document.body.ondragover = dragOverHandler;
    document.body.ondragenter = dragStartHandler;
    document.body.ondragleave = dragEndHandler;
}