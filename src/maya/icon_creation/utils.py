"""utils module contains all auxillary functions to interact with the Maya APIs.
"""
# built-in imports
import os
import platform
import shutil
import tempfile
import contextlib
import logging
import json

# maya imports
from maya import OpenMayaUI, cmds, mel
from maya.api import OpenMaya, OpenMayaAnim
from shiboken2 import wrapInstance
from PySide2 import QtWidgets, QtGui

# constants
LOG = logging.getLogger(__name__)

MTYPE_ICON_TEMPLATE_NODE = 'IconTemplateNode'
MTYPE_PBR_MATERIAL = 'MLAsset.PBR'
MODEL_FOLDER_NAME = 'Model'
PORTAL_FOLDER_NAME = 'Portal'
FILE_PATH_ATTR = 'fileTextureName'
ICON_TEMPLATE_PORTAL_TEXTURE = 'IconTemplateBackgroundTexture.png'
ICON_TEMPLATE_MODEL_TEXTURE = 'IconTemplateModelTexture.png'
ICON_TEMPLATE_NS = 'MLIcon'
ASSET_MANAGER_NODE_NAME = 'MLAssetManager'
DEFORMER_TYPES = [
    'kBlendShape',
    'kDeltaMush',
    'kSkin',
    'kSoftMod',
    'kLattice',
    'kCluster',
    'kWire',
    'kTension',
    'kShrinkWrapFilter',
    'kWrapFilter',
    'kSculpt',
    'kJiggleDeformer',
    'kNonLinear'
]
KMAT_MATERIAL_DEFINITION = {
    'albedo': '{relativeTexturePath}',
    'color': [1, 1, 1, 1],
    'blendmode': 'Opaque',
    'name': '{shaderName}',
    'shaderName': 'UnlitTextured'
}


def mayaMainWindow():
    """Get Maya's main window as a QWidget.

    Returns:
        QtWidgets.QWidget: Maya's main window wrapped in a Qt widget.
    """
    OpenMayaUI.MQtUtil.mainWindow()
    ptr = OpenMayaUI.MQtUtil.mainWindow()

    return wrapInstance(long(ptr), QtWidgets.QWidget)


def playIcon():
    """Get play icon.

    Returns:
        QtGui.QIcon
    """
    iconPath = mergePaths(os.path.dirname(__file__), 'resources', 'play_icon.png')
    return QtGui.QIcon(iconPath)


def setRangeIcon():
    """Get frame icon.

    Returns:
        QtGui.QIcon
    """
    iconPath = mergePaths(os.path.dirname(__file__), 'resources', 'frame_icon.png')
    return QtGui.QIcon(iconPath)


def pauseIcon():
    """Get pause icon.

    Returns:
        QtGui.QIcon
    """
    iconPath = mergePaths(os.path.dirname(__file__), 'resources', 'pause_icon.png')
    return QtGui.QIcon(iconPath)


def materialEmptyIcon():
    """Get empty material icon.

    Returns:
        QtGui.QIcon
    """
    iconPath = mergePaths(os.path.dirname(__file__), 'resources', 'materialEmpty_icon.png')
    return QtGui.QIcon(iconPath)


def wrenchIcon():
    """Get wrench icon.

    Returns:
        QtGui.QIcon
    """
    iconPath = mergePaths(os.path.dirname(__file__), 'resources', 'wrench_icon.png')
    return QtGui.QIcon(iconPath)


def magicLeapLogoIcon():
    """Get Magic Leap logo icon.

    Returns:
        QtGui.QIcon
    """
    iconPath = mergePaths(os.path.dirname(__file__), 'resources', 'logo.png')
    return QtGui.QIcon(iconPath)


def samplePortalIconMovie():
    """Get portal icon gif.

    Returns:
        QtGui.QIcon
    """
    iconPath = mergePaths(os.path.dirname(__file__), 'resources', 'sample_portal_icon.gif')
    return QtGui.QMovie(iconPath)


def mergePaths(*paths):
    """Join path parts.
    
    Return:
        str
    """
    path = None
    try:
        path = os.path.abspath(os.path.join(*paths))
    except AttributeError as err:
        LOG.error('A provided path does not exist.')
        LOG.error('Paths: {0}'.format(paths))

    return path


def getIconPortalSkySphereFilePath():
    """Get the portal mesh template file path.

    Returns:
        str
    """
    return mergePaths(os.environ['ASSET_TOOLS_DATA'], 'PortalSkySphere.fbx')


def getIconConverter():
    """Get the icon-converter CLI file path.

    Returns:
        str
    """
    if platform.system() == 'Darwin':
        return mergePaths(os.environ['ASSET_TOOLS_DATA'], 'icon-converter')
    elif platform.system() == 'Windows':
        return mergePaths(os.environ['ASSET_TOOLS_DATA'], 'icon-converter.exe')
    else:
        LOG.exception('Unsupported platform, icon-converter is not supported on %s', platform.system())


def getAssetPreviewer():
    """Get the asset-previewer CLI file path.

    Returns:
        str
    """
    if platform.system() == 'Darwin':
        return mergePaths(os.environ['ASSET_TOOLS_DATA'], 'asset-previewer')
    elif platform.system() == 'Windows':
        return mergePaths(os.environ['ASSET_TOOLS_DATA'], 'asset-previewer.exe')
    else:
        LOG.exception('Unsupported platform, asset-previewer is not supported on %s', platform.system())


def getIconTemplateNodeFullPath():
    """Get the first existing icon template node.

    Returns:
        str
    """
    iconTemplateNodes = getMetaType(MTYPE_ICON_TEMPLATE_NODE)

    if not iconTemplateNodes:
        return

    return iconTemplateNodes[0]


def stripNamespaces(excludeNamespaceList=None, emptyFirst=True):
    """Remove any user generated namespaces.
    
    Args:
        excludeNamespaceList(list[str]): Namespaces not to remove.
        emptyFirst(bool): Move object to the root namespace before deleting namespace.

    Returns:
        None
    """

    keep = ['UI', 'shared']

    if excludeNamespaceList is not None:
        keep.extend(excludeNamespaceList)

    namespaces = [ns for ns in cmds.namespaceInfo(lon=True, r=True) if ns not in keep]
    namespaces.sort(key=lambda namespace: namespace.count(':'), reverse=True)
    for ns in namespaces:
        try:
            cmds.namespace(rm=ns, mnr=emptyFirst)
            LOG.debug('Removed namespace: %s', ns)
        except RuntimeError:
            LOG.exception('Could not remove namespace, it might not be empty')


def importSceneReferences():
    """Import all file references into the current scene.

    Returns:
        None
    """
    while cmds.file(q=True, r=True):
        refs = cmds.file(q=True, r=True)
        for ref in refs:
            if cmds.referenceQuery(ref, il=True):
                cmds.file(ref, ir=True)
                LOG.debug('Importing file reference: {0}'.format(ref))

        refs = cmds.file(q=True, r=True)
        if not refs or refs is None:
            break


@contextlib.contextmanager
def openTempScene(filePath):
    """Open a copy of a maya scene, then reopen original when finished.

    Args:
        filePath(str): Path to an existing scene.

    Returns:
        None
    """
    tempDir = tempfile.gettempdir()

    tempPath = os.path.abspath(os.path.join(tempDir, os.path.basename(filePath)))

    try:
        shutil.copy2(filePath, tempPath)
        cmds.file(tempPath, o=True, f=True)
        yield tempPath
    except Exception as err:
        LOG.exception('Failed to open temporary scene: %s', err)
    finally:
        cmds.file(filePath, o=True, f=True)
        # FUTURE: Don't ignore errors from the cleanup of the temporary files.
        shutil.rmtree(tempDir, ignore_errors=True)


def exportTexture(sourceTexturePath, targetTexturePath):
    """Copy a texture file to a new location.
    
    Args:
        sourceTexturePath(str): Existing texture file path.
        targetTexturePath(str): The file path to save to.

    Returns:
        list[Error]
    """
    errors = []

    try:
        shutil.copy2(sourceTexturePath, targetTexturePath)
    except IOError as err:
        errors.extend(err)

    return errors


def isMacOS():
    """Check if MacOS is the running OS.

    Returns:
        bool
    """
    if platform.system() == 'Darwin':
        return True

    return False


def isWindows():
    """Check if Windows is the running OS.

    Returns:
        bool
    """
    if platform.system() == 'Windows':
        return True

    return False


def formatPathForWindowsMEL(path):
    """Format bad path conversions.

    Args:
        path(str): A file path.
    
    Returns:
        str
    """
    return path.replace('\\', '/')


def importFBX(filePath):
    """Import an FBX file into the current scene.

    Args:
        filePath(str): Path to an existing FBX file.

    Returns:
        None
    """
    # Since FBX is a plugin need to make sure it's loaded before exporting.
    if not cmds.pluginInfo('fbxmaya', q=True, l=True):
        cmds.loadPlugin('fbxmaya')

    mel.eval('FBXResetImport')

    mel.eval('FBXImportCameras -v false')
    mel.eval('FBXImportLights -v false')
    mel.eval('FBXImportConstraints -v false')
    mel.eval('FBXImportSetLockedAttribute -v true')
    mel.eval('FBXImportSkins -v false')
    mel.eval('FBXImportMode -v add')

    if isWindows():
        LOG.debug('Formatting filePath for Windows MEL evaluation.')
        filePath = formatPathForWindowsMEL(filePath)

    mel.eval('FBXImport -file "{0}"'.format(filePath))


def exportFBX(outputPath, selectionOnly=True, takes=[]):
    """Save out a rig's deformation skeleton and meshes.

    Args:
        nodePaths(list[str]): Nodes that will be exported.
        outputPath(str): Directory path where the FBX will be exported to.
        takes(dict): Animation clip data.

    Returns:
        None
    """
    # Since FBX is a plugin need to make sure it's loaded before exporting.
    if not cmds.pluginInfo('fbxmaya', q=True, l=True):
        cmds.loadPlugin('fbxmaya')

    # Reset the current FBX export settings.
    mel.eval('FBXResetExport')
    mel.eval('FBXExportSplitAnimationIntoTakes -c')

    # Base FBX export settings.
    mel.eval('FBXExportFileVersion "FBX201800"')
    mel.eval('FBXExportUpAxis y')
    mel.eval('FBXExportUseSceneName -v false')
    mel.eval('FBXExportQuaternion -v euler')
    mel.eval('FBXExportScaleFactor 1.0')
    mel.eval('FBXExportConvertUnitString cm')

    # Things that will be exported.
    mel.eval('FBXExportSkins -v true')
    mel.eval('FBXExportSmoothMesh -v true')
    mel.eval('FBXExportInAscii -v false')

    if takes:
        startFrame = min([x['startFrame'] for x in takes])
        endFrame = max([x['endFrame'] for x in takes])

        LOG.debug('Exporting animation for range: %s', [startFrame, endFrame])

        mel.eval('FBXExportBakeResampleAnimation -v false')
        mel.eval('FBXExportApplyConstantKeyReducer -v false')
        mel.eval('FBXProperty \"Export|IncludeGrp|Animation|ExtraGrp|RemoveSingleKey\" -v false')
        mel.eval('FBXProperty \"Export|IncludeGrp|Animation|CurveFilter\" -v false')

        mel.eval('FBXExportBakeComplexAnimation -v true')
        mel.eval('FBXExportBakeComplexStep -v 1')
        mel.eval('FBXExportBakeComplexStart -v {0}'.format(startFrame))
        mel.eval('FBXExportBakeComplexEnd -v {0}'.format(endFrame))
        
        mel.eval('FBXExportDeleteOriginalTakeOnSplitAnimation -v true')
        for take in takes:
            LOG.debug('Splitting take: %s', take['name'])
            mel.eval('FBXExportSplitAnimationIntoTakes -v \"{0}\" {1} {2}'.format(take['name'], take['startFrame'], take['endFrame']))

        LOG.debug(mel.eval('FBXExportSplitAnimationIntoTakes -q'))
    else:
        mel.eval('FBXExportBakeResampleAnimation -v false')
        mel.eval('FBXExportApplyConstantKeyReducer -v false')
        mel.eval('FBXProperty \"Export|IncludeGrp|Animation|ExtraGrp|RemoveSingleKey\" -v false')
        mel.eval('FBXProperty \"Export|IncludeGrp|Animation|CurveFilter\" -v false')

        mel.eval('FBXExportBakeComplexAnimation -v true')
        mel.eval('FBXExportBakeComplexStart -v 1')
        mel.eval('FBXExportBakeComplexEnd -v 2')
        mel.eval('FBXExportBakeComplexStep -v 1')

        mel.eval('FBXExportDeleteOriginalTakeOnSplitAnimation -v true')
        mel.eval('FBXExportSplitAnimationIntoTakes -v \"idle\" 1 2')

    # Things NOT to be exported.    
    mel.eval('FBXExportInstances -v false')
    mel.eval('FBXExportReferencedAssetsContent -v false')
    mel.eval('FBXExportSmoothingGroups -v false')
    mel.eval('FBXExportHardEdges -v false')
    mel.eval('FBXExportTangents -v false')
    mel.eval('FBXExportShapes -v false')
    mel.eval('FBXExportConstraints -v false')
    mel.eval('FBXExportCameras -v false')
    mel.eval('FBXExportLights -v false')
    mel.eval('FBXExportEmbeddedTextures -v false')
    mel.eval('FBXExportInputConnections -v false')

    # Command to actually do the exporting.
    if isWindows():
        outputPath = formatPathForWindowsMEL(outputPath)
    cmd = 'FBXExport -f "{0}"'.format(outputPath)
    
    if selectionOnly:
        cmd += ' -s'
    
    # Create the output directory, or else the FBX exporter silently fails.
    if not os.path.exists(os.path.dirname(outputPath)):
        os.makedirs(outputPath)

    errors = []
    try:
        mel.eval(cmd)
    except RuntimeError as err:
        errors.extend(err.args[0])

    return errors


def getProjectDirectory():
    """Get the full file path to the current project set in Maya.

    Returns:
        str: File path to the project root directory.
    """
    # If the user has set the project, there will be a scene directory.
    projectDirectory = cmds.workspace(q=True, rd=True)
    projectOutputFolderName = 'scene'
    if projectOutputFolderName in cmds.workspace(q=True, frl=True):
        return os.path.abspath(os.path.join(projectDirectory, cmds.workspace(fre=projectOutputFolderName)))

    # If the file is save and doesn't belong to a project, 
    # use the scene location as the project.
    currentScene = os.path.abspath(cmds.file(q=True, sn=True))
    if currentScene:
        return os.path.dirname(currentScene)

    # If nothing is setup, just use the default Maya project directory.
    return os.path.abspath(cmds.workspace(q=True, dir=True))


def getMetaType(metaType):
    """Get full node paths of a specific MetaType.

    Args:
        metaType: name of MetaType

    Returns:
        list[str]
    """
    result = []

    attrs = cmds.ls('*.metaTypes', long=True, recursive=True)

    for attr in attrs:
        nodePath = attr.split('.')[0]
        if hasMetaType(nodePath, metaType):
            result.append(nodePath)

    return result


def setMetaType(nodePath, metaType):
    """Add the given metatype to the node.
    
    Args:
        nodePath(str): Node name.
        metaType(str): A metatype.

    Returns:
        None
    """
    attrExists = cmds.attributeQuery('metaTypes', node=nodePath, exists=True)

    if not attrExists:
        cmds.addAttr(nodePath, longName='metaTypes', dataType='string')

    existingMetaTypeData = cmds.getAttr('{0}.metaTypes'.format(nodePath))

    if existingMetaTypeData:
        value = existingMetaTypeData + ':{0}'.format(metaType)
    else:
        value = metaType

    cmds.setAttr('{0}.metaTypes'.format(nodePath), value, type='string')


def hasMetaType(nodePath, metaType):
    """Check if a given node has a metatype.

    Args:
        nodePath(str): Node name.
        metaType(str): A metatype.

    Returns:
        bool
    """
    attrExists = cmds.attributeQuery('metaTypes', node=nodePath, exists=True)

    if not attrExists:
        return False

    existingMetaTypeData = cmds.getAttr('{0}.metaTypes'.format(nodePath))
    metaTypes = existingMetaTypeData.split(':')

    if metaType in metaTypes:
        return True

    return False


def playAnimation(startFrame, endFrame, play=True):
    """Set the timeline, and play the animation.

    Args:
        startFrame(int): Frame to start at.
        endFrame(int): Frame to set end to.
        play(bool): Whether to start/stop the animation.

    Returns:
        None
    """
    cmds.playbackOptions(
        minTime=startFrame,
        animationStartTime=startFrame,
        maxTime=endFrame,
        animationEndTime=endFrame,
        view='all',
        loop='continuous'
    )

    if play:
        cmds.play(forward=True)
    else:
        cmds.play(state=False)


def setAnimationTimeline(startFrame, endFrame):
    """Set the timeline.

    Args:
        startFrame(int): Frame to start at.
        endFrame(int): Frame to set end to.

    Returns:
        None
    """
    cmds.playbackOptions(
        minTime=startFrame,
        animationStartTime=startFrame,
        maxTime=endFrame,
        animationEndTime=endFrame
    )


def isSceneSaved():
    """Check if the scene exists on disk.

    Returns:
        bool
    """
    if cmds.file(query=True, sceneName=True):
        return True

    return False


def connect(sourceAttr, destinationAttr):
    """Connect one node attribute to another.

    Args:
        sourceAttr(str): First attribute name.
        destinationAttr(str): Second attribute name.

    Returns:
        None
    """
    node, attr = sourceAttr.split('.')
    attrExists = cmds.attributeQuery(attr, node=node, exists=True)
    if not attrExists:
        cmds.addAttr(node, longName=attr, attributeType='message')

    node, attr = destinationAttr.split('.')
    attrExists = cmds.attributeQuery(attr, node=node, exists=True)
    if not attrExists:
        cmds.addAttr(node, longName=attr, attributeType='message')

    cmds.connectAttr(sourceAttr, destinationAttr)


def getMObject(nodeName):
    """Get the first node associated to the given name.
    
    nodeName(str): Name of an existing node.

    Returns:
        OpenMaya.MObject
    """
    selectionList = OpenMaya.MSelectionList()
    selectionList.add(nodeName)

    return selectionList.getDependNode(0)


def getNodePaths(nodes):
    """Get the full path of nodes.

    Args:
        node(list[OpenMaya.MObject]): An existing nodes.

    Returns:
        list[str]
    """
    result = []

    for node in nodes:
        nodePath = getNodePath(node)
        result.append(nodePath)

    return result


def getNodePath(node):
    """Get the full path to a node.

    Args:
        node(OpenMaya.MObject): An existing node.

    Returns:
        str
    """
    dag = OpenMaya.MFnDagNode(node)

    return dag.fullPathName()


def getConnectedNode(node, attrName):
    """Get the node connected to a given attribute.

    Args:
        node(OpenMaya.MObject): An existing node.
        attrName(str): Attribute name on node.

    Returns:
        OpenMaya.MObject
    """
    depNode = OpenMaya.MFnDependencyNode(node)
    mplug = depNode.findPlug(attrName, False)

    if not mplug.isConnected or not mplug.isSource:
        return

    destPlugs = mplug.destinations()

    return destPlugs[0].node()


def getChildMeshes(node):
    """Get all mesh objects recursively of a given node.

    Args:
        node(OpenMaya.MObject): An existing node.

    Returns:
        list[OpenMaya.MObject]
    """
    allTransforms = getChildren(node)

    meshes = []
    
    for transform in allTransforms:
        if getMeshes(transform):
            meshes.append(transform)

    return meshes


def getChildren(node, recursive=True, nodeType=OpenMaya.MFn.kTransform):
    """Get all children of the given type with the given node.

    Args:
        node(OpenMaya.MObject): An existing node.
        recursive(bool): Search node hierarchy.
        nodeType(OpenMaya.MFn): Can be used to override the child type returned.

    Returns:
        list[OpenMaya.MObject]
    """
    result = []

    dagNode = OpenMaya.MFnDagNode(node)

    for i in range(dagNode.childCount()):
        childMObject = dagNode.child(i)

        if childMObject.hasFn(nodeType):
            result.append(childMObject)

        if recursive:
            result.extend(getChildren(childMObject, recursive, nodeType))

    return result


def getMeshes(node):
    """Get all mesh children.

    Args:
        node(OpenMaya.MObject): An existing node.

    Return:
        list[OpenMaya.MObject]
    """
    result = []

    dag = OpenMaya.MFnDagNode(node)
    
    for i in range(dag.childCount()):
        childMObject = dag.child(i)
    
        if childMObject.hasFn(OpenMaya.MFn.kMesh):
            result.append(childMObject)

    return result


def openAttributeEditor():
    """Shows the Attribute Editor.

    Returns:
        None
    """
    cmds.ToggleAttributeEditor()


def newScene(filePath):
    """Create a new Maya ASCII scene.

    Args:
        filePath(str): Path to save the file.

    Return:
        bool
    """
    result = False
    
    # Save the current file to avoid a RuntimeError when creating a new
    # file when an unsaved file is already opened.
    if cmds.file(query=True, sceneName=True) and cmds.file(query=True, modified=True):
        cmds.file(save=True, force=True, type='mayaAscii')

    cmds.file(force=True, newFile=True)

    if filePath:
        cmds.file(rename=filePath)
        cmds.file(save=True, force=True, type='mayaAscii')
        result = True

    return result


def openScene(filePath):
    """Open a given maya scene.

    Args:
        filePath(str): Path to an existing maya scene file.

    Returns:
        bool
    """
    if os.path.isfile(filePath):
        cmds.file(filePath, o=True, f=True)
        return True

    LOG.exception('Failed to open file: %s', filePath)

    return False


def saveScene():
    """Force the scene to save.

    Returns:
        None
    """
    if cmds.file(query=True, sceneName=True) and cmds.file(query=True, modified=True):
        cmds.file(save=True, force=True, type='mayaAscii')


def getSceneDirectory():
    """Get the active scene directory.
    If a project is set use that directory, otherwise use
    the directory of the currently open scene.

    Returns:
        str
    """
    scenePath = cmds.file(query=True, sceneName=True)
    if not scenePath:
        return getProjectDirectory()

    return os.path.dirname(scenePath)