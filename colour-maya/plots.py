#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Autodesk Maya - Plotting
========================

Defines **Autodesk Maya** plotting objects.
"""

from __future__ import division, unicode_literals

import numpy as np

try:
    import maya.cmds as cmds
    import maya.OpenMaya as OpenMaya
except ImportError as error:
    pass

from colour.models import RGB_to_XYZ, XYZ_to_Lab
from colour.colorimetry import ILLUMINANTS

__author__ = 'Colour Developers'
__copyright__ = 'Copyright (C) 2013 - 2014 - Colour Developers'
__license__ = 'New BSD License - http://opensource.org/licenses/BSD-3-Clause'
__maintainer__ = 'Colour Developers'
__email__ = 'colour-science@googlegroups.com'
__status__ = 'Production'

__all__ = ['get_dag_path',
           'get_mpoint',
           'get_shapes',
           'set_attributes',
           'RGB_to_Lab',
           'RGB_identity_cube',
           'Lab_colourspace_cube',
           'Lab_coordinates_system_representation']


def get_dag_path(node):
    """
    Returns a dag path from given node.

    Parameters
    ----------
    node : str or unicode
        Node name.

    Returns
    -------
    MDagPath
        MDagPath.
    """

    selection_list = OpenMaya.MSelectionList()
    selection_list.add(node)
    dag_path = OpenMaya.MDagPath()
    selection_list.getDagPath(0, dag_path)
    return dag_path


def get_mpoint(point):
    """
    Converts a tuple to MPoint.

    Parameters
    ----------
    point : tuple
        Point.

    Returns
    -------
    MPoint
        MPoint.
    """

    return OpenMaya.MPoint(point[0], point[1], point[2])


def get_shapes(object, full_path=False, no_intermediate=True):
    """
    Returns shapes of given object.

    Parameters
    ----------
    object : str or unicode
        Current object.
    full_path : bool, optional
        Current full path state.
    no_intermediate : bool, optional
        Current no intermediate state.

    Returns
    -------
    list
        Objects shapes.
    """

    object_shapes = []
    shapes = cmds.listRelatives(object,
                                fullPath=full_path,
                                shapes=True,
                                noIntermediate=no_intermediate)
    if shapes is not None:
        object_shapes = shapes

    return object_shapes


def set_attributes(attributes):
    """
    Sets given attributes.

    Parameters
    ----------
    attributes : dict
        Attributes to set.

    Returns
    -------
    bool
        Definition success.
    """

    for attribute, value in attributes.items():
        cmds.setAttr(attribute, value)
    return True


def RGB_to_Lab(RGB, colourspace):
    """
    Converts given *RGB* value from given colourspace to *CIE Lab* colourspace.

    Parameters
    ----------
    RGB : array_like
        *RGB* value.
    colourspace : RGB_Colourspace
        *RGB* colourspace.

    Returns
    -------
    bool
        Definition success.
    """

    return XYZ_to_Lab(
        RGB_to_XYZ(np.array(RGB),
                   colourspace.whitepoint,
                   ILLUMINANTS.get(
                       'CIE 1931 2 Degree Standard Observer').get('E'),
                   colourspace.to_XYZ,
                   'Bradford',
                   colourspace.inverse_transfer_function),
        colourspace.whitepoint)


def RGB_identity_cube(name, density=20):
    """
    Creates an RGB identity cube with given name and geometric density.

    Parameters
    ----------
    name : str or unicode
        Cube name.
    density : int, optional
        Cube divisions count.

    Returns
    -------
    unicode
        Cube.
    """

    cube = cmds.polyCube(w=1,
                         h=1,
                         d=1,
                         sx=density,
                         sy=density,
                         sz=density,
                         ch=False)[0]
    set_attributes({'{0}.translateX'.format(cube): .5,
                    '{0}.translateY'.format(cube): .5,
                    '{0}.translateZ'.format(cube): .5})
    cmds.setAttr('{0}.displayColors'.format(cube), True)

    vertex_colour_array = OpenMaya.MColorArray()
    vertex_index_array = OpenMaya.MIntArray()
    point_array = OpenMaya.MPointArray()
    fn_mesh = OpenMaya.MFnMesh(get_dag_path(get_shapes(cube)[0]))
    fn_mesh.getPoints(point_array, OpenMaya.MSpace.kWorld)
    for i in range(point_array.length()):
        vertex_colour_array.append(point_array[i][0],
                                   point_array[i][1],
                                   point_array[i][2])
        vertex_index_array.append(i)
    fn_mesh.setVertexColors(vertex_colour_array, vertex_index_array, None)

    cmds.makeIdentity(cube, apply=True, t=True, r=True, s=True)
    cmds.xform(cube, a=True, rotatePivot=(0, 0, 0), scalePivot=(0, 0, 0))
    return cmds.rename(cube, name)


def Lab_colourspace_cube(colourspace, density=20):
    """
    Creates a *CIE Lab* colourspace cube with geometric density.

    Parameters
    ----------
    colourspace : RGB_Colourspace
        *RGB* Colourspace description.
    density : int, optional
        Cube divisions count.

    Returns
    -------
    unicode
        *CIE Lab* Colourspace cube.
    """

    cube = RGB_identity_cube(colourspace.name, density)
    it_mesh_vertex = OpenMaya.MItMeshVertex(get_dag_path(cube))
    while not it_mesh_vertex.isDone():
        position = it_mesh_vertex.position(OpenMaya.MSpace.kObject)
        it_mesh_vertex.setPosition(
            get_mpoint(tuple(np.ravel(RGB_to_Lab((position[0],
                                                  position[1],
                                                  position[2],),
                                                 colourspace)))))
        it_mesh_vertex.next()
    set_attributes({'{0}.rotateX'.format(cube): 180,
                    '{0}.rotateZ'.format(cube): 90})
    cmds.makeIdentity(cube, apply=True, t=True, r=True, s=True)
    return cube


def Lab_coordinates_system_representation():
    """
    Creates a *CIE Lab* coordinates system representation.

    Returns
    -------
    bool
        Definition success.
    """

    group = cmds.createNode('transform')

    cube = cmds.polyCube(w=600, h=100, d=600, sx=12, sy=2, sz=12, ch=False)[0]
    set_attributes({'{0}.translateY'.format(cube): 50,
                    '{0}.overrideEnabled'.format(cube): True,
                    '{0}.overrideDisplayType'.format(cube): 2,
                    '{0}.overrideShading'.format(cube): False})
    cmds.makeIdentity(cube, apply=True, t=True, r=True, s=True)
    cmds.select(['{0}.f[0:167]'.format(cube), '{0}.f[336:359]'.format(cube)])
    cmds.delete()

    cmds.nurbsToPolygonsPref(polyType=1, chordHeightRatio=0.975)

    for label, position, name in (('-a*', (-350, 0), 'minus_a'),
                                  ('+a*', (350, 0), 'plus_a'),
                                  ('-b*', (0, 350), 'minus_b'),
                                  ('+b*', (0, -350), 'plus_b')):
        curves = cmds.listRelatives(
            cmds.textCurves(f='Arial Black Bold', t=label)[0])
        mesh = cmds.polyUnite(*[cmds.planarSrf(x,
                                               ch=False,
                                               o=True,
                                               po=1)
                                for x in curves],
                              ch=False)[0]
        cmds.xform(mesh, cp=True)
        cmds.xform(mesh, translation=(0, 0, 0), absolute=True)
        cmds.makeIdentity(cube, apply=True, t=True, r=True, s=True)
        cmds.select(mesh)
        cmds.polyColorPerVertex(rgb=(0, 0, 0), cdo=True)
        set_attributes({'{0}.translateX'.format(mesh): position[0],
                        '{0}.translateZ'.format(mesh): position[1],
                        '{0}.rotateX'.format(mesh): -90,
                        '{0}.scaleX'.format(mesh): 50,
                        '{0}.scaleY'.format(mesh): 50,
                        '{0}.scaleY'.format(mesh): 50,
                        '{0}.overrideEnabled'.format(mesh): True,
                        '{0}.overrideDisplayType'.format(mesh): 2})
        cmds.delete(cmds.listRelatives(curves, parent=True))
        cmds.makeIdentity(mesh, apply=True, t=True, r=True, s=True)
        mesh = cmds.rename(mesh, name)
        cmds.parent(mesh, group)

    cube = cmds.rename(cube, 'grid')
    cmds.parent(cube, group)
    cmds.rename(group, 'Lab_coordinates_system_representation')

    return True
