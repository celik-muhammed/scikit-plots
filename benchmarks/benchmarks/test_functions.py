import time

import numpy as np
from numpy import abs, cos, exp, pi, sin, sqrt
from scipy.optimize import rosen


class SimpleQuadratic:
    def fun(self, x):
        return np.dot(x, x)

    def der(self, x):
        return 2.0 * x

    def hess(self, x):
        return 2.0 * np.eye(x.size)


class AsymmetricQuadratic:
    def fun(self, x):
        return np.dot(x, x) + x[0]

    def der(self, x):
        d = 2.0 * x
        d[0] += 1
        return d

    def hess(self, x):
        return 2.0 * np.eye(x.size)


class SlowRosen:
    def fun(self, x):
        time.sleep(40e-6)
        return rosen(x)


class LJ:
    """
    The Lennard Jones potential

    a mathematically simple model that approximates the interaction between a
    pair of neutral atoms or molecules.
    https://en.wikipedia.org/wiki/Lennard-Jones_potential

    E = sum_ij V(r_ij)

    where r_ij is the cartesian distance between atom i and atom j, and the
    pair potential has the form

    V(r) = 4 * eps * ( (sigma / r)**12 - (sigma / r)**6

    Notes
    -----
    the double loop over many atoms makes this *very* slow in Python.  If it
    were in a compiled language it would be much faster.

    """

    def __init__(self, eps=1.0, sig=1.0):
        self.sig = sig
        self.eps = eps

    def vij(self, r):
        return 4.0 * self.eps * ((self.sig / r) ** 12 - (self.sig / r) ** 6)

    def dvij(self, r):
        p7 = 6.0 / self.sig * (self.sig / r) ** 7
        p13 = -12.0 / self.sig * (self.sig / r) ** 13
        return 4.0 * self.eps * (p7 + p13)

    def fun(self, coords):
        natoms = coords.size // 3
        coords = np.reshape(coords, [natoms, 3])
        energy = 0.0
        for i in range(natoms):
            for j in range(i + 1, natoms):
                dr = coords[j, :] - coords[i, :]
                r = np.linalg.norm(dr)
                energy += self.vij(r)
        return energy

    def der(self, coords):
        natoms = coords.size // 3
        coords = np.reshape(coords, [natoms, 3])
        energy = 0.0
        grad = np.zeros([natoms, 3])
        for i in range(natoms):
            for j in range(i + 1, natoms):
                dr = coords[j, :] - coords[i, :]
                r = np.linalg.norm(dr)
                energy += self.vij(r)
                g = self.dvij(r)
                grad[i, :] += -g * dr / r
                grad[j, :] += g * dr / r
        grad = grad.reshape([natoms * 3])
        return grad

    def get_random_configuration(self):
        rnd = np.random.uniform(-1, 1, [3 * self.natoms])
        return rnd * float(self.natoms) ** (1.0 / 3)


class LJ38(LJ):
    natoms = 38
    target_E = -173.928427


class LJ30(LJ):
    natoms = 30
    target_E = -128.286571


class LJ20(LJ):
    natoms = 20
    target_E = -77.177043


class LJ13(LJ):
    natoms = 13
    target_E = -44.326801


class Booth:
    target_E = 0.0
    solution = np.array([1.0, 3.0])
    xmin = np.array([-10.0, -10.0])
    xmax = np.array([10.0, 10.0])

    def fun(self, coords):
        x, y = coords
        return (x + 2.0 * y - 7.0) ** 2 + (2.0 * x + y - 5.0) ** 2

    def der(self, coords):
        x, y = coords
        dfdx = 2.0 * (x + 2.0 * y - 7.0) + 4.0 * (2.0 * x + y - 5.0)
        dfdy = 4.0 * (x + 2.0 * y - 7.0) + 2.0 * (2.0 * x + y - 5.0)
        return np.array([dfdx, dfdy])


class Beale:
    target_E = 0.0
    solution = np.array([3.0, 0.5])
    xmin = np.array([-4.5, -4.5])
    xmax = np.array([4.5, 4.5])

    def fun(self, coords):
        x, y = coords
        p1 = (1.5 - x + x * y) ** 2
        p2 = (2.25 - x + x * y**2) ** 2
        p3 = (2.625 - x + x * y**3) ** 2
        return p1 + p2 + p3

    def der(self, coords):
        x, y = coords
        dfdx = (
            2.0 * (1.5 - x + x * y) * (-1.0 + y)
            + 2.0 * (2.25 - x + x * y**2) * (-1.0 + y**2)
            + 2.0 * (2.625 - x + x * y**3) * (-1.0 + y**3)
        )
        dfdy = (
            2.0 * (1.5 - x + x * y) * (x)
            + 2.0 * (2.25 - x + x * y**2) * (2.0 * y * x)
            + 2.0 * (2.625 - x + x * y**3) * (3.0 * x * y**2)
        )
        return np.array([dfdx, dfdy])


"""
Global Test functions for minimizers.

HolderTable, Ackey and Levi have many competing local minima and are suited
for global minimizers such as basinhopping or differential_evolution.
(https://en.wikipedia.org/wiki/Test_functions_for_optimization)

See also https://mpra.ub.uni-muenchen.de/2718/1/MPRA_paper_2718.pdf

"""


class HolderTable:
    target_E = -19.2085
    solution = [8.05502, 9.66459]
    xmin = np.array([-10, -10])
    xmax = np.array([10, 10])
    stepsize = 2.0
    temperature = 2.0

    def fun(self, x):
        return -abs(
            sin(x[0]) * cos(x[1]) * exp(abs(1.0 - sqrt(x[0] ** 2 + x[1] ** 2) / pi))
        )

    def dabs(self, x):
        """Derivative of absolute value"""
        if x < 0:
            return -1.0
        if x > 0:
            return 1.0
        return 0.0


# commented out at the because it causes FloatingPointError in
# basinhopping
#     def der(self, x):
#         R = sqrt(x[0]**2 + x[1]**2)
#         g = 1. - R / pi
#         f = sin(x[0]) * cos(x[1]) * exp(abs(g))
#         E = -abs(f)
#
#         dRdx = x[0] / R
#         dgdx = - dRdx / pi
#         dfdx = cos(x[0]) * cos(x[1]) * exp(abs(g)) + f * self.dabs(g) * dgdx
#         dEdx = - self.dabs(f) * dfdx
#
#         dRdy = x[1] / R
#         dgdy = - dRdy / pi
#         dfdy = -sin(x[0]) * sin(x[1]) * exp(abs(g)) + f * self.dabs(g) * dgdy
#         dEdy = - self.dabs(f) * dfdy
#         return np.array([dEdx, dEdy])


class Ackley:
    # note: this function is not smooth at the origin.  the gradient will never
    # converge in the minimizer
    target_E = 0.0
    solution = [0.0, 0.0]
    xmin = np.array([-5, -5])
    xmax = np.array([5, 5])

    def fun(self, x):
        E = (
            -20.0 * exp(-0.2 * sqrt(0.5 * (x[0] ** 2 + x[1] ** 2)))
            + 20.0
            + np.e
            - exp(0.5 * (cos(2.0 * pi * x[0]) + cos(2.0 * pi * x[1])))
        )
        return E

    def der(self, x):
        R = sqrt(x[0] ** 2 + x[1] ** 2)
        term1 = -20.0 * exp(-0.2 * R)
        term2 = -exp(0.5 * (cos(2.0 * pi * x[0]) + cos(2.0 * pi * x[1])))

        deriv1 = term1 * (-0.2 * 0.5 / R)

        dfdx = 2.0 * deriv1 * x[0] - term2 * pi * sin(2.0 * pi * x[0])
        dfdy = 2.0 * deriv1 * x[1] - term2 * pi * sin(2.0 * pi * x[1])

        return np.array([dfdx, dfdy])


class Levi:
    target_E = 0.0
    solution = [1.0, 1.0]
    xmin = np.array([-10, -10])
    xmax = np.array([10, 10])

    def fun(self, x):
        E = (
            sin(3.0 * pi * x[0]) ** 2
            + (x[0] - 1.0) ** 2 * (1.0 + sin(3 * pi * x[1]) ** 2)
            + (x[1] - 1.0) ** 2 * (1.0 + sin(2 * pi * x[1]) ** 2)
        )
        return E

    def der(self, x):
        dfdx = 2.0 * 3.0 * pi * cos(3.0 * pi * x[0]) * sin(3.0 * pi * x[0]) + 2.0 * (
            x[0] - 1.0
        ) * (1.0 + sin(3 * pi * x[1]) ** 2)

        dfdy = (
            (x[0] - 1.0) ** 2
            * 2.0
            * 3.0
            * pi
            * cos(3.0 * pi * x[1])
            * sin(3.0 * pi * x[1])
            + 2.0 * (x[1] - 1.0) * (1.0 + sin(2 * pi * x[1]) ** 2)
            + (x[1] - 1.0) ** 2
            * 2.0
            * 2.0
            * pi
            * cos(2.0 * pi * x[1])
            * sin(2.0 * pi * x[1])
        )

        return np.array([dfdx, dfdy])


class EggHolder:
    target_E = -959.6407
    solution = [512, 404.2319]
    xmin = np.array([-512.0, -512])
    xmax = np.array([512.0, 512])

    def fun(self, x):
        a = -(x[1] + 47) * np.sin(np.sqrt(abs(x[1] + x[0] / 2.0 + 47)))
        b = -x[0] * np.sin(np.sqrt(abs(x[0] - (x[1] + 47))))
        return a + b


class CrossInTray:
    target_E = -2.06261
    solution = [1.34941, -1.34941]
    xmin = np.array([-10.0, -10])
    xmax = np.array([10.0, 10])

    def fun(self, x):
        arg = abs(100 - sqrt(x[0] ** 2 + x[1] ** 2) / pi)
        val = np.power(abs(sin(x[0]) * sin(x[1]) * exp(arg)) + 1.0, 0.1)
        return -0.0001 * val


class Schaffer2:
    target_E = 0
    solution = [0.0, 0.0]
    xmin = np.array([-100.0, -100])
    xmax = np.array([100.0, 100])

    def fun(self, x):
        num = np.power(np.sin(x[0] ** 2 - x[1] ** 2), 2) - 0.5
        den = np.power(1 + 0.001 * (x[0] ** 2 + x[1] ** 2), 2)
        return 0.5 + num / den


class Schaffer4:
    target_E = 0.292579
    solution = [0, 1.253131828927371]
    xmin = np.array([-100.0, -100])
    xmax = np.array([100.0, 100])

    def fun(self, x):
        num = cos(sin(abs(x[0] ** 2 - x[1] ** 2))) ** 2 - 0.5
        den = (1 + 0.001 * (x[0] ** 2 + x[1] ** 2)) ** 2
        return 0.5 + num / den
