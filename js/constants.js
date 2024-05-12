export const properties = {
    "pareto": { fullName: "Pareto optimality", shortName: "Pareto" },
    "jr": { fullName: "Justified Representation (JR)", shortName: "JR" },
    "pjr": { fullName: "Proportional Justified Representation (PJR)", shortName: "PJR" },
    "ejr": { fullName: "Extended Justified Representation (EJR)", shortName: "EJR" },
    "ejr+": { fullName: "EJR+ without cohesiveness", shortName: "EJR+" },
    "fjr": { fullName: "Full Justified Representation (FJR)", shortName: "FJR" },
    "priceability": { fullName: "Priceability" },
    "core": { fullName: "Core", shortName: "Core" },
}

export const rules = {
    "av": {
        "fullName": "Approval Voting (AV)",
        "shortName": "AV",
        "active": 1,
        "weight": true
    },
    "sav": {
        "fullName": "Satisfaction Approval Voting (SAV)",
        "shortName": "SAV",
        "active": 0,
        "weight": true
    },
    "pav": {
        "fullName": "Proportional Approval Voting (PAV)",
        "shortName": "PAV",
        "active": 1,
        "weight": true
    },
    "slav": {
        "fullName": "Sainte-Laguë Approval Voting (SLAV)",
        "shortName": "SLAV",
        "active": 0,
        "weight": true
    },
    "cc": {
        "fullName": "Approval Chamberlin-Courant (CC)",
        "shortName": "CC",
        "active": 0,
        "weight": true
    },
    "lexcc": {
        "fullName": "Lexicographic Chamberlin-Courant (lex-CC)",
        "shortName": "lex-CC",
        "active": 0,
        "weight": true
    },
    "geom2": {
        "fullName": "2-Geometric Rule",
        "shortName": "2-Geometric",
        "active": 0,
        "weight": true
    },
    "seqpav": {
        "fullName": "Sequential Proportional Approval Voting (seq-PAV)",
        "shortName": "seq-PAV",
        "active": 0,
        "weight": true
    },
    "revseqpav": {
        "fullName": "Reverse Sequential Proportional Approval Voting (revseq-PAV)",
        "shortName": "revseq-PAV",
        "active": 0,
        "weight": true
    },
    "seqslav": {
        "fullName": "Sequential Sainte-Laguë Approval Voting (seq-SLAV)",
        "shortName": "seq-SLAV",
        "active": 0,
        "weight": true
    },
    "seqcc": {
        "fullName": "Sequential Approval Chamberlin-Courant (seq-CC)",
        "shortName": "seq-CC",
        "active": 0,
        "weight": true
    },
    "seqphragmen": {
        "fullName": "Phragmén's Sequential Rule (seq-Phragmén)",
        "shortName": "seq-Phragmén",
        "active": 1,
        "weight": true
    },
    "minimaxphragmen": {
        "fullName": "Phragmén's Minimax Rule (minimax-Phragmén)",
        "shortName": "minimax-Phragmén",
        "active": 0,
        "weight": true
    },
    "leximaxphragmen": {
        "fullName": "Phragmén's Leximax Rule (leximax-Phragmén)",
        "shortName": "leximax-Phragmén",
        "active": 0,
        "weight": true
    },
    "maximin-support": {
        "fullName": "Maximin Support Method (MMS)",
        "shortName": "Maximin Support",
        "active": 1,
        "weight": true
    },
    "monroe": {
        "fullName": "Monroe's Approval Rule (Monroe)",
        "shortName": "Monroe",
        "active": 0,
        "weight": true
    },
    "greedy-monroe": {
        "fullName": "Greedy Monroe",
        "shortName": "greedy-Monroe",
        "active": 0.4,
        "weight": false
    },
    "minimaxav": {
        "fullName": "Minimax Approval Voting (MAV)",
        "shortName": "MAV",
        "active": 1,
        "weight": true
    },
    "lexminimaxav": {
        "fullName": "Lexicographic Minimax Approval Voting (lex-MAV)",
        "shortName": "lex-MAV",
        "active": 0,
        "weight": true
    },
    "equal-shares": {
        "fullName": "Method of Equal Shares (aka Rule X) with Phragmén phase",
        "shortName": "Equal Shares",
        "active": 1,
        "weight": false
    },
    "equal-shares-with-av-completion": {
        "fullName": "Method of Equal Shares (aka Rule X) with AV completion",
        "shortName": "Equal Shares + AV",
        "active": 0,
        "weight": false
    },
    "equal-shares-with-increment-completion": {
        "fullName": "Method of Equal Shares (aka Rule X) with increment completion",
        "shortName": "Equal Shares + incr.",
        "active": 0,
        "weight": false
    },
    "phragmen-enestroem": {
        "fullName": "Method of Phragmén-Eneström",
        "shortName": "Eneström",
        "active": 0,
        "weight": true
    },
    "consensus-rule": {
        "fullName": "Consensus Rule",
        "shortName": "Consensus",
        "active": 0,
        "weight": true
    },
    "trivial": {
        "fullName": "Trivial Rule",
        "shortName": "Trivial",
        "active": 0,
        "weight": true
    },
    "rsd": {
        "fullName": "Random Serial Dictator",
        "shortName": "RSD",
        "active": 0,
        "weight": true
    },
    "eph": {
        "fullName": "E Pluribus Hugo (EPH)",
        "shortName": "E Pluribus Hugo",
        "active": 0,
        "weight": true
    },
}

export const deleteIconHTML = `<div class="delete-icon">
    <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" fill="currentColor" class="bi bi-trash3" viewBox="0 0 16 16">
        <path d="M6.5 1h3a.5.5 0 0 1 .5.5v1H6v-1a.5.5 0 0 1 .5-.5ZM11 2.5v-1A1.5 1.5 0 0 0 9.5 0h-3A1.5 1.5 0 0 0 5 1.5v1H2.506a.58.58 0 0 0-.01 0H1.5a.5.5 0 0 0 0 1h.538l.853 10.66A2 2 0 0 0 4.885 16h6.23a2 2 0 0 0 1.994-1.84l.853-10.66h.538a.5.5 0 0 0 0-1h-.995a.59.59 0 0 0-.01 0H11Zm1.958 1-.846 10.58a1 1 0 0 1-.997.92h-6.23a1 1 0 0 1-.997-.92L3.042 3.5h9.916Zm-7.487 1a.5.5 0 0 1 .528.47l.5 8.5a.5.5 0 0 1-.998.06L5 5.03a.5.5 0 0 1 .47-.53Zm5.058 0a.5.5 0 0 1 .47.53l-.5 8.5a.5.5 0 1 1-.998-.06l.5-8.5a.5.5 0 0 1 .528-.47ZM8 4.5a.5.5 0 0 1 .5.5v8.5a.5.5 0 0 1-1 0V5a.5.5 0 0 1 .5-.5Z"/>
    </svg>
</div>`;

export const infoIconHtml = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-info-circle" viewBox="0 0 16 16">
    <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
    <path d="m8.93 6.588-2.29.287-.082.38.45.083c.294.07.352.176.288.469l-.738 3.468c-.194.897.105 1.319.808 1.319.545 0 1.178-.252 1.465-.598l.088-.416c-.2.176-.492.246-.686.246-.275 0-.375-.193-.304-.533L8.93 6.588zM9 4.5a1 1 0 1 1-2 0 1 1 0 0 1 2 0z"/>
</svg>`;