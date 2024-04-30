"""
Example 2.6 (PAV, seq-PAV, revseq-PAV).

From "Multi-Winner Voting with Approval Preferences"
by Martin Lackner and Piotr Skowron
http://dx.doi.org/10.1007/978-3-031-09016-5
"""

from abcvoting import abcrules
from abcvoting.preferences import Profile
from abcvoting import misc
from abcvoting.output import output, DETAILS

output.set_verbosity(DETAILS)

print(misc.header("Example 6", "*"))

# Approval profile
num_cand = 4
a, b, c, d = range(4)  # a = 0, b = 1, c = 2, ...
cand_names = "abcd"


profile = Profile(num_cand, cand_names=cand_names)
profile.add_voters([{a, b}, {a, b, c}, {a, b, d}, {a, c, d}, {a, c, d}, {b}, {c}, {d}])

print(misc.header("Input:"))
print(profile.str_compact())

committees_av = abcrules.compute_av(profile, 1)

committees_revseqpav = abcrules.compute_revseqpav(profile, 1)
