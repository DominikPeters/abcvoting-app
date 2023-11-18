import { rules } from './constants.js';

export function setRuleActive(rule, active) {
    rules[rule].active = active;
    document.getElementById('rule-choice-' + rule).checked = active;
    let number_selected = Object.values(rules).filter(rule => rule.active).length;
    document.getElementById('choose-rules-button-text').innerText = 'Choose rules (' + number_selected + ' / ' + Object.keys(rules).length + ' selected)';
}

export function populateRuleChoiceModal() {
    document.getElementById('selectAllRulesButton').addEventListener('click', () => {
        for (let rule in rules) {
            setRuleActive(rule, true);
        }
    });
    
    document.getElementById('deselectAllRulesButton').addEventListener('click', () => {
        for (let rule in rules) {
            setRuleActive(rule, false);
        }
    });

    let list = document.getElementById('rule-choice-list');
    for (let rule of Object.keys(rules)) {
        let li = document.createElement('li');
        let checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = 'rule-choice-' + rule;
        checkbox.value = rule;
        checkbox.checked = rules[rule].active;
        checkbox.addEventListener('change', function () {
            setRuleActive(rule, checkbox.checked);
        });
        li.appendChild(checkbox);
        let label = document.createElement('label');
        label.htmlFor = 'rule-choice-' + rule;
        label.appendChild(document.createTextNode(rules[rule].fullName));
        li.appendChild(label);
        list.appendChild(li);
    }
}