"""
Example for reading and writing Preflib files.
"""

import os
from abcvoting import fileio
from abcvoting import abcrules
from abcvoting.misc import str_sets_of_candidates
from abcvoting.preferences import Profile


currdir = os.path.dirname(os.path.abspath(__file__))


# Write a profile to toi file
profile = Profile(5, "ABCDE")
profile.add_voters([{0, 1}, {1, 3, 4}, {2}, {3}, {3}])
fileio.write_profile_to_preflib_cat_file(
    os.path.join(currdir, "preflib-files/new_example.cat"), profile
)


# Read a directory of Preflib files (using parameter `top_ranks`)
profiles = fileio.read_preflib_files_from_dir(os.path.join(currdir, "preflib-files"), top_ranks=3)
# Compute PAV for each profile
committeesize = 2
for profile in profiles.values():
    print(
        f"Computing a committee of size {committeesize} "
        "with the Proportional Approval Voting (PAV) rule"
    )
    print(f"given a {profile}")
    print("Output:")
    committees = abcrules.compute_pav(profile, committeesize)
    print(str_sets_of_candidates(committees))
    print("****************************************")


# Read a Preflib file (using parameter `setsize`)
profile = fileio.read_preflib_file(os.path.join(currdir, "preflib-files/example.toi"), setsize=1)
# Compute Phragmen's sequential rule for this profile
print("Computing a committee of size", committeesize, end=" ")
print("with Phragmen's sequential rule")
print("given a", profile)
print("Output:")
committees = abcrules.compute_seqphragmen(profile, committeesize)
print(str_sets_of_candidates(committees))
print("****************************************")
