"""
dosy_opt.py
-----------

Download from: https://git.io/JUHOY

Script that optimises parameters for a diffusion experiment. Currently only
works with oneshot DOSY (Pelta et al., Magn. Reson. Chem. 2002, 40 (13),
S147-S152, DOI: 10.1002/mrc.1107).

This is meant to be called from the TopSpin command line on a 2D diffusion
experiment.

Note that this script does not tweak the gradient lengths ("little delta"), so
these should be set to a sensible value (e.g. 1 ms) before running this script.

The algorithm is as follows:

 1. Create 1D versions of the diffusion experiment, one with the minimum
    gradient (10%, the "reference spectrum", expno 99998) and one with the
    maximum gradient (80%, "optimisation spectrum", expno 99999).
 2. Acquires both spectra.
 3. Check whether the opt. spectrum has at least 75% signal attenuation
    relative to the ref. spectrum. If not, increases the diffusion delay
    ("big Delta") and repeats steps 1 and 2.
 4. If the attenuation is sufficient, it then runs a POISE optimisation on the
    opt. spectrum to find the gradient strength at which 75% signal attenuation
    is achieved.
 5. Once this gradient strength has been found, returns to the 2D experiment
    and runs the `dosy` Bruker AU programme using the new parameter.

SPDX-License-Identifier: GPL-3.0-or-later
"""

# Dictionary of DOSY pulse programmes, to be entered in the form
#    "2d_pulprog": ["1d_pulprog", "GRAD_AMPLITUDE_PARAM", "DIFF_DELAY_PARAM"]
# In more detail:
#  - 2d_pulprog is the name of the 2D DOSY pulse sequence.
#  - 1d_pulprog is the name of the corresponding 1D DOSY pulse sequence, which
#     should be just a single increment of the 2D sequence, but with Difframp
#     removed. See the doneshot_nd_jy pulse programmes for an example.
#  - GRAD_AMPLITUDE_PARAM is the parameter name in the 2D DOSY pulse sequence
#     that is multiplied by Difframp. In the 1D DOSY pulse sequence it should
#     not be multiplied by Difframp, so simply corresponds to the gradient
#     strength. Note that you need a space between GPZ and the number.
#  - DIFF_DELAY_PARAM is the parameter name in both 1D and 2D sequences that
#     corresponds to the diffusion delay. Again, a space between D and the
#     number is required.
# Other DOSY variants can be entered here to "register" them and make them
# available for use with this script.
pulprog_dict = {
    "doneshot_2d_jy": ["doneshot_1d_jy", "GPZ 1", "D 20"],
}

# Look up the 1D pulse programme and associated parameters based on the current
# 2D pulse programme.
pp2d = GETPAR("PULPROG")
if pp2d in pulprog_dict:
    pp1d, gpzparam, dparam = pulprog_dict[pp2d]
else:
    MSG("dosy_opt: unsupported pulse programme. New pulse programmes can be"
        " added in the dosy_opt.py script.")
    EXIT()

# Get the expno of the 2D dataset, and store the parameter set. This is
# important because we want the optimisation to inherit most parameters, e.g.
# D1, SW, etc. from the parent experiment (which has presumably been set up by
# the user).
original_2d_expno = int(CURDATA()[1])
original_2d_dataset = CURDATA()
XCMD("wpar dosytemp all")

# Set up the reference experiment.
reference_expno = 99998
reference_dataset = list(original_2d_dataset)
reference_dataset[1] = str(reference_expno)
NEWDATASET(reference_dataset, None, "dosytemp")
RE(reference_dataset)
PUTPAR("PULPROG", pp1d)
PUTPAR("PARMODE", "1D")
PUTPAR("PPARMOD", "1D")
PUTPAR(gpzparam, "10")
XCMD("sendgui browse_update_tree")
# Acquire reference dataset.
XCMD("poise_1d", wait=WAIT_TILL_DONE)

# Set up optimisation expno.
optimisation_expno = 99999
optimisation_dataset = list(original_2d_dataset)   # make a copy
optimisation_dataset[1] = str(optimisation_expno)
NEWDATASET(optimisation_dataset, None, "dosytemp")
RE(optimisation_dataset)
PUTPAR("PULPROG", pp1d)
PUTPAR("PARMODE", "1D")
PUTPAR("PPARMOD", "1D")
PUTPAR(gpzparam, "80")
XCMD("sendgui browse_update_tree")

# Optimise the diffusion delay first.
while True:
    # Here we use the `--maxfev 1` trick to evaluate a cost function at 80%
    # gradient. The cost function is stored as the `TI` parameter after the
    # experiment has been recorded.
    RE(optimisation_dataset)
    XCMD("poise dosy1d_aux -a nm --maxfev 1 -q", wait=WAIT_TILL_DONE)
    cf = float(GETPAR("TI"))
    # The dosy1d_aux cost function is (opt. intensity/ref. intensity) - 0.25.
    # If the opt. spectrum has been attenuated too little, then this value will
    # be positive.
    if cf > 0:
        # Increase D20, i.e. big Delta, by 100 ms
        current_d20 = float(GETPAR(dparam))
        new_d20 = current_d20 + 0.1
        PUTPAR(dparam, str(new_d20))
        # Set it in the reference spectrum too
        RE(reference_dataset)
        PUTPAR(dparam, str(new_d20))
        # Re-acquire the reference spectrum.
        XCMD("xau poise_1d", wait=WAIT_TILL_DONE)
    # If the cost function is negative, then that means it's sufficiently
    # attenuated, and we can go on to the actual optimisation.
    else:
        break

# At this point, we know that 80% gradient strength provides at least 75%
# attenuation. So we can run an optimisation to find the actual value that does
# provide 75% attenuation (which is somewhere between 10% and 80%).
RE(optimisation_dataset)
XCMD("poise dosy1d -a bobyqa -q", wait=WAIT_TILL_DONE)
# Save the final parameters.
best_d20 = GETPAR(dparam)
best_gpz = GETPAR(gpzparam)

# Jump back to original 2D expt. Set dparam, but not gpzparam as that should
# always be 100% (the actual gradient amplitude is controlled by Difframp,
# which will be generated by the `dosy` AU programme).
RE(original_2d_dataset)
PUTPAR(dparam, best_d20)
PUTPAR(gpzparam, "100")
# Generate Difframp, etc. and then run the AU programme.
XCMD("xau dosy 10 {} 16 l y".format(best_gpz))
