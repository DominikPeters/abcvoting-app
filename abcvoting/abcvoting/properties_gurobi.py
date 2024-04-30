def _check_pareto_optimality_gurobi(profile, committee):
    """
    Test, by an ILP and the Gurobi solver, whether a committee is Pareto optimal.

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

    model = gb.Model()

    # binary variables: indicate whether voter i approves of
    # at least x candidates in the dominating committee
    utility = {}
    for voter in profile:
        for x in range(1, len(committee) + 1):
            utility[(voter, x)] = model.addVar(vtype=gb.GRB.BINARY)

    # binary variables: indicate whether a candidate is inside the dominating committee
    in_committee = model.addVars(profile.num_cand, vtype=gb.GRB.BINARY, name="in_committee")

    # binary variables: determine for which voter(s) the condition of having strictly
    # more preferred candidates in dominating committee will be satisfied
    condition_strictly_more = model.addVars(
        range(len(profile)), vtype=gb.GRB.BINARY, name="condition_strictly_more"
    )

    # constraint: utility actually matches the number of approved candidates
    # in the dominating committee, for all voters
    for voter in profile:
        model.addConstr(
            gb.quicksum(utility[(voter, x)] for x in range(1, len(committee) + 1))
            == gb.quicksum(in_committee[cand] for cand in voter.approved)
        )

    # constraint: all voters should have at least as many preferred candidates
    # in the dominating committee as in the query committee
    for i, voter in enumerate(profile):
        model.addConstr(
            gb.quicksum(utility[(voter, x)] for x in range(1, len(committee) + 1))
            >= num_apprvd_cands_query[i]
        )

    # constraint: the condition of having strictly more approved candidates in
    # dominating committee will be satisfied for at least one voter
    model.addConstr(gb.quicksum(condition_strictly_more) >= 1)

    # loop through all variables in the condition_strictly_more array (there is one for each voter)
    # if it has value 1, then the condition of having strictly more preferred candidates on the
    # dominating committee has to be satisfied for this voter
    for i, voter in enumerate(profile):
        model.addConstr(
            (condition_strictly_more[i] == 1)
            >> (
                gb.quicksum(utility[(voter, x)] for x in range(1, len(committee) + 1))
                >= num_apprvd_cands_query[i] + 1
            )
        )

    # constraint: committee has the right size
    model.addConstr(gb.quicksum(in_committee) == len(committee))

    # set the objective function
    model.setObjective(
        gb.quicksum(
            utility[(voter, x)] for voter in profile for x in range(1, len(committee) + 1)
        ),
        gb.GRB.MAXIMIZE,
    )

    _set_gurobi_model_parameters(model)
    model.optimize()

    # return value based on status code
    # status code 2 means model was solved to optimality, thus a dominating committee was found
    if model.Status == 2:
        committee = {cand for cand in profile.candidates if in_committee[cand].Xn >= 0.9}
        detailed_information = {"dominating_committee": committee}
        return False, detailed_information

    # status code 3 means that model is infeasible, thus no dominating committee was found
    if model.Status == 3:
        detailed_information = {}
        return True, detailed_information

    raise RuntimeError(f"Gurobi returned an unexpected status code: {model.Status}")



def _check_EJR_gurobi(profile, committee):
    """
    Test, by an ILP and the Gurobi solver, whether a committee satisfies EJR.

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
    model = gb.Model()

    # integer variable: ell
    ell = model.addVar(vtype=gb.GRB.INTEGER, name="ell")

    # binary variables: indicate whether a voter is inside the ell-cohesive group
    in_group = model.addVars(len(profile), vtype=gb.GRB.BINARY, name="in_group")

    # constraints: ell has to be between 1 and committeesize inclusive
    model.addConstr(ell >= 1)
    model.addConstr(ell <= len(committee))

    # constraint: size of ell-cohesive group should be appropriate wrt. ell
    model.addConstr(gb.quicksum(in_group) >= ell * len(profile) / len(committee))

    # constraints based on binary indicator variables:
    # if voter is in ell-cohesive group, then the voter should have
    # strictly less than ell approved candidates in committee
    for vi, voter in enumerate(profile):
        model.addConstr((in_group[vi] == 1) >> (len(voter.approved & committee) + 1 <= ell))

    in_cut = model.addVars(profile.num_cand, vtype=gb.GRB.BINARY, name="in_cut")

    # the voters in group should agree on at least ell candidates
    model.addConstr(gb.quicksum(in_cut) >= ell)

    # if a candidate is in the cut, then `approval_matrix[(voter, cand)]` *must be* 1 for all
    # voters inside the group
    for voter_index, voter in enumerate(profile):
        for cand in profile.candidates:
            if approval_matrix[(voter, cand)] == 0:
                model.addConstr(in_cut[cand] + in_group[voter_index] <= 1.5)  # not both true

    # model.setObjective(ell, gb.GRB.MINIMIZE)

    _set_gurobi_model_parameters(model)
    model.optimize()

    # return value based on status code
    # status code 2 means model was solved to optimality, thus an ell-cohesive group
    # that satisfies the condition of EJR was found
    if model.Status == 2:
        cohesive_group = {vi for vi, _ in enumerate(profile) if in_group[vi].Xn >= 0.9}
        joint_candidates = {cand for cand in profile.candidates if in_cut[cand].Xn >= 0.9}
        detailed_information = {
            "cohesive_group": cohesive_group,
            "ell": round(ell.Xn),
            "joint_candidates": joint_candidates,
        }
        return False, detailed_information

    # status code 3 means that model is infeasible, thus no ell-cohesive group
    # that satisfies the condition of EJR was found
    if model.Status == 3:
        detailed_information = {}
        return True, detailed_information

    raise RuntimeError(f"Gurobi returned an unexpected status code: {model.Status}")



def _check_PJR_gurobi(profile, committee):
    """
    Test with a Gurobi ILP whether a committee satisfies PJR.

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
    model = gb.Model()

    # integer variable: ell
    ell = model.addVar(vtype=gb.GRB.INTEGER, name="ell")

    # binary variables: indicate whether a voter is inside the ell-cohesive group
    in_group = model.addVars(len(profile), vtype=gb.GRB.BINARY, name="in_group")

    # constraints: ell has to be between 1 and committeesize inclusive
    model.addConstr(ell >= 1)
    model.addConstr(ell <= len(committee))

    # constraint: size of ell-cohesive group should be appropriate wrt ell
    model.addConstr(gb.quicksum(in_group) >= ell * len(profile) / len(committee))

    # binary variables: indicate whether a candidate is in the intersection
    # of approved candidates over voters inside the group
    in_cut = model.addVars(profile.num_cand, vtype=gb.GRB.BINARY, name="in_cut")

    # the voters in group should agree on at least ell candidates
    model.addConstr(gb.quicksum(in_cut) >= ell)

    # if a candidate is in the cut, then `approval_matrix[(voter, cand)]` *must be* 1 for all
    # voters inside the group
    for voter_index, voter in enumerate(profile):
        for cand in profile.candidates:
            if approval_matrix[(voter, cand)] == 0:
                model.addConstr(in_cut[cand] + in_group[voter_index] <= 1.5)  # not both true

    # binary variables: indicate whether a candidate is inside the union
    # of approved candidates, taken over voters that are in the ell-cohesive group
    in_union = model.addVars(profile.num_cand, vtype=gb.GRB.BINARY, name="in_union")

    # compute the in_union variables, depending on the values of in_cut
    for vi, voter in enumerate(profile):
        for cand in voter.approved:
            model.addConstr((in_group[vi] == 1) >> (in_union[cand] == 1))

    # constraint to ensure that the intersection between candidates that are in union
    # intersected with the input committee, has size strictly less than ell
    model.addConstr(
        gb.quicksum(in_union[cand] * in_committee[cand] for cand in profile.candidates) + 1 <= ell
    )

    # model.setObjective(ell, gb.GRB.MINIMIZE)

    _set_gurobi_model_parameters(model)
    model.optimize()

    # return value based on status code
    # status code 2 means model was solved to optimality, thus an ell-cohesive group
    # that satisfies the condition of PJR was found
    if model.Status == 2:
        cohesive_group = {vi for vi, _ in enumerate(profile) if in_group[vi].Xn >= 0.9}
        joint_candidates = {cand for cand in profile.candidates if in_cut[cand].Xn >= 0.9}
        detailed_information = {
            "cohesive_group": cohesive_group,
            "ell": round(ell.Xn),
            "joint_candidates": joint_candidates,
        }
        return False, detailed_information

    # status code 3 means that model is infeasible, thus no ell-cohesive group
    # that satisfies the condition of PJR was found
    if model.Status == 3:
        detailed_information = {}
        return True, detailed_information

    raise RuntimeError(f"Gurobi returned an unexpected status code: {model.Status}")



def _check_priceability_gurobi(profile, committee, stable=False):
    """
    Test, by an ILP and the Gurobi solver, whether a committee is priceable.

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

    model = gb.Model()

    approved_candidates = [
        cand for cand in profile.candidates if any(cand in voter.approved for voter in profile)
    ]
    if len(approved_candidates) < len(committee):
        # there are fewer candidates that are approved by at least one voter than candidates
        # in the committee.
        # in this case, return True iff all approved candidates appear in the committee
        # note: the original definition of priceability does not work in this case.
        return all(cand in committee for cand in approved_candidates)

    budget = model.addVar(vtype=gb.GRB.CONTINUOUS)
    payment = {}
    for voter in profile:
        payment[voter] = {}
        for candidate in profile.candidates:
            payment[voter][candidate] = model.addVar(vtype=gb.GRB.CONTINUOUS)

    # condition 1 [from "Multi-Winner Voting with Approval Preferences", Definition 4.8]
    for voter in profile:
        model.addConstr(
            gb.quicksum(payment[voter][candidate] for candidate in profile.candidates) <= budget
        )

    # condition 2 [from "Multi-Winner Voting with Approval Preferences", Definition 4.8]
    for voter in profile:
        for candidate in profile.candidates:
            if candidate not in voter.approved:
                model.addConstr(payment[voter][candidate] == 0)

    # condition 3 [from "Multi-Winner Voting with Approval Preferences", Definition 4.8]
    for candidate in profile.candidates:
        if candidate in committee:
            model.addConstr(gb.quicksum(payment[voter][candidate] for voter in profile) == 1)
        else:
            model.addConstr(gb.quicksum(payment[voter][candidate] for voter in profile) == 0)

    if stable:
        # condition 4*
        # [from "Market-Based Explanations of Collective Decisions", Section 3.1, Equation (3)]
        for candidate in profile.candidates:
            if candidate not in committee:
                extrema = []
                for voter in profile:
                    if candidate in voter.approved:
                        extremum = model.addVar(vtype=gb.GRB.CONTINUOUS)
                        extrema.append(extremum)
                        r = model.addVar(vtype=gb.GRB.CONTINUOUS)
                        max_Payment = model.addVar(vtype=gb.GRB.CONTINUOUS)
                        model.addConstr(
                            r
                            == budget
                            - gb.quicksum(
                                payment[voter][committee_member] for committee_member in committee
                            )
                        )
                        model.addGenConstrMax(
                            max_Payment,
                            [payment[voter][committee_member] for committee_member in committee],
                        )
                        model.addGenConstrMax(extremum, [max_Payment, r])
                model.addConstr(gb.quicksum(extrema) <= 1)
    else:
        # condition 4 [from "Multi-Winner Voting with Approval Preferences", Definition 4.8]
        for candidate in profile.candidates:
            if candidate not in committee:
                model.addConstr(
                    gb.quicksum(
                        budget
                        - gb.quicksum(
                            payment[voter][committee_member] for committee_member in committee
                        )
                        for voter in profile
                        if candidate in voter.approved
                    )
                    <= 1
                )

    model.setObjective(budget)
    _set_gurobi_model_parameters(model)
    model.optimize()

    if model.Status == gb.GRB.OPTIMAL:
        output.details(f"Budget: {budget.X}")

        column_widths = {
            candidate: max(len(str(payment[voter][candidate].X)) for voter in payment)
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
                    str(pay.X).rjust(column_widths[candidate])
                    for candidate, pay in payment[voter].items()
                )
            )

        return True
    elif model.Status == gb.GRB.INFEASIBLE:
        output.details("No feasible budget and payment function")
        return False
    else:
        raise RuntimeError(f"Gurobi returned an unexpected status code: {model.Status}")


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

    model = gb.Model()

    set_of_voter = model.addVars(range(len(profile)), vtype=gb.GRB.BINARY)
    set_of_candidates = model.addVars(range(profile.num_cand), vtype=gb.GRB.BINARY)

    model.addConstr(
        gb.quicksum(set_of_candidates) * len(profile) <= gb.quicksum(set_of_voter) * committeesize
    )
    model.addConstr(gb.quicksum(set_of_voter) >= 1)
    for i, voter in enumerate(profile):
        approved = [
            (c in voter.approved) * set_of_candidates[i] for i, c in enumerate(profile.candidates)
        ]
        model.addConstr(
            (set_of_voter[i] == 1)
            >> (gb.quicksum(approved) >= len(voter.approved & committee) + 1)
        )

    _set_gurobi_model_parameters(model)
    model.optimize()

    if model.Status == gb.GRB.OPTIMAL:
        return False
    elif model.Status == gb.GRB.INFEASIBLE:
        return True
    else:
        raise RuntimeError(f"Gurobi returned an unexpected status code: {model.Status}")
