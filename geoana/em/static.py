from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import numpy as np
import warnings
import properties
from scipy.special import ellipk, ellipe
from scipy.constants import mu_0

from .base import BaseEM, BaseDipole, BaseMagneticDipole, BaseElectricDipole
from .. import spatial

__all__ = ["MagneticDipoleWholeSpace", "CircularLoopWholeSpace"]


class MagneticDipoleWholeSpace(BaseMagneticDipole, BaseEM):
    """
    Static magnetic dipole in a wholespace.
    """

    def vector_potential(self, xyz, coordinates="cartesian"):
        """Vector potential of a static magnetic dipole. See Griffiths, 1999
        equation 5.83

        .. math::

            \\vec{A}(\\vec{r}) = \\frac{\mu_0}{4\pi}
            \\frac{\\vec{m}\\times\\vec{r}}{r^3}

        **Required**

        :param numpy.array xyz: Location at which we calculate the vector
                                potential

        **Optional**

        :param str coordinates: coordinate system that the xyz is provided
                                in and that the solution will be returned
                                in (cartesian or cylindrical).
                                Default: `"cartesian"`

        **Returns**

        :rtype: numpy.array
        :return: The magnetic vector potential at each observation location

        """
        supported_coordinates = ["cartesian", "cylindrical"]
        assert coordinates.lower() in supported_coordinates, (
            "coordinates must be in {}, the coordinate system "
            "you provided, {}, is not yet supported".format(
                supported_coordinates, coordinates
            )
        )

        n_obs = xyz.shape[0]

        # orientation of the dipole
        if coordinates.lower() == "cylindrical":
            xyz = spatial.cylindrical_2_cartesian(xyz)

        dxyz = self.vector_distance(xyz)
        r = spatial.repeat_scalar(self.distance(xyz))
        m = self.moment * np.atleast_2d(self.orientation).repeat(n_obs, axis=0)

        m_cross_r = np.cross(m, dxyz)
        a = (self.mu / (4 * np.pi)) * m_cross_r / (r**3)

        if coordinates.lower() == "cylindrical":
            a = spatial.cartesian_2_cylindrical(xyz, a)

        return a


    def magnetic_flux_density(self, xyz, coordinates="cartesian"):
        """Magnetic flux (:math:`\\vec{b}`) of a static magnetic dipole

        **Required**

        :param numpy.array xyz: Location of the receivers(s)

        **Optional**

        :param str coordinates: coordinate system that the xyz is provided
                                in and that the solution will be returned
                                in (cartesian or cylindrical).
                                Default: `"cartesian"`

        **Returns**

        :rtype: numpy.array
        :return: The magnetic flux at each observation location
        """

        supported_coordinates = ["cartesian", "cylindrical"]
        assert coordinates.lower() in supported_coordinates, (
            "coordinates must be in {}, the coordinate system "
            "you provided, {}, is not yet supported".format(
                supported_coordinates, coordinates
            )
        )

        n_obs = xyz.shape[0]

        if coordinates.lower() == "cylindrical":
            xyz = spatial.cylindrical_2_cartesian(xyz)

        r = self.vector_distance(xyz)
        dxyz = spatial.repeat_scalar(self.distance(xyz))
        m_vec = (
            self.moment * np.atleast_2d(self.orientation).repeat(n_obs, axis=0)
        )

        m_dot_r = (m_vec * r).sum(axis=1)

        # Repeat the scalars
        m_dot_r = np.atleast_2d(m_dot_r).T.repeat(3, axis=1)
        # dxyz = np.atleast_2d(dxyz).T.repeat(3, axis=1)

        b = (self.mu / (4 * np.pi)) * (
            (3.0 * r * m_dot_r / (dxyz ** 5)) -
            m_vec / (dxyz ** 3)
        )

        if coordinates.lower() == "cylindrical":
            b = spatial.cartesian_2_cylindrical(xyz, b)

        return b

    def magnetic_field(self, xyz, coordinates="cartesian"):
        """Magnetic field (:math:`\\vec{h}`) of a static magnetic dipole

        **Required**

        :param numpy.array xyz: Location of the receivers(s)

        **Optional**

        :param str coordinates: coordinate system that the xyz is provided
                                in and that the solution will be returned
                                in (cartesian or cylindrical).
                                Default: `"cartesian"`

        **Returns**

        :rtype: numpy.array
        :return: The magnetic field at each observation location

        """
        return self.magnetic_flux(xyz, coordinates=coordinates) / self.mu


class CircularLoopWholeSpace(BaseDipole, BaseEM):

    """
    Static magnetic field from a circular loop in a wholespace.
    """

    current = properties.Float(
        "Electric current through the loop (A)", default=1.
    )

    radius = properties.Float(
        "radius of the loop (m)", default=1., min=0.
    )

    def vector_potential(self, xyz, coordinates="cartesian"):
        """Vector potential due to the a steady-state current through a
        circular loop. Following Jackson, 2004 (equation 5.37), in spherical
        coordinates (radial :math:`r`, azimuthal:`theta`, polar :math:`\phi`)
        the vector potential is given by:

        .. math::

            A_\\theta(r, \phi, z) = \\frac{\mu_0}{4\pi}
            \\frac{4IR}{\sqrt{R^2 + r^2 + 2Rr\sin\phi}}
            \left[ \\frac{(2-k^2)K(k) - 2E(k)}{k^2} \\right]

        where

        .. math::

            k^2 = \\frac{4 R r \sin\phi}{R^2 + r^2 + 2Rr\sin\phi}

        and

        - :math:`r` is the distance to a test point
        - :math:`I` is the current through the loop
        - :math:`R` is the radius of the loop
        - :math:`\phi` is the angle between the test point and the normal of the loop
        - :math:`E(k)` and :math:`K(k)` are the complete elliptic integrals


        **Required**

        :param numpy.array xyz: Location where we calculate the vector
                                potential

        **Optional**

        :param str coordinates: coordinate system that the xyz is provided
                                in and that the solution will be returned
                                in (cartesian or cylindrical).
                                Default: `"cartesian"`

        **Returns**

        :rtype: numpy.array
        :return: The magnetic vector potential at each observation location

        """
        supported_coordinates = ["cartesian", "cylindrical"]
        assert coordinates.lower() in supported_coordinates, (
            "coordinates must be in {}, the coordinate system "
            "you provided, {}, is not yet supported".format(
                supported_coordinates, coordinates
            )
        )

        # convert coordinates if not cartesian
        if coordinates.lower() == "cylindrical":
            xyz = spatial.cylindrical_2_cartesian(xyz)

        n_obs = xyz.shape[0]
        dxyz = self.vector_distance(xyz)
        r = self.distance(xyz)

        # # calculate sin theta
        # here we use the definition of the dot product:
        #    a dot b = |a| |b| cos(\theta)
        # and the identity cos(\theta)**2 + sin(\theta)**2 = 1
        magnitudes = (spatial.vector_magnitude(self.orientation) * r)
        cos_phi = self.dot_orientation(dxyz) / magnitudes
        sin_phi = np.sqrt(1 - cos_phi**2)

        k2 = (
            (4*self.radius*r*sin_phi) /
            (self.radius**2 + r**2 + 2*self.radius*r*sin_phi)
        )
        k = np.sqrt(k2)

        E = ellipe(k)
        K = ellipk(k)

        # % 1/r singular at r = 0 and 1/k singular at k = 0
        ind = (r > 0) & (k2 > 0) & (k < 1)
        Atheta = np.zeros(n_obs)

        Atheta[ind] = (
            mu_0 / (4*np.pi) *
            (
                (4*self.current*self.radius) /
                (
                    self.radius**2 + r[ind]**2 +
                    2*self.radius*r[ind]*sin_phi[ind]
                )
            ) *
            ((2-k2[ind])*K[ind]-2*E[ind]) / k2[ind]
        )

        # assume that the z-axis aligns with the polar axis
        A = np.zeros_like(xyz)
        A[ind, 0] = Atheta[ind] * (-xyz[ind, 1] / r[ind])
        A[ind, 1] = Atheta[ind] * (xyz[ind, 0] / r[ind])

        # rotate the points to aligned with the normal to the source
        A = spatial.rotate_points_from_normals(
            A, np.r_[0., 0., 1.], self.orientation
        )

        if coordinates.lower() == "cylindrical":
            A = spatial.cartesian_2_cylindrical(xyz, A)

        return A
