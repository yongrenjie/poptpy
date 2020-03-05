import os

p_tshome = "/opt/topspin4.0.7/exp/stan/nmr"
p_pypopt = os.path.join(p_tshome, "py/user/pypopt")
p_costfunctions = os.path.join(p_pypopt, "cost_functions")
p_python3 = "/usr/local/bin/python3"


def main():
    """
    Main routine for creation of a new cost function.
    """
    # Instructions:
    # 1. Define cf_name (this will be the name you choose for the cost function
    #    when creating a new routine in TopSpin).
    # 2. Edit f() to return the value you want it to.
    # 3. Run this script, either in TopSpin or using the external Python 3.

    # STEP 1: Change this to whatever name you want.
    cf_name = "total_int"

    # STEP 2: Edit this function to suit your purposes.
    def f():
        # f() must return the value of the cost function as a float.
        # Some builtin methods are available:
        #  - getpar(param)       takes a string and returns the value of the
        #                        parameter as a float.
        #  - get_real_spectrum() returns the real spectrum as a numpy array
        #                        of size SI. You can pass two arguments, "left"
        #                        and "right", to specify a particular region
        #                        of the spectrum of interest.
        #           For example:
        #           - get_real_spectrum() OR get_real_spectrum(None, None)
        #             return the entire spectrum.
        #           - get_real_spectrum(6.21, None)
        #             returns the part of the spectrum with shift <= 6.21
        #             (i.e. the spectrum is left-bounded by 6.21 ppm).
        #           - get_real_spectrum(None, 6.21)
        #             returns the part of the spectrum with shift >= 6.21.
        #           - get_real_spectrum(6.21, 4)
        #             returns the part of the spectrum between 6.21 and 4 ppm.
        #  - get_imag_spectrum() does the same for the imaginary spectrum.
        #  - get_fid()           returns the complex-valued FID as a numpy
        #                        array of size TD/2.

        # In this short example, we simply sum the intensities at each point
        # of the real spectrum. This gives us a quick and easy measure of the
        # total signal intensity.
        return np.sum(get_real_spectrum())

    # STEP 3
    # Run the script!

    # The code below doesn't need to be modified.
    cf = Cost_Function(cf_name, f)
    if not os.path.isdir(p_costfunctions):
        os.makedirs(p_costfunctions)
    p_cf_file = os.path.join(p_costfunctions, cf_name)
    with open(p_cf_file, "wb") as file:
        dill.dump(cf, file)
    print("Cost function {} successfully"
          "saved to {}.".format(cf_name, p_costfunctions))


class Cost_Function:
    def __init__(self, name, function):
        self.name = name
        self.function = function


if __name__ == "__main__":
    # Check if this is being called from TopSpin
    try:
        SHOW_STATUS("pypopt_makecf.py: Running script with Python 3...")
        from subprocess import *
        import sys
        py3run = Popen([p_python3, sys.argv[0]], stdout=PIPE)
        out, _ = py3run.communicate()
        MSG(out)
        EXIT()
    except NameError:  # Python 3
        import dill
        main()
