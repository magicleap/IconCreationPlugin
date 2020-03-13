"""constants module holds commonly used variables for the package.
"""
# maya imports
from maya.api import OpenMaya

# constants
ICON_ANIMATION_CLIPS = (
    ('idle', 2),
    ('hover', 600),
    ('activate', 90),
    ('menu', 600),
    ('loading', 300)
)
ICON_ANIMATION_FPS = 'ntscf'
ICON_LINEAR_UNITS = 'cm'
ICON_UP_VECTOR = (0, 1, 0)
ICON_UP_AXIS = 'Y'
VALID_MATERIAL_TYPES = ['blinn', 'lambert', 'phong']
FILE_NODE_TYPE = 'file'
INVALID_NODE_TYPES = [
    OpenMaya.MFn.kConstraint,
    OpenMaya.MFn.kLight,
    OpenMaya.MFn.kCamera
]
PORTAL_NODEPATH = 'MLIcon:IconTemplate|MLIcon:Portal|MLIcon:InsidePortal_SkySphere'
PREVIEWER_PACKAGE_ID = 'com.magicleap.iconreview'
