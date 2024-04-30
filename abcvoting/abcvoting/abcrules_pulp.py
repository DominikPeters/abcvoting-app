"""ABC rules implemented as integer linear programs (ILPs) with pulp."""

import functools
import itertools
import math
from abcvoting.misc import sorted_committees
from abcvoting import scores
from abcvoting import misc
from abcvoting.output import output
import pulp
import js
import json

ACCURACY = 1e-8  # 1e-9 causes problems (some unit tests fail)
CMP_ACCURACY = 10 * ACCURACY  # when comparing float numbers obtained from a MIP

def mySolve(model):
    return json.loads(js.runHighs(model.writeLP()))


def _optimize_rule_pulp(
    set_opt_model_func,
    profile,
    committeesize,
    resolute,
    max_num_of_committees,
    name="None",
    committeescorefct=None,
):
    """Compute rules, which are given in the form of an optimization problem, using pulp.

    Parameters
    ----------
    set_opt_model_func : callable
        sets constraints and objective and adds additional variables, see examples below for its
        signature
    profile : abcvoting.preferences.Profile
        approval sets of voters
    committeesize : int
        number of chosen alternatives
    resolute : bool
    max_num_of_committees : int
        maximum number of committees this method returns, value can be None
    name : str
        name of the model, used for error messages
    committeescorefct : callable
        a function used to compute the score of a committee

    Returns
    -------
    committees : list of set
        a list of winning committees,
        each of them represented as set of integers from `0` to `num_cand` - 1

    maxscore : float
        best objective value returned by ILP

    """

    maxscore = None
    committees = []

    model = pulp.LpProblem(name, pulp.LpMinimize)

    # `in_committee` is a binary variable indicating whether `cand` is in the committee
    in_committee = {}
    for cand in profile.candidates:
        in_committee[cand] = pulp.LpVariable(f"in_committee_{cand}", cat=pulp.LpBinary)

    set_opt_model_func(model, in_committee)

    while True:
        solution = mySolve(model)
        status = solution["Status"]

        if status not in ["Optimal", "Infeasible"]:
            raise RuntimeError(
                f"Pulp returned an unexpected status code: {status}\n"
                f"Warning: solutions may be incomplete or not optimal (model {name})."
            )
        if status != "Optimal":
            if len(committees) == 0:
                # we are in the first round of searching for committees
                # and Pulp didn't find any
                raise RuntimeError(f"Pulp found no solution (model {name})")
            break

        value = {}
        for v in solution["Columns"]:
            value[v] = solution["Columns"][v]["Primal"]
        committee = {
            cand
            for cand in profile.candidates
            if value[in_committee[cand].name] >= 0.9
            # this should be >= 1 - ACCURACY, but apparently it is not necessarily the case that
            # integers are only ACCURACY apart from either 0 or 1
        }
        if len(committee) != committeesize:
            raise RuntimeError(
                "_optimize_rule_pulp() produced a committee with "
                f"fewer than `committeesize` members (model {name}).\n"
                + "\n".join(
                    f"({v.name}, {value[v.name]})" for v in model.variables() if "in_committee" in v.name
                )
            )

        if committeescorefct is None:
            objective_value = solution["ObjectiveValue"]  # numeric value from MIP
        else:
            objective_value = committeescorefct(profile, committee)  # exact value

        if maxscore is None:
            maxscore = objective_value
        elif (committeescorefct is not None and objective_value > maxscore) or (
            committeescorefct is None and objective_value > maxscore + CMP_ACCURACY
        ):
            raise RuntimeError(
                "Pulp found a solution better than a previous optimum. This "
                f"should not happen (previous optimal score: {maxscore}, "
                f"new optimal score: {value(model.objective)}, model {name})."
            )
        elif (committeescorefct is not None and objective_value < maxscore) or (
            committeescorefct is None and objective_value < maxscore - CMP_ACCURACY
        ):
            # no longer optimal
            break

        committees.append(committee)

        if resolute:
            break
        if max_num_of_committees is not None and len(committees) >= max_num_of_committees:
            return committees, maxscore

        # find a new committee that has not been found yet by excluding previously found committees
        model += pulp.lpSum(in_committee[cand] for cand in committee) <= committeesize - 1

    return committees, maxscore

def _pulp_thiele_methods(
    scorefct_id,
    profile,
    committeesize,
    resolute,
    max_num_of_committees,
):
    def set_opt_model_func(model, in_committee):
        # utility[(voter, x)] contains (intended binary) variables counting the number of approved
        # candidates in the selected committee by `voter`. This utility[(voter, x)] is true for
        # exactly the number of candidates in the committee approved by `voter` for all
        # x = 1...committeesize.
        #
        # If marginal_scorefct(x) > 0 for x >= 1, we assume that marginal_scorefct is monotonic
        # decreasing and therefore in combination with the objective function the following
        # interpretation is valid:
        # utility[(voter, x)] indicates whether `voter` approves at least x candidates in the
        # committee (this is the case for scorefct_id "pav", "slav" or "geom").

        utility = {}

        max_in_committee = {}
        for i, voter in enumerate(profile):
            # maximum number of approved candidates that this voter can have in a committee
            max_in_committee[voter] = min(len(voter.approved), committeesize)
            for x in range(1, max_in_committee[voter] + 1):
                utility[(voter, x)] = pulp.LpVariable(f"utility({i,x})", lowBound=0, upBound=1, cat='Integer')

        # constraint: the committee has the required size
        model += pulp.lpSum(in_committee) == committeesize

        # constraint: utilities are consistent with actual committee
        for voter in profile:
            model += pulp.lpSum(utility[voter, x] for x in range(1, max_in_committee[voter] + 1)) == pulp.lpSum(in_committee[cand] for cand in voter.approved)

        # objective: the Thiele score of the committee
        model += pulp.lpSum(
            float(marginal_scorefct(x)) * voter.weight * utility[(voter, x)]
            for voter in profile
            for x in range(1, max_in_committee[voter] + 1)
        )

        model.sense = pulp.LpMaximize

    marginal_scorefct = scores.get_marginal_scorefct(scorefct_id, committeesize)

    score_values = [marginal_scorefct(x) for x in range(1, committeesize + 1)]
    if not all(
        first > second or first == second == 0
        for first, second in zip(score_values, score_values[1:])
    ):
        raise ValueError("The score function must be monotonic decreasing")
    min_score_value = min(val for val in score_values if val > 0)
    if min_score_value < ACCURACY:
        output.warning(
            f"Thiele scoring function {scorefct_id} can take smaller values "
            f"(min={min_score_value}) than Gurobi accuracy ({ACCURACY})."
        )

    committees, _ = _optimize_rule_pulp(
        set_opt_model_func=set_opt_model_func,
        profile=profile,
        committeesize=committeesize,
        resolute=resolute,
        max_num_of_committees=max_num_of_committees,
        name=scorefct_id,
        committeescorefct=functools.partial(scores.thiele_score, scorefct_id),
    )
    return sorted_committees(committees)

def _pulp_lexcc(profile, committeesize, resolute, max_num_of_committees):
    def set_opt_model_func(model, in_committee):
        # utility[(voter, x)] contains (intended binary) variables counting the number of approved
        # candidates in the selected committee by `voter`. This utility[(voter, x)] is true for
        # exactly the number of candidates in the committee approved by `voter` for all
        # x = 1...committeesize.

        utility = {}
        iteration = len(satisfaction_constraints)
        scorefcts = [scores.get_marginal_scorefct(f"atleast{i + 1}") for i in range(iteration + 1)]

        max_in_committee = {}
        for i, voter in enumerate(profile):
            # maximum number of approved candidates that this voter can have in a committee
            max_in_committee[voter] = min(len(voter.approved), committeesize)
            for x in range(1, max_in_committee[voter] + 1):
                utility[(voter, x)] = pulp.LpVariable(f"utility({i, x})", lowBound=0, upBound=1, cat=pulp.LpBinary)

        # constraint: the committee has the required size
        model += pulp.lpSum(in_committee) == committeesize

        # constraint: utilities are consistent with actual committee
        for voter in profile:
            model += pulp.lpSum(utility[voter, x] for x in range(1, max_in_committee[voter] + 1)) == pulp.lpSum(in_committee[cand] for cand in voter.approved)

        # additional constraints from previous iterations
        for prev_iteration in range(iteration):
            model += pulp.lpSum(float(scorefcts[prev_iteration](x)) * voter.weight * utility[(voter, x)] for voter in profile for x in range(1, max_in_committee[voter] + 1)) >= satisfaction_constraints[prev_iteration] - ACCURACY

        # objective: the at-least-y score of the committee in iteration y
        model += pulp.lpSum(float(scorefcts[iteration](x)) * voter.weight * utility[(voter, x)] for voter in profile for x in range(1, max_in_committee[voter] + 1))

        model.sense = pulp.LpMaximize
        model.setObjective(model.objective)

    # proceed in `committeesize` many iterations to achieve lexicographic tie-breaking
    satisfaction_constraints = []
    for iteration in range(1, committeesize):
        # in iteration x maximize the number of voters that have at least x approved candidates
        # in the committee
        committees, _ = _optimize_rule_pulp(
            set_opt_model_func=set_opt_model_func,
            profile=profile,
            committeesize=committeesize,
            resolute=True,
            max_num_of_committees=None,
            name=f"lexcc-atleast{iteration}",
            committeescorefct=functools.partial(scores.thiele_score, f"atleast{iteration}"),
        )
        satisfaction_constraints.append(
            scores.thiele_score(f"atleast{iteration}", profile, committees[0])
        )
    iteration = committeesize
    committees, _ = _optimize_rule_pulp(
        set_opt_model_func=set_opt_model_func,
        profile=profile,
        committeesize=committeesize,
        resolute=resolute,
        max_num_of_committees=max_num_of_committees,
        name="lexcc-final",
        committeescorefct=functools.partial(scores.thiele_score, f"atleast{committeesize}"),
    )
    satisfaction_constraints.append(
        scores.thiele_score(f"atleast{iteration}", profile, committees[0])
    )
    detailed_info = {"opt_score_vector": satisfaction_constraints}
    return sorted_committees(committees), detailed_info

def _pulp_monroe(profile, committeesize, resolute, max_num_of_committees):
    def set_opt_model_func(model, in_committee):
        num_voters = len(profile)

        # optimization goal: variable "satisfaction"
        satisfaction = pulp.LpVariable("satisfaction", lowBound=0, upBound=num_voters, cat=pulp.LpInteger)

        model += (
            pulp.lpSum(in_committee[cand] for cand in profile.candidates) == committeesize
        )

        # a partition of voters into committeesize many sets
        partition = pulp.LpVariable.dicts(
            "partition", [(cand, i) for cand in profile.candidates for i in range(len(profile))], lowBound=0, cat=pulp.LpInteger
        )
        for i in range(len(profile)):
            # every voter has to be part of a voter partition set
            model += pulp.lpSum(partition[(cand, i)] for cand in profile.candidates) == 1
        for cand in profile.candidates:
            # every voter set in the partition has to contain
            # at least (num_voters // committeesize) candidates
            model += (
                pulp.lpSum(partition[(cand, j)] for j in range(len(profile)))
                >= (num_voters // committeesize - num_voters * (1 - in_committee[cand]))
            )
            # every voter set in the partition has to contain
            # at most ceil(num_voters/committeesize) candidates
            model += (
                pulp.lpSum(partition[(cand, j)] for j in range(len(profile)))
                <= (
                    num_voters // committeesize
                    + bool(num_voters % committeesize)
                    + num_voters * (1 - in_committee[cand])
                )
            )
            # if in_committee[i] = 0 then partition[(i,j) = 0
            model += (
                pulp.lpSum(partition[(cand, j)] for j in range(len(profile)))
                <= num_voters * in_committee[cand]
            )

        # constraint for objective variable "satisfaction"
        model += (
            pulp.lpSum(
                partition[(cand, j)] * (cand in profile[j].approved)
                for j in range(len(profile))
                for cand in profile.candidates
            )
            >= satisfaction
        )

        # optimization objective
        model += pulp.lpSum(satisfaction)
        model.sense = pulp.LpMaximize

    committees, _ = _optimize_rule_pulp(
        set_opt_model_func=set_opt_model_func,
        profile=profile,
        committeesize=committeesize,
        resolute=resolute,
        max_num_of_committees=max_num_of_committees,
        name="Monroe",
        committeescorefct=scores.monroescore,
    )
    return sorted_committees(committees)


def _pulp_minimaxphragmen(profile, committeesize, resolute, max_num_of_committees):
    """ILP for Phragmen's minimax rule (minimax-Phragmen), using Pulp.

    Minimizes the maximum load.

    Warning: does not include the lexicographic optimization as specified
    in Markus Brill, Rupert Freeman, Svante Janson and Martin Lackner.
    Phragmen's Voting Methods and Justified Representation.
    https://arxiv.org/abs/2102.12305
    Instead: minimizes the maximum load (without consideration of the
             second-, third-, ...-largest load
    """

    def set_opt_model_func(model, in_committee):
        load = {}
        for cand in profile.candidates:
            for i, voter in enumerate(profile):
                load[(voter, cand)] = pulp.LpVariable(f"load{i}-{cand}", lowBound=0, upBound=1, cat=pulp.LpContinuous)

        # constraint: the committee has the required size
        model += (
            pulp.lpSum(in_committee[cand] for cand in profile.candidates) == committeesize
        )

        for cand in profile.candidates:
            for voter in profile:
                if cand not in voter.approved:
                    load[(voter, cand)] = 0

        # a candidate's load is distributed among his approvers
        for cand in profile.candidates:
            model += (
                pulp.lpSum(
                    voter.weight * load[(voter, cand)]
                    for voter in profile
                    if cand in profile.candidates
                )
                >= in_committee[cand]
            )

        loadbound = pulp.LpVariable("loadbound", lowBound=0, upBound=committeesize, cat=pulp.LpContinuous)
        for voter in profile:
            model += (
                pulp.lpSum(load[(voter, cand)] for cand in voter.approved) <= loadbound
            )

        # maximizing the negative distance makes code more similar to the other methods here
        model += pulp.lpSum(-loadbound)
        model.sense = pulp.LpMaximize

    # check if a sufficient number of candidates is approved
    if len(profile.approved_candidates()) < committeesize:
        # An insufficient number of candidates is approved:
        # Committees consist of all approved candidates plus
        #  a correct number of unapproved candidates
        approved_candidates = profile.approved_candidates()
        remaining_candidates = [
            cand for cand in profile.candidates if cand not in approved_candidates
        ]
        num_missing_candidates = committeesize - len(approved_candidates)

        if resolute:
            return [approved_candidates | set(remaining_candidates[:num_missing_candidates])]

        return [
            approved_candidates | set(extra)
            for extra in itertools.combinations(remaining_candidates, num_missing_candidates)
        ]

    committees, _ = _optimize_rule_pulp(
        set_opt_model_func=set_opt_model_func,
        profile=profile,
        committeesize=committeesize,
        resolute=resolute,
        max_num_of_committees=max_num_of_committees,
        name="minimax-Phragmen",
    )
    return sorted_committees(committees)

def _pulp_leximaxphragmen(profile, committeesize, resolute, max_num_of_committees):
    
    def set_opt_model_func(model, in_committee):
        load = {}
        loadbound_constraint = {}
        for cand in profile.candidates:
            for i, voter in enumerate(profile):
                load[(voter, cand)] = pulp.LpVariable(f"load{i}-{cand}", 0, 1)

        for i, _ in enumerate(profile):
            for j, _ in enumerate(profile):
                loadbound_constraint[(i, j)] = pulp.LpVariable(f"loadbound_constraint({i, j})", 0, 1, cat='Binary')

        for i, _ in enumerate(profile):
            model += pulp.lpSum(loadbound_constraint[(i, j)] for j, _ in enumerate(profile)) == 1
            model += pulp.lpSum(loadbound_constraint[(j, i)] for j, _ in enumerate(profile)) == 1

        # constraint: the committee has the required size
        model += pulp.lpSum(in_committee[cand] for cand in profile.candidates) == committeesize

        for cand in profile.candidates:
            for voter in profile:
                if cand not in voter.approved:
                    load[(voter, cand)] = 0

        # a candidate's load is distributed among his approvers
        for cand in profile.candidates:
            model += pulp.lpSum(
                voter.weight * load[(voter, cand)]
                for voter in profile
                if cand in profile.candidates
            ) >= in_committee[cand]

        for i, _ in enumerate(loadbounds):
            for j, voter in enumerate(profile):
                model += pulp.lpSum(load[(voter, cand)] for cand in voter.approved) <= loadbounds[i] + (1 - loadbound_constraint[(i, j)]) * committeesize + ACCURACY
                    # constraint applies only if loadbound_constraint[(i, voter)] == 1

        newloadbound = pulp.LpVariable("new loadbound", 0, committeesize)
        for j, voter in enumerate(profile):
            model += pulp.lpSum(load[(voter, cand)] for cand in voter.approved) <= newloadbound + pulp.lpSum(loadbound_constraint[(i, j)] * committeesize for i in range(len(loadbounds)))

        # maximizing the negative distance makes code more similar to the other methods here
        model += pulp.lpSum(-newloadbound)
        model.sense = pulp.LpMaximize
    
    # check if a sufficient number of candidates is approved
    approved_candidates = profile.approved_candidates()
    if len(approved_candidates) < committeesize:
        # An insufficient number of candidates is approved:
        # Committees consist of all approved candidates plus
        #  a correct number of unapproved candidates
        remaining_candidates = [
            cand for cand in profile.candidates if cand not in approved_candidates
        ]
        num_missing_candidates = committeesize - len(approved_candidates)

        if resolute:
            return [approved_candidates | set(remaining_candidates[:num_missing_candidates])]

        return [
            approved_candidates | set(extra)
            for extra in itertools.combinations(remaining_candidates, num_missing_candidates)
        ]

    loadbounds = []
    for iteration in range(len(profile) - 1):
        # in interation we enforce a new loadbound.
        # first for all voters, then for all except one, then for all except two, etc.
        committees, neg_loadbound = _optimize_rule_pulp(
            set_opt_model_func=set_opt_model_func,
            profile=profile,
            committeesize=committeesize,
            resolute=True,
            max_num_of_committees=None,
            name=f"leximaxphragmen-iteration{iteration}",
        )
        if math.isclose(neg_loadbound, 0, rel_tol=CMP_ACCURACY, abs_tol=CMP_ACCURACY):
            # all other voters have a load of zero, no further loadbounds constraints required
            break
        loadbounds.append(-neg_loadbound)

    committees, _ = _optimize_rule_pulp(
        set_opt_model_func=set_opt_model_func,
        profile=profile,
        committeesize=committeesize,
        resolute=resolute,
        max_num_of_committees=max_num_of_committees,
        name="leximaxphragmen-final",
    )

    return sorted_committees(committees)

def _pulp_maximin_support_scorefct(profile, base_committee):
    """Uses an LP to compute the maximin support values obtained when adding any
    candidate to the committee.

    Based on the LP described in the proof of Theorem 4.2 of
    L. Sánchez-Fernández et al.
    The maximin support method: an extension of the D'Hondt method to approval-based multiwinner elections
    Mathematical Programming (2022)
    """

    scores = [0] * profile.num_cand
    remaining_candidates = [cand for cand in profile.candidates if cand not in base_committee]

    for added_cand in remaining_candidates:
        committee = set(base_committee) | {added_cand}

        model = pulp.LpProblem("MaximinSupport", pulp.LpMaximize)

        minimum = pulp.LpVariable("threshold", 0, None)  # named "s" in the paper

        f = {(vi, cand): pulp.LpVariable(f"fractional_assignment_{vi}_{cand}", 0, None)
             for vi in range(len(profile)) for cand in range(profile.num_cand)}

        for vi, voter in enumerate(profile):
            if voter.approved & committee:
                model += pulp.lpSum(f[vi, cand] for cand in voter.approved & committee) == voter.weight

        for cand in committee:
            model += pulp.lpSum(
                f[vi, cand] for vi, voter in enumerate(profile) if cand in voter.approved
            ) >= minimum

        model += minimum

        solution = mySolve(model)
        status = solution["Status"]

        if status == "Optimal":
            scores[added_cand] = solution["Columns"][minimum.name]["Primal"]
        else:
            raise RuntimeError(f"Pulp returned an unexpected status code: {status}")

    return scores

def _pulp_minimaxav(profile, committeesize, resolute, max_num_of_committees):
    def set_opt_model_func(model, in_committee):
        max_hamming_distance = pulp.LpVariable(
            "max_hamming_distance", lowBound=0, upBound=profile.num_cand, cat=pulp.LpInteger
        )

        model.addConstraint(
            pulp.lpSum(in_committee[cand] for cand in profile.candidates) == committeesize
        )

        for voter in profile:
            not_approved = [cand for cand in profile.candidates if cand not in voter.approved]
            # maximum Hamming distance is greater of equal than the Hamming distances
            # between individual voters and the committee
            model.addConstraint(
                max_hamming_distance
                >= pulp.lpSum(1 - in_committee[cand] for cand in voter.approved)
                + pulp.lpSum(in_committee[cand] for cand in not_approved)
            )

        # maximizing the negative distance makes code more similar to the other methods here
        model.setObjective(-max_hamming_distance)
        model.sense = pulp.LpMaximize

    committees, _ = _optimize_rule_pulp(
        set_opt_model_func=set_opt_model_func,
        profile=profile,
        committeesize=committeesize,
        resolute=resolute,
        max_num_of_committees=max_num_of_committees,
        name="Minimax_AV",
        committeescorefct=lambda profile, committee: -scores.minimaxav_score(profile, committee),
        # negative because _optimize_rule_mip maximizes while minimaxav minimizes
    )
    return sorted_committees(committees)


def _pulp_lexminimaxav(profile, committeesize, resolute, max_num_of_committees):
    def set_opt_model_func(model, in_committee):
        voteratmostdistances = {}

        for i, voter in enumerate(profile):
            for dist in range(profile.num_cand + 1):
                voteratmostdistances[(i, dist)] = pulp.LpVariable(
                    f"atmostdistance({i, dist})", cat=pulp.LpBinary
                )
                if dist >= len(voter.approved) + committeesize:
                    # distances are always <= len(voter.approved) + committeesize
                    voteratmostdistances[(i, dist)] = 1
                if dist < abs(len(voter.approved) - committeesize):
                    # distances are never < abs(len(voter.approved) - committeesize)
                    voteratmostdistances[(i, dist)] = 0

        # constraint: the committee has the required size
        model.addConstraint(pulp.lpSum(in_committee) == committeesize)

        # constraint: distances are consistent with actual committee
        for i, voter in enumerate(profile):
            not_approved = [cand for cand in profile.candidates if cand not in voter.approved]
            for dist in range(profile.num_cand + 1):
                if isinstance(voteratmostdistances[(i, dist)], int):
                    # trivially satisfied
                    continue
                model.addConstraint(
                        pulp.lpSum(1 - in_committee[cand] for cand in voter.approved)
                        + pulp.lpSum(in_committee[cand] for cand in not_approved)
                        <= dist + (1 - voteratmostdistances[(i, dist)]) * (profile.num_cand + 1)
                )

        # additional constraints from previous iterations
        for dist, num_voters_achieving_distance in hammingdistance_constraints.items():
            model.addConstraint(
                pulp.lpSum(voteratmostdistances[(i, dist)] for i, _ in enumerate(profile))
                >= num_voters_achieving_distance - ACCURACY
            )

        new_distance = min(hammingdistance_constraints.keys()) - 1
        # objective: maximize number of voters achieving at most distance `new_distance`
        model.setObjective(
            pulp.lpSum(voteratmostdistances[(i, new_distance)] for i, _ in enumerate(profile)),
        )
        model.sense = pulp.LpMaximize

    # compute minimaxav as baseline and then improve on it
    committees = _pulp_minimaxav(
        profile, committeesize, resolute=True, max_num_of_committees=None
    )
    maxdistance = scores.minimaxav_score(profile, committees[0])
    # all voters have at most this distance
    hammingdistance_constraints = {maxdistance: len(profile)}
    for distance in range(maxdistance - 1, -1, -1):
        # in iteration `distance` we maximize the number of voters that have at
        # most a Hamming distance of `distance` to the committee
        if distance == 0:
            # last iteration
            _resolute = resolute
            _max_num_of_committees = max_num_of_committees
        else:
            _resolute = True
            _max_num_of_committees = None
        committees, _ = _optimize_rule_pulp(
            set_opt_model_func=set_opt_model_func,
            profile=profile,
            committeesize=committeesize,
            resolute=_resolute,
            max_num_of_committees=_max_num_of_committees,
            name=f"lexminimaxav-atmostdistance{distance}",
            committeescorefct=functools.partial(
                scores.num_voters_with_upper_bounded_hamming_distance, distance
            ),
        )
        num_voters_achieving_distance = scores.num_voters_with_upper_bounded_hamming_distance(
            distance, profile, committees[0]
        )
        hammingdistance_constraints[distance] = num_voters_achieving_distance
    committees = sorted_committees(committees)
    detailed_info = {
        "hammingdistance_constraints": hammingdistance_constraints,
        "opt_distances": [misc.hamming(voter.approved, committees[0]) for voter in profile],
    }
    return committees, detailed_info