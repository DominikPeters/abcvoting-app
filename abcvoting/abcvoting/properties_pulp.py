import pulp
import json
import js

def mySolve(model):
    return json.loads(js.runHighs(model.writeLP()))

def _check_pareto_optimality_pulp(profile, committee):
    """
    Test, by an ILP and the pulp solver, whether a committee is Pareto optimal.

    That is, there is no other committee which dominates it.

    Parameters
    ----------
    profile : abcvoting.preferences.Profile
        A profile.
    committee : iterable of int
        A committee.

    Returns
    -------
    bool
    """

    # array to store number of approved candidates per voter in the query committee
    num_apprvd_cands_query = [len(voter.approved & committee) for voter in profile]

    model = pulp.LpProblem("pareto_optimality_check", pulp.LpMaximize)

    # binary variables: indicate whether voter i approves of
    # at least x candidates in the dominating committee
    utility = {}
    for voter in profile:
        for x in range(1, len(committee) + 1):
            utility[(voter, x)] = pulp.LpVariable(f"utility_{voter}_{x}", cat="Binary")

    # binary variables: indicate whether a candidate is inside the dominating committee
    in_committee = pulp.LpVariable.dicts("in_committee", profile.candidates, cat="Binary")

    # binary variables: determine for which voter(s) the condition of having strictly
    # more preferred candidates in dominating committee will be satisfied
    condition_strictly_more = pulp.LpVariable.dicts(
        "condition_strictly_more", range(len(profile)), cat="Binary"
    )

    # constraint: utility actually matches the number of approved candidates
    # in the dominating committee, for all voters
    for voter in profile:
        model += (
            pulp.lpSum(utility[(voter, x)] for x in range(1, len(committee) + 1))
            == pulp.lpSum(in_committee[cand] for cand in voter.approved)
        )

    # constraint: all voters should have at least as many preferred candidates
    # in the dominating committee as in the query committee
    for i, voter in enumerate(profile):
        model += (
            pulp.lpSum(utility[(voter, x)] for x in range(1, len(committee) + 1))
            >= num_apprvd_cands_query[i]
        )

    # constraint: the condition of having strictly more approved candidates in
    # dominating committee will be satisfied for at least one voter
    model += pulp.lpSum(condition_strictly_more) >= 1

    # loop through all variables in the condition_strictly_more array (there is one for each voter)
    # if it has value 1, then the condition of having strictly more preferred candidates on the
    # dominating committee has to be satisfied for this voter
    for i, voter in enumerate(profile):
        model += (
            pulp.lpSum(utility[(voter, x)] for x in range(1, len(committee) + 1))
            >= num_apprvd_cands_query[i] + condition_strictly_more[i]
        )

    # constraint: committee has the right size
    model += pulp.lpSum(in_committee) == len(committee)

    # set the objective function
    model += pulp.lpSum(
        utility[(voter, x)] for voter in profile for x in range(1, len(committee) + 1)
    )

    # solve the problem
    solution = mySolve(model)
    status = solution["Status"]
    value = {}
    for v in solution["Columns"]:
        value[v] = solution["Columns"][v]["Primal"]

    # return value based on status code
    # status code 1 means model was solved to optimality, thus a dominating committee was found
    if status == "Optimal":
        committee = {cand for cand in profile.candidates if value[in_committee[cand].name()] >= 0.9}
        detailed_information = {"dominating_committee": committee}
        return False, detailed_information

    # status code -1 means that model is infeasible, thus no dominating committee was found
    if status == "Infeasible":
        detailed_information = {}
        return True, detailed_information

    raise RuntimeError(f"Pulp returned an unexpected status code: {status}")

def _check_EJR_pulp(profile, committee):
    """
    Test, by an ILP and the pulp solver, whether a committee satisfies EJR.

    Parameters
    ----------
    profile : abcvoting.preferences.Profile
        A profile.
    committee : iterable of int
        A committee.

    Returns
    -------
    bool
    """

    # compute matrix-dictionary for voters approval
    # approval_matrix[(voter, cand)] = 1 if cand is in voter's approval set
    # approval_matrix[(voter, cand)] = 0 otherwise
    approval_matrix = {}
    for voter in profile:
        for cand in profile.candidates:
            if cand in voter.approved:
                approval_matrix[(voter, cand)] = 1
            else:
                approval_matrix[(voter, cand)] = 0

    # create the model to be optimized
    model = pulp.LpProblem("ejr_problem", pulp.LpMinimize)

    # integer variable: ell
    ell = pulp.LpVariable("ell", lowBound=1, upBound=len(committee), cat="Integer")

    # binary variables: indicate whether a voter is inside the ell-cohesive group
    in_group = [pulp.LpVariable(f"in_group_{i}", cat="Binary") for i in range(len(profile))]

    # constraints: size of ell-cohesive group should be appropriate wrt. ell
    model += pulp.lpSum(in_group) >= ell * len(profile) / len(committee)

    # constraints based on binary indicator variables:
    # if voter is in ell-cohesive group, then the voter should have
    # strictly less than ell approved candidates in committee
    for vi, voter in enumerate(profile):
        model += len(voter.approved & committee) + 1 <= ell + (1 - in_group[vi]) * len(committee)

    in_cut = [pulp.LpVariable(f"in_cut_{i}", cat="Binary") for i in range(profile.num_cand)]

    # the voters in group should agree on at least ell candidates
    model += pulp.lpSum(in_cut) >= ell

    # if a candidate is in the cut, then `approval_matrix[(voter, cand)]` *must be* 1 for all
    # voters inside the group
    for voter_index, voter in enumerate(profile):
        for cand in profile.candidates:
            if approval_matrix[(voter, cand)] == 0:
                model += in_cut[cand] + in_group[voter_index] <= 1.5  # not both true

    # model.setObjective(ell, gb.GRB.MINIMIZE)

    # solve the problem
    solution = mySolve(model)
    status = solution["Status"]
    value = {}
    for v in solution["Columns"]:
        value[v] = solution["Columns"][v]["Primal"]

    # return value based on status code
    # status code "Optimal" means model was solved to optimality, thus an ell-cohesive group
    # that satisfies the condition of EJR was found
    if status == "Optimal":
        cohesive_group = {vi for vi, _ in enumerate(profile) if value[in_group[vi].name()] >= 0.9}
        joint_candidates = {cand for cand in profile.candidates if value[in_cut[cand].name()] >= 0.9}
        detailed_information = {
            "cohesive_group": cohesive_group,
            "ell": round(value[ell.name()]),
            "joint_candidates": joint_candidates,
        }
        return False, detailed_information

    # status code "Infeasible" means that model is infeasible, thus no ell-cohesive group
    # that satisfies the condition of EJR was found
    if status == "Infeasible":
        detailed_information = {}
        return True, detailed_information

    raise RuntimeError(f"Pulp returned an unexpected status code: {status}")

def _check_PJR_pulp(profile, committee):
    """
    Test with a Pulp ILP whether a committee satisfies PJR.

    Parameters
    ----------
    profile : abcvoting.preferences.Profile
        A profile.
    committee : iterable of int
        A committee.

    Returns
    -------
    bool
    """

    # compute matrix-dictionary for voters approval
    # approval_matrix[(voter, cand)] = 1 if cand is in voter's approval set
    # approval_matrix[(voter, cand)] = 0 otherwise
    approval_matrix = {}

    for voter in profile:
        for cand in profile.candidates:
            if cand in voter.approved:
                approval_matrix[(voter, cand)] = 1
            else:
                approval_matrix[(voter, cand)] = 0

    # compute deterministically array of binary variables that
    # indicate whether a candidate is inside the input committee
    in_committee = []
    for cand in profile.candidates:
        if cand in committee:
            in_committee.append(1)
        else:
            in_committee.append(0)

    # create the model to be optimized
    model = pulp.LpProblem("PJR", pulp.LpMinimize)

    # integer variable: ell
    ell = pulp.LpVariable("ell", 1, len(committee), cat='Integer')

    # binary variables: indicate whether a voter is inside the ell-cohesive group
    in_group = {}
    for i in range(len(profile)):
        in_group[i] = pulp.LpVariable(f"in_group_{i}", cat='Binary')

    # constraint: size of ell-cohesive group should be appropriate wrt ell
    model += pulp.lpSum(in_group.values()) >= ell * len(profile) / len(committee)

    # binary variables: indicate whether a candidate is in the intersection
    # of approved candidates over voters inside the group
    in_cut = {}
    for cand in profile.candidates:
        in_cut[cand] = pulp.LpVariable(f"in_cut_{cand}", cat='Binary')

    # the voters in group should agree on at least ell candidates
    model += pulp.lpSum(in_cut.values()) >= ell

    # if a candidate is in the cut, then `approval_matrix[(voter, cand)]` *must be* 1 for all
    # voters inside the group
    for voter_index, voter in enumerate(profile):
        for cand in profile.candidates:
            if approval_matrix[(voter, cand)] == 0:
                model += in_cut[cand] + in_group[voter_index] <= 1.5  # not both true

    # binary variables: indicate whether a candidate is inside the union
    # of approved candidates, taken over voters that are in the ell-cohesive group
    in_union = {}
    for cand in profile.candidates:
        in_union[cand] = pulp.LpVariable(f"in_union_{cand}", cat='Binary')

    # compute the in_union variables, depending on the values of in_cut
    for vi, voter in enumerate(profile):
        for cand in voter.approved:
            model += in_union[cand] >= in_group[vi]

    # constraint to ensure that the intersection between candidates that are in union
    # intersected with the input committee, has size strictly less than ell
    model += pulp.lpSum([in_union[cand] * in_committee[cand] for cand in profile.candidates]) + 1 <= ell

    # model.setObjective(ell)

    # Solve the problem
    solution = mySolve(model)
    status = solution["Status"]
    value = {}
    for v in solution["Columns"]:
        value[v] = solution["Columns"][v]["Primal"]

    # return value based on status code
    # status code 1 means model was solved to optimality, thus an ell-cohesive group
    # that satisfies the condition of PJR was found
    if status == "Optimal":
        cohesive_group = {vi for vi, _ in enumerate(profile) if value[in_group[vi].name()] >= 0.9}
        joint_candidates = {cand for cand in profile.candidates if value[in_cut[cand].name()] >= 0.9}
        detailed_information = {
            "cohesive_group": cohesive_group,
            "ell": round(value[ell.name()]),
            "joint_candidates": joint_candidates,
        }
        return False, detailed_information

    # status code -1 means that model is infeasible, thus no ell-cohesive group
    # that satisfies the condition of PJR was found
    if status == "Infeasible":
        detailed_information = {}
        return True, detailed_information

    raise RuntimeError(f"Pulp returned an unexpected status code: {status}")

def _check_priceability_pulp(profile, committee, stable=False):
    """
    Test, by an ILP and the Pulp solver, whether a committee is priceable.

    Parameters
    ----------
    profile : abcvoting.preferences.Profile
        approval sets of voters
    committee : set
        set of candidates

    Returns
    -------
    bool

    References
    ----------
    Multi-Winner Voting with Approval Preferences.
    Martin Lackner and Piotr Skowron.
    <http://dx.doi.org/10.1007/978-3-031-09016-5>

    Market-Based Explanations of Collective Decisions.
    Dominik Peters, Grzegorz Pierczyski, Nisarg Shah, Piotr Skowron.
    <https://www.cs.toronto.edu/~nisarg/papers/priceability.pdf>
    """

    model = pulp.LpProblem("priceability", pulp.LpMinimize)

    approved_candidates = [
        cand for cand in profile.candidates if any(cand in voter.approved for voter in profile)
    ]
    if len(approved_candidates) < len(committee):
        # there are fewer candidates that are approved by at least one voter than candidates
        # in the committee.
        # in this case, return True iff all approved candidates appear in the committee
        # note: the original definition of priceability does not work in this case.
        return all(cand in committee for cand in approved_candidates)

    budget = pulp.LpVariable("budget", lowBound=0, cat="Continuous")
    payment = {}
    for voter in profile:
        payment[voter] = {}
        for candidate in profile.candidates:
            payment[voter][candidate] = pulp.LpVariable(
                f"payment_{voter}_{candidate}", lowBound=0, cat="Continuous"
            )

    # condition 1 [from "Multi-Winner Voting with Approval Preferences", Definition 4.8]
    for voter in profile:
        model += (
            pulp.lpSum(payment[voter][candidate] for candidate in profile.candidates) <= budget
        )

    # condition 2 [from "Multi-Winner Voting with Approval Preferences", Definition 4.8]
    for voter in profile:
        for candidate in profile.candidates:
            if candidate not in voter.approved:
                model += payment[voter][candidate] == 0

    # condition 3 [from "Multi-Winner Voting with Approval Preferences", Definition 4.8]
    for candidate in profile.candidates:
        if candidate in committee:
            model += (
                pulp.lpSum(payment[voter][candidate] for voter in profile) == 1
            )
        else:
            model += pulp.lpSum(payment[voter][candidate] for voter in profile) == 0

    if stable:
        # condition 4*
        # [from "Market-Based Explanations of Collective Decisions", Section 3.1, Equation (3)]
        for candidate in profile.candidates:
            if candidate not in committee:
                extrema = []
                for voter in profile:
                    if candidate in voter.approved:
                        extremum = pulp.LpVariable(
                            f"extremum_{voter}_{candidate}",
                            lowBound=0,
                            cat="Continuous",
                        )
                        extrema.append(extremum)
                        r = pulp.LpVariable(
                            f"r_{voter}_{candidate}", lowBound=0, cat="Continuous"
                        )
                        max_payment = pulp.LpVariable(
                            f"max_payment_{voter}_{candidate}",
                            lowBound=0,
                            cat="Continuous",
                        )
                        model += (
                            r
                            == budget
                            - pulp.lpSum(
                                payment[voter][committee_member]
                                for committee_member in committee
                            )
                        )
                        
                        
                        # PuLP translation of max constraints
                        # model.addGenConstrMax(
                        #     max_Payment,
                        #     [payment[voter][committee_member] for committee_member in committee],
                        # )
                        binary_vars = []
                        for committee_member in committee:
                            bin_var = pulp.LpVariable(f"binary_{voter}_{candidate}_{committee_member}", cat="Binary")
                            binary_vars.append(bin_var)
                            # if bin_var == 1, then payment[voter][committee_member] >= max_payment
                            model += max_payment >= payment[voter][committee_member] - (1 - bin_var) * budget
                            # if bin_var == 1, then payment[voter][committee_member] <= max_payment
                            model += max_payment <= payment[voter][committee_member] + (1 - bin_var) * budget

                        model += pulp.lpSum(binary_vars) == 1

                        # model.addGenConstrMax(extremum, [max_Payment, r])
                        binary_extremum = pulp.LpVariable(f"binary_extremum_{voter}_{candidate}", cat="Binary")
                        # if binary_extremum == 1, then extremum >= max_payment
                        model += extremum >= max_payment - (1 - binary_extremum) * budget
                        # if binary_extremum == 1, then extremum <= max_payment
                        model += extremum <= max_payment + (1 - binary_extremum) * budget
                        # if binary_extremum == 0, then extremum >= r
                        model += extremum >= r - binary_extremum * budget
                        # if binary_extremum == 0, then extremum <= r
                        model += extremum <= r + binary_extremum * budget

                model += pulp.lpSum(extrema) <= 1
    else:
        # condition 4 [from "Multi-Winner Voting with Approval Preferences", Definition 4.8]
        for candidate in profile.candidates:
            if candidate not in committee:
                model += (
                    pulp.lpSum(
                        budget
                        - pulp.lpSum(
                            payment[voter][committee_member]
                            for committee_member in committee
                        )
                        for voter in profile
                        if candidate in voter.approved
                    )
                    <= 1
                )

    model += budget

    solution = mySolve(model)
    status = solution["Status"]
    value = {}
    for v in solution["Columns"]:
        value[v] = solution["Columns"][v]["Primal"]

    if status == "Optimal":
        output.details(f"Budget: {value[budget.name()]}")

        column_widths = {
            candidate: max(
                len(str(value[payment[voter][candidate].name()])) for voter in payment
            )
            for candidate in profile.candidates
        }
        column_widths["voter"] = len(str(len(profile)))
        output.details(
            " " * column_widths["voter"]
            + " | "
            + " | ".join(
                str(i).rjust(column_widths[candidate])
                for i, candidate in enumerate(profile.candidates)
            )
        )
        for i, voter in enumerate(profile):
            output.details(
                str(i).rjust(column_widths["voter"])
                + " | "
                + " | ".join(
                    str(value[payment[voter][candidate].name()]).rjust(column_widths[candidate])
                    for candidate in profile.candidates
                )
            )

        return True
    elif status == "Infeasible":
        output.details("No feasible budget and payment function")
        return False
    else:
        raise RuntimeError(f"Pulp returned an unexpected status code: {status}")
    
def _check_core_gurobi(profile, committee, committeesize):
    """Test, by an ILP and the Gurobi solver, whether a committee is in the core.

    Parameters
    ----------
    profile : abcvoting.preferences.Profile
        approval sets of voters
    committee : set
        set of candidates
    committeesize : int
        size of committee

    Returns
    -------
    bool

    References
    ----------
    Multi-Winner Voting with Approval Preferences.
    Martin Lackner and Piotr Skowron.
    <http://dx.doi.org/10.1007/978-3-031-09016-5>
    """

    model = pulp.LpProblem("Core Test", pulp.LpMinimize)

    set_of_voters = [pulp.LpVariable(f"voter_{i}", cat=pulp.LpBinary) for i in range(len(profile))]
    set_of_candidates = [pulp.LpVariable(f"candidate_{i}", cat=pulp.LpBinary) for i in range(profile.num_cand)]

    model += pulp.lpSum(set_of_candidates) * len(profile) <= pulp.lpSum(set_of_voters) * committeesize
    model += pulp.lpSum(set_of_voters) >= 1
    for i, voter in enumerate(profile):
        approved = [
            (c in voter.approved) * set_of_candidates[i] for i, c in enumerate(profile.candidates)
        ]
        model += pulp.lpSum(approved) >= set_of_voters[i] * (len(voter.approved & committee) + 1)

    solution = mySolve(model)
    status = solution["Status"]
    value = {}
    for v in solution["Columns"]:
        value[v] = solution["Columns"][v]["Primal"]

    if status == "Optimal":
        coalition = {vi for vi, _ in enumerate(profile) if value[set_of_voters[vi].name()] >= 0.9}
        objection = {cand for cand in profile.candidates if value[set_of_candidates[cand].name()] >= 0.9}
        detailed_information = {
            "coalition": coalition,
            "objection": objection,
        }
        return False, detailed_information
    elif status == "Infeasible":
        detailed_information = {}
        return True, detailed_information
    else:
        raise RuntimeError(f"Pulp returned an unexpected status code: {status}")
