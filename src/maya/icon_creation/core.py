"""core module contains all the main logic for building and export Icons.
"""
# built-in imports
import os
import logging
import shutil
import json
import subprocess
import re
import collections
import zipfile

# maya imports
from maya import cmds, mel
from maya.api import OpenMaya

# package imports
from . import utils
from . import constants
from . import mldb

# constants
LOG = logging.getLogger(__name__)


def getMObject(nodeName):
    """Get a node.

    Args:
        nodeName(str): Existing node name.

    Returns:
        OpenMaya.MObject
    """
    selectionList = OpenMaya.MSelectionList()
    selectionList.add(nodeName)

    return selectionList.getDependNode(0)


def getNodePath(node):
    """Get a node's full path name.
    
    Args:
        node(OpenMaya.MObject): An existing node.
    Returns:
        str
    """
    dag = OpenMaya.MFnDagNode(node)
    
    return dag.fullPathName()


def getIconTemplateNode():
    """Get an icon template node in the current scene.

    Returns:
        OpenMaya.MObject
    """
    if not iconTemplateExists():
        return

    nodePath = utils.getIconTemplateNodeFullPath()

    return getMObject(nodePath)


def getModelComponentNode():
    """Get the model component node from the icon template.

    Returns:
        OpenMaya.MObject
    """
    if not iconTemplateExists():
        return

    nodePath = utils.getIconTemplateNodeFullPath()
    node = utils.getMObject(nodePath)

    return utils.getConnectedNode(node, 'modelComponent')


def getPortalComponentNode():
    """Get the portal component node from the icon template.

    Returns:
        OpenMaya.MObject
    """
    if not iconTemplateExists():
        return

    nodePath = utils.getIconTemplateNodeFullPath()
    node = utils.getMObject(nodePath)

    return utils.getConnectedNode(node, 'portalComponent')


def getIconSettings():
    """Get the icon settings from the icon template node.

    Returns:
        dict
    """
    settings = {}
    
    node = getIconTemplateNode()

    try:
        depNode = OpenMaya.MFnDependencyNode(node)
        
        plug = depNode.findPlug('iconSettings', False)
        rawSettingsData = plug.asString()
        
        settings = json.loads(rawSettingsData)
    except ValueError:
        LOG.info('No settings data found on Icon Template.')

    return settings


def saveIconSettings(data={}):
    """Save the given settings to the icon template node.

    Args:
        data(dict): Key, value pairs to save, must be JSON serializeable.

    Returns:
        None
    """
    node = getIconTemplateNode()

    try:
        depNode = OpenMaya.MFnDependencyNode(node)
        
        settings = json.dumps(data)

        plug = depNode.findPlug('iconSettings', False)
        plug.setString(settings)
    except Exception as err:
        LOG.error(err)
        LOG.info('No settings data found on Icon Template.')


def saveOutputPath(value):
    """Set the output path setting.

    Args:
        value(str): file path.
    
    Returns:
        None
    """
    if not iconTemplateExists():
        LOG.info('No Icon Template node in the scene, cant saving Icon settings.')
        return

    settingsData = getIconSettings()
    settingsData['outputPath'] = value
    saveIconSettings(settingsData)


def saveSDKPath(value):
    """Set the MLSDK path setting.

    Args:
        value(str): file path.
    
    Returns:
        None
    """
    if not iconTemplateExists():
        LOG.info('No Icon Template node in the scene, cant saving Icon settings.')
        return

    settingsData = getIconSettings()
    settingsData['sdkPath'] = value
    saveIconSettings(settingsData)


def importTemplate(**settings):
    """Create/Import a new icon template.

    Args:
        settings(dict): Data to load onto the template.

    Returns:
        bool
    """
    if iconTemplateExists():
        LOG.exception('template already in the scene, delete it and try again.')
        return False

    namespace = ':{0}'.format(utils.ICON_TEMPLATE_NS)
    
    if not cmds.namespace(exists=namespace):
        cmds.namespace(add=namespace)
    
    templateRootNode = cmds.createNode('transform', name='{0}:IconTemplate'.format(namespace))
    utils.setMetaType(templateRootNode, utils.MTYPE_ICON_TEMPLATE_NODE)
    cmds.addAttr(templateRootNode, longName='iconSettings', dataType='string')

    modelGroupNode = cmds.createNode('transform', name='{0}:Model'.format(namespace))
    utils.connect('{0}.modelComponent'.format(templateRootNode), '{0}.IconTemplate'.format(modelGroupNode))

    portalGroupNode = cmds.createNode('transform', name='{0}:Portal'.format(namespace))
    utils.connect('{0}.portalComponent'.format(templateRootNode), '{0}.IconTemplate'.format(portalGroupNode))

    cmds.parent(modelGroupNode, portalGroupNode, templateRootNode)

    portalSkySphereFilePath = utils.getIconPortalSkySphereFilePath()
    cmds.namespace(setNamespace=namespace)
    utils.importFBX(portalSkySphereFilePath)

    # Need to use a hardcoded node path because currently there is no way to get,
    # the imported nodes from an FBX.
    portalSkySphereNodePath = '{0}:InsidePortal_SkySphere'.format(namespace)
    cmds.parent(portalSkySphereNodePath, portalGroupNode)

    # Need to reset the namespace to the root one, to avoid user importing new data into it.
    # This doesn't stop them, but makes it harder is all.
    cmds.namespace(setNamespace=':')

    utils.saveScene()

    return True


def iconTemplateExists():
    """Get the first existing icon template in the scene.

    Returns:
        bool
    """
    iconTemplateNodePaths = utils.getMetaType(utils.MTYPE_ICON_TEMPLATE_NODE)
    
    if iconTemplateNodePaths:
        return True

    return False


def buildIcon(validate=True, export=False, cleanup=True):
    """Build a valid Portal Icon.
    
    Args:
        validate(bool): Should the icon be validated after a successful build.
        export(bool): Should the icon be bundled after a successful build.
        cleanup(bool): Should the built icon be removed, useful for validation only.

    Returns:
        bool
    """
    result = False

    try:
        result = exportIcon()
        LOG.info('exported: %s', result)
        if validate:
            result = validateIcon()
            LOG.info('validated: %s', result)
            if cleanup:
                LOG.info('Cleaning up Icon.')
    except Exception as err:
        LOG.exception('something went wrong exporting.')
        result = False
    
    return result


def prevalidateScene():
    """Validations to check for before build.

    Returns:
        list[str]
    """
    errors = []

    if checkModelForAnimatedTransforms():
        errors.append('Animated transform(s) found under Model component.')

    if checkPortalForAnimatedTransforms():
        errors.append('Animated transform(s) found under Portal component.')

    return errors


def validateIcon():
    """Run validation checks on a built icon using the icon-converter CLI.

    Returns:
        bool
    """
    result = False

    # Run external validations handled by icon-converter.
    # Most validation should go into the icon-converter, other
    # validations related to Maya are handled above.
    outputPath = getIconDirectory()
    
    # modelPath and portalPath need to be Unix styled paths for
    # the icon-converter.
    modelPath = '{0}/{1}'.format(os.path.basename(outputPath), utils.MODEL_FOLDER_NAME)

    portalPath = '{0}/{1}'.format(os.path.basename(outputPath), utils.PORTAL_FOLDER_NAME)

    executable = utils.getIconConverter()
    
    cmd = [
        executable,
        'validate',
        '--format', 'json', 
        '-m', modelPath,
        '--local-model-folder', utils.MODEL_FOLDER_NAME,
        '-p', portalPath,
        '--local-portal-folder', utils.PORTAL_FOLDER_NAME,
        outputPath
        # '"{0}"'.format(outputPath)
    ]

    errors = []

    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        LOG.debug(out)
        result = True
    except subprocess.CalledProcessError as err:
        LOG.error(err.cmd)
        LOG.error(err.output)
        errors = parseValidationOutput(err.output)
        result = False

    # Adding this just to make errors more readable in the Script Editor for now.
    # FUTURE: Instead of just logging this, have an error dialog for the user.
    if errors:
        msg = ''
        for err in errors:
            msg += '\n{0}\n'.format(err['code'])
            msg += '\t{0}\n'.format(err['message'])
        LOG.info('\n\nError Report:\n%s\n', msg)

    return result


def parseValidationOutput(output):
    """Read validation output from the icon-converter CLI.

    Args:
        output(str): Output data.

    Returns:
        list[str]: Errrors returned by icon-converter.
    """
    errors = []

    for line in output.splitlines():
        jsonOutput = json.loads(line)
        if 'errors' in jsonOutput:
            errors.extend(jsonOutput['errors'])

    return errors


def exportIcon():
    """Bundle a built icon into a zip archive.

    Returns:
        bool
    """
    currentScenePath = os.path.abspath(cmds.file(query=True, sceneName=True))
    if not currentScenePath:
        LOG.error('Save your file before exporting.')
        return False

    LOG.info('Attempting to save the file.')
    cmds.file(save=True, force=True)

    settingsData = getIconSettings()
    outputPath = settingsData.get('outputPath', None)
    if outputPath is None:
        raise ValueError('outputPath is not set.')

    result = False
    with utils.openTempScene(currentScenePath) as tmpPath:
        utils.importSceneReferences()
        # utils.stripNamespaces(excludeNamespaceList=[self.namespace])
        unlockNodes()
        utils.stripNamespaces()
        bakeTransforms()
        bakeAnimation()
        for componentType in ['Model', 'Portal']:
            result = exportIconComponent(componentType=componentType)

    LOG.info('Export Completed: {0}'.format(outputPath))
    return result


def getIconDirectory():
    """Get the icon export root directory.
    
    Returns:
        str
    """
    settingsData = getIconSettings()

    outputPath = settingsData.get('outputPath', None)
    if outputPath is None:
        LOG.exception('missing outputPath from settings.')
        return None

    iconDirectory = utils.mergePaths(outputPath, 'Icon')

    return iconDirectory


def exportIconComponent(componentType):
    """Export out the given icon component.
    
    Args:
        componentType(str): Model or Portal.

    Return:
        bool
    """
    iconDirectory = getIconDirectory()
    outputDirectory = utils.mergePaths(iconDirectory, componentType)

    # Remove all directory incase an IconComponent was previously exported.
    shutil.rmtree(path=outputDirectory, ignore_errors=True)
    if not os.path.exists(outputDirectory):
        os.makedirs(outputDirectory)

    if componentType == 'Model':
        node = getModelComponentNode()
    elif componentType == 'Portal':
        node = getPortalComponentNode()
    else:
        return

    meshes = getMeshesRecursive(node)
    materials, unsupportedMaterials = getMaterialsForMeshes(meshes)
    
    # Make sure material names are all unique to avoid validation errors.
    # If multiple copies of a material are listed in a KMAT, icon-converter fails,
    # submission tests.
    materials = list(set(materials))

    textures = getTexturesFromMaterials(materials)
    textureFilePaths = getFilePathsFromTextures(textures)

    # Export textures, need to do this before KMAT.
    for texture in textureFilePaths:
        textureExportPath = utils.mergePaths(outputDirectory, os.path.basename(texture))
        utils.exportTexture(texture, textureExportPath)
    
    # Export KMAT.
    kmatData = {
        'global': {
            'color': [1, 1, 1, 1],
            'blendmode': 'Opaque'
        },
        'materials': []
    }

    for mat in materials:
        tex = getTexture(mat)
        materialDefinition = utils.KMAT_MATERIAL_DEFINITION.copy()

        if tex is not None:
            textureFilePath = getFilePathFromTexture(tex)
            if not textureFilePath:
                continue
            fileName = os.path.basename(textureFilePath)
            relativeTexture = '{0}/{1}/{2}'.format(os.path.basename(iconDirectory), componentType, fileName)
            materialDefinition['albedo'] = materialDefinition['albedo'].format(relativeTexturePath=relativeTexture)
            materialDefinition['name'] = materialDefinition['name'].format(shaderName=mat)
        else:
            colorRGB = cmds.getAttr(mat + '.color')[0]
            materialDefinition['color'] = [colorRGB[0], colorRGB[1], colorRGB[2], 1]
            materialDefinition['name'] = materialDefinition['name'].format(shaderName=mat)
            materialDefinition.pop('albedo')

        kmatData['materials'].append(materialDefinition)

    kmatPath = utils.mergePaths(outputDirectory, '{0}.kmat'.format(componentType))
    with open(kmatPath, 'w+') as fp:
        json.dump(kmatData, fp, indent=2)

    # Parent component group to world
    cmds.parent(getNodePath(node), w=True)

    # Get list of supported and unsupported children.
    transforms = getChildren(node)

    unsupportedNodes = []
    for nodeType in constants.INVALID_NODE_TYPES:
        nodes = getChildren(node, True, nodeType)
        unsupportedNodes.extend(nodes)

    supportedNodes = [x for x in transforms if x not in unsupportedNodes]

    supportedNodePaths = [getNodePath(x) for x in supportedNodes]

    # Remove unsupported nodes.
    unsupportedNodePaths = [getNodePath(x) for x in unsupportedNodes]
    if unsupportedNodePaths:
        cmds.delete(unsupportedNodePaths)

    # Parent component group to world
    children = getChildren(node=node, recursive=False)
    childNodePaths = [getNodePath(x) for x in children]
    cmds.parent(childNodePaths, world=True, absolute=True)

    # Select all nodes of component
    bakeableNodes = [getNodePath(x) for x in transforms if getNodePath(x)]
    cmds.select(bakeableNodes, replace=True)

    # Export an FBX that is the base format for the Icon.
    fbxPath = utils.mergePaths(outputDirectory, '{0}.fbx'.format(componentType))
    settingsData = getIconSettings()
    animationTakes = settingsData.get('animationTakes', [])
    err = utils.exportFBX(fbxPath, selectionOnly=True, takes=animationTakes)

    return True


def unlockNodes():
    """Unlock the TRS channels of a transform.

    Returns:
        None
    """
    attrs = ['t', 'r', 's']
    nodes = [constants.PORTAL_NODEPATH]
    for node in nodes:
        for attr in attrs:
            cmds.setAttr(node + '.' + attr, lock=False)


def bakeTransforms():
    """Bake non zero transform values into basic transforms.
    Portal Icons do not support not joint transform data.

    Returns:
        None
    """
    iconTemplateNode = getIconTemplateNode()
    transforms = getChildren(node=iconTemplateNode)

    for transform in transforms:
        if transform.hasFn(OpenMaya.MFn.kJoint):
            continue

        if getMeshes(transform):
            continue

        nodePath = utils.getNodePath(transform)

        children = getChildren(node=transform, recursive=False)
        
        childrenNodePaths = [utils.getNodePath(child) for child in children]
        cmds.parent(childrenNodePaths, world=True)

        LOG.info('Baking transform on {0}'.format(nodePath))
        cmds.makeIdentity(nodePath, apply=True, translate=True, rotate=True, scale=True)

        childrenNodePaths = [utils.getNodePath(child) for child in children]
        cmds.parent(childrenNodePaths, nodePath)


def bakeAnimation():
    """Bake animation on all icon template joints.

    Returns:
        None
    """
    LOG.info('Start baking animation.')
    settingsData = getIconSettings()
    defaultTake = dict(name='idle', startFrame=1, endFrame=2)
    animationTakes = settingsData.get('animationTakes', [defaultTake])

    if not animationTakes:
        return

    iconTemplateNode = getIconTemplateNode()
    transforms = getChildren(node=iconTemplateNode)

    unsupportedNodes = []
    for nodeType in constants.INVALID_NODE_TYPES:
        unsupported = getChildren(node=iconTemplateNode, recursive=True, nodeType=nodeType)
        unsupportedNodes.extend(unsupported)

    supportedNodes = [x for x in transforms if x not in unsupportedNodes]
    supportedNodePaths = [getNodePath(x) for x in supportedNodes]
    LOG.info('Begin baking nodes: %s', supportedNodePaths)

    # Check if exporting animation.
    for take in animationTakes:
        timeRange = (take['startFrame'], take['endFrame'])
        LOG.info(
            'Baking animation for take {0}({1} - {2})'.format(
                take['name'],
                take['startFrame'],
                take['endFrame']
            )
        )
        # Bake supported children.
        # Delete static keys on baked children.
        cmds.bakeResults(
            supportedNodePaths,
            time=timeRange,
            simulation=True,
            sampleBy=1,
            disableImplicitControl=True,
            preserveOutsideKeys=True
        )

        # cmds.delete(supportedNodePaths, staticChannels=True)


def getMaterialsForMesh(mesh):
    """Get assigned materials on a mesh.

    Args:
        mesh(str | OpenMaya.MObject): Mesh node path name.

    Returns:
        list[list[str], list[str]]
    """
    result = []
    unsupported = []

    if isinstance(mesh, OpenMaya.MObject):
        mesh = getNodePath(mesh)

    if not isinstance(mesh, (str, unicode)):
        raise ValueError('Mesh is not a string.')

    if not cmds.objExists(mesh):
        LOG.exception('{0} does not exist in the scene.'.format(mesh))
        return []

    engines = cmds.listConnections(mesh, type='shadingEngine', destination=True, source=False) or []
    for engine in engines:
        connectedMaterials = cmds.listConnections(engine + '.surfaceShader', source=True) or []

        for material in connectedMaterials:
            if cmds.nodeType(material) not in constants.VALID_MATERIAL_TYPES:
                unsupported.append(material)

        result.extend([m for m in connectedMaterials if m not in unsupported])

    LOG.debug('mesh %s', mesh)

    LOG.debug('unsupported mats {0}'.format(unsupported))

    return result, unsupported


def getMaterialsForMeshes(meshes):
    """Get assigned materials on a meshes.
    
    Args:
        meshes(list[str | OpenMaya.MObject]): Mesh node path names.

    Returns:
        list[list[list[str], list[str]]]
    """
    mats = []
    unsupportedMats = []

    for mesh in meshes:
        meshMats, unsupported = getMaterialsForMesh(mesh)
        mats.extend(meshMats)
        unsupportedMats.extend(unsupported)

    return mats, unsupportedMats


def getTexturesFromMaterials(materials):
    """Get texture files assigned to materials.
    
    Args:
        materials(list[str]): Material names.
    
    Returns:
        list[str]
    """
    result = []

    for material in materials:
        tex = getTexture(material)
        if tex is not None:
            result.append(tex)

    return result


def getTexture(material):
    """Get the color texture assigned to a material.

    Args:
        materials(str): Material name.

    Returns:
        str
    """
    if not isinstance(material, (str, unicode)):
        raise ValueError('Material is not a string.')

    if not cmds.objExists(material):
        LOG.exception('{0} does not exist in the scene.'.format(material))
        return

    fileNodes = cmds.listConnections(material + '.color', source=True, type=constants.FILE_NODE_TYPE) or []
    
    if not fileNodes:
        LOG.debug('No file node connected to material color attribute.')
        return

    return fileNodes[0]


def isValidMaterial(material):
    """Check if a given material is one of the valid types.
    
    Args:
        material(str): Material name.

    Returns:
        bool
    """
    if cmds.nodeType(material) in constants.VALID_MATERIAL_TYPES:
        return True

    return False


def setColorTexture(material, textureFilePath):
    """Set the color texture of a material.

    Args:
        material(str): Material name.
        textureFilePath(str): Existing texture file path.

    Returns:
        None
    """
    if not isValidMaterial(material):
        LOG.exception('unsupported type for material %s', material)
        return

    texture = getTexture(material)

    if texture is None:
        texture = createFileTexture()
        cmds.connectAttr(texture + '.outColor', material + '.color')

    cmds.setAttr(texture + '.' + utils.FILE_PATH_ATTR, textureFilePath, type='string')


def createFileTexture():
    """Create a new file texture node.

    Returns:
        str
    """
    texture = cmds.shadingNode('file', asTexture=True)
    placement = cmds.shadingNode('place2dTexture', asUtility=True)

    cmds.connectAttr(placement + '.outUV', texture + '.uvCoord')
    cmds.connectAttr(placement + '.outUvFilterSize', texture + '.uvFilterSize')

    attrs = [
        '.vertexCameraOne',
        '.vertexUvOne',
        '.vertexUvTwo',
        '.vertexUvThree',
        '.coverage',
        '.mirrorU',
        '.mirrorV',
        '.noiseUV',
        '.offset',
        '.repeatUV',
        '.rotateFrame',
        '.rotateUV',
        '.stagger',
        '.translateFrame',
        '.wrapU',
        '.wrapV'
    ]

    for attr in attrs:
        cmds.connectAttr(placement + attr, texture + attr)

    return texture


def getFilePathFromTexture(texture):
    """Get file path associated to file texture node.

    Args:
        str: Texture node name.

    Returns:
        str
    """
    texturePath = cmds.getAttr(texture + '.' + utils.FILE_PATH_ATTR)

    return texturePath


def getFilePathsFromTextures(textures):
    """Get all texture file paths from texture nodes.

    Args:
        textures(list[str]): Texture node names.

    Returns:
        list[str]
    """
    result = []

    for texture in textures:
        texturePath = cmds.getAttr(texture + '.' + utils.FILE_PATH_ATTR)
        if texturePath and os.path.exists(texturePath):
            result.append(texturePath)

    return result


def getMeshesRecursive(node):
    """Get all child meshes of a node.

    Args:
        node(OpenMaya.MObject): Existing node.

    Returns:
        list[OpenMaya.MObject]
    """
    allTransforms = getChildren(node)

    meshes = []
    for transform in allTransforms:
        m = getMeshes(transform)
        meshes.extend(m)

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


def selectNodes(nodes):
    """Select the given nodes.

    Args:
        nodes(list[str]): Node names.

    Returns:
        None
    """
    cmds.select(nodes, r=True)


def checkSceneSettings():
    """Get whether the scene settings are valid for icon export.

    Returns:
        dict
    """

    result = {}

    linearUnits = cmds.currentUnit(query=True, linear=True)
    linearUnitsChecked = True if linearUnits == constants.ICON_LINEAR_UNITS else False
    
    timeUnits = cmds.currentUnit(query=True, time=True)
    timeUnitsChecked = True if timeUnits == constants.ICON_ANIMATION_FPS else False
    
    return dict(units=linearUnitsChecked, fps=timeUnitsChecked)


def getSceneSettings():
    """Get scene linear units and time units.

    Returns:
        dict
    """
    linearUnits = cmds.currentUnit(query=True, linear=True)
    timeUnits = cmds.currentUnit(query=True, time=True)

    return dict(units=linearUnits, fps=timeUnits)

def setSceneSettings(units=True, fps=True):
    """Set the time or fps units.

    Args:
        units(bool): Linear units.
        fps(bool): Time units.

    Returns:
        None
    """
    if units:
        cmds.currentUnit(linear=constants.ICON_LINEAR_UNITS)
    
    if fps:
        cmds.currentUnit(time=constants.ICON_ANIMATION_FPS)


def getUnitsValue():
    """Get linear units title.

    Returns:
        str
    """
    fullName = cmds.currentUnit(query=True, linear=True, fullName=True)
    shortName = cmds.currentUnit(query=True, linear=True, fullName=False)

    result = '{0}({1})'.format(fullName.capitalize(), shortName.upper())

    return result


def getFPSValue():
    """Get time units title.

    Returns:
        str
    """
    fps = dict(
        game=15,
        film=24,
        pal=25,
        ntsc=30,
        show=48,
        palf=50,
        ntscf=60
    )[cmds.currentUnit(query=True, time=True)]

    return '{0} FPS'.format(fps)


def updateClipData(payload={}):
    """Set animation clip data.
    
    Args:
        payload(dict): Animation data.

    Returns:
        None
    """
    if not payload:
        return

    settingsData = getIconSettings()
    animData = settingsData.get('animationTakes', [])

    clipDataIndex = -1
    for index, clipData in enumerate(animData):
        if clipData['name'] == payload['name']:
            clipDataIndex = index
            break

    if clipDataIndex == -1:
        if not payload['enabled']:
            return

        newClipData = dict(
            name=payload['name'],
            startFrame=payload['startFrame'],
            endFrame=payload['endFrame']
        )
        animData.append(newClipData)

        settingsData['animationTakes'] = animData
        saveIconSettings(settingsData)

        LOG.debug('animation take added: %s', payload)

        return

    if not payload['enabled']:
        animData.pop(clipDataIndex)

        LOG.debug('animation take removed: %s', payload)

        settingsData['animationTakes'] = animData
        saveIconSettings(settingsData)

        return

    for k, v in animData[clipDataIndex].items():
        if k in payload:
            animData[clipDataIndex][k] = v

            LOG.debug('animation take updated: %s', payload)

    settingsData['animationTakes'] = animData
    saveIconSettings(settingsData)


def getAnimationData(asDict=True):
    """Get animation clip data.

    Returns:
        dict
    """
    settingsData = getIconSettings()
    animData = settingsData.get('animationTakes', [])

    if not asDict:
        return animData

    result = {}
    for item in animData:
        result[item['name']] = dict(startFrame=item['startFrame'], endFrame=item['endFrame'])

    return result


def createIconZip():
    """Create icon bundle.

    Returns:
        str
    """
    def _writeZip(path, zipObject):
        fd = os.path.basename(os.path.dirname(path))
        fn = os.path.basename(path)
        archiveName = os.path.join(fd, fn)
        zipObject.write(path, archiveName)

    def _getGLBPaths(path):
        for roots, dirs, files in os.walk(path):
            for fn in files:
                if os.path.splitext(fn)[1] in ['.kmat', '.fbx', '.png', '.jpg']:
                    yield os.path.join(roots, fn)

    iconDirectory = getIconDirectory()
    
    if iconDirectory is None:
        LOG.exception('cannot create zip for Icon, missing outputPath.')

    zipPath = utils.mergePaths(os.path.dirname(iconDirectory), 'Icon.zip')

    with zipfile.ZipFile(zipPath, 'w') as zp:
        for p in _getGLBPaths(iconDirectory):
            _writeZip(p, zp)

    return zipPath


def openIconPreviewer(iconZipPath, mlsdkPath=None):
    """Open Icon Review app on device and load icon bundle.

    Args:
        iconZipPath(str): Existing icon bundle.
        mlsdkPath(str): MLSDK version directory path.

    Returns:
        str
    """
    if mlsdkPath is not None:
        if not os.path.exists(mlsdkPath):
            return 'MLSDK path does not exist.'

        os.environ['MLSDK'] = str(mlsdkPath)

    if os.environ.get('MLSDK', None) is None:
        return 'MLSDK environment variable has not been set.'

    _mldb = None

    try:
        _mldb = mldb.MLDB()
    except Exception as err:
        return err.message

    deviceList = _mldb.fetch_devices()

    if not deviceList['devices']:
        return 'No connected device found.'

    _mldb.device_id = deviceList['devices'][0]

    if not _mldb.is_app_running(constants.PREVIEWER_PACKAGE_ID):
        _mldb.run_launch(constants.PREVIEWER_PACKAGE_ID)

    device_ip = _mldb.fetch_device_ip()

    executable = utils.getAssetPreviewer()

    settingsData = getIconSettings()
    iconDirectory = getIconDirectory()
    modelFolder = os.path.basename(iconDirectory) + '/Model'
    portalFolder = os.path.basename(iconDirectory) + '/Portal'

    sendIconCmd = [
        executable,
        'send-icon',
        '--name', 'Icon',
        '--view', 'detail',
        '--manifest-model-folder', modelFolder,
        '--manifest-portal-folder', portalFolder,
        '--zip-model-folder', 'Model',
        '--zip-portal-folder', 'Portal',
        '--device-ip', device_ip,
        # FUTURE: Update the asset-previewer cli, the this is using
        # a prelease where the default port is set to 8080 which errors.
        '--port', '9400',
        '"{0}"'.format(str(iconZipPath))
    ]

    try:
        cmd = ' '.join(sendIconCmd)
        LOG.info('Attempting command: %s', cmd)
        LOG.info(os.environ)
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True, env=os.environ)
        LOG.info(output)
        result = ''
    except Exception as err:
        raise err
        # e = str(err.output)
        # output = e.split('\n')
        # for line in output:
        #     LOG.error(line)
        # result = err.output

    return result


def checkForAnimatedTransforms(node, startFrame, endFrame):
    """Check for animated transforms on a node.

    Args:
        node(str): Node name.
        startFrame(int): First frame.
        endFrame(int): Last frame.

    Returns:
        bool
    """
    checked = False

    childrenNodes = getChildren(node, recursive=True, nodeType=OpenMaya.MFn.kTransform)
    childrenNodePaths = [getNodePath(child) for child in childrenNodes]

    for childNodePath in childrenNodePaths:
        for attrName in ['translate', 'rotate', 'scale']:
            kwargs = dict(query=True, time=(startFrame, endFrame), timeChange=True)
            attrPath = '{0}.{1}'.format(childNodePath, attrName)
            if cmds.keyframe(attrPath, **kwargs):
                return True

    return checked


def checkModelForAnimatedTransforms():
    """Check all transforms under the model component for animated transforms.

    Returns:
        bool
    """
    if not iconTemplateExists():
        return False

    node = getModelComponentNode()
    settingsData = getIconSettings()
    animData = settingsData.get('animationTakes', [])

    for take in animData:
        takeChecked = checkForAnimatedTransforms(node, take['startFrame'], take['endFrame'])
        if takeChecked:
            return True

    return False


def checkPortalForAnimatedTransforms():
    """Check all transforms under the portal component for animated transforms.

    Returns:
        bool
    """
    if not iconTemplateExists():
        return False

    node = getPortalComponentNode()
    settingsData = getIconSettings()
    animData = settingsData.get('animationTakes', [])

    for take in animData:
        takeChecked = checkForAnimatedTransforms(node, take['startFrame'], take['endFrame'])
        if takeChecked:
            return True

    return False


def checkAttrForKeys(nodePath, attrName, frame):
    """Check an attribute for key data.

    Args:
        nodePath(str): Node name.
        attrName(str): Attribute name.
        frame(int): Frame number.

    Return:
        bool
    """
    keys = cmds.keyframe('{0}.{1}'.format(nodePath, attrName), query=True, time=(frame, frame), timeChange=True)

    checked = False

    if keys is not None and len(keys) == 3:
        checked = True

    return checked


def checkTRSForKeys(nodePath, frame):
    """Check node for keys.

    Args:
        nodePath(str): Node name.
        frame(int): Frame number.
    
    Returns:
        bool
    """
    checked = False
    for attrName in ['translate', 'rotate', 'scale']:
        checked = checkAttrForKeys(nodePath, attrName, frame)
        if not checked:
            break

    return checked


def checkTakeForAnimation(startFrame, endFrame):
    """Check to make sure animation clip has a start and end keyframe.
    
    Args:
        startFrame(int): First frame.
        endFrame(int): Last frame.
    
    Returns:
        bool
    """
    checked = False

    if not iconTemplateExists():
        return checked

    node = getModelComponentNode()
    childrenNodes = getChildren(node, recursive=True, nodeType=OpenMaya.MFn.kJoint)
    childrenNodePaths = [getNodePath(child) for child in childrenNodes]

    for childNodePath in childrenNodePaths:
        startChecked = checkTRSForKeys(childNodePath, startFrame)
        endChecked = checkTRSForKeys(childNodePath, endFrame)
        if endChecked and startChecked:
            checked = True
        else:
            checked = False
            break

    return checked
