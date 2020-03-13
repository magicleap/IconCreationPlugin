# variables
MODULE_SCRIPTS_PATH=${MAYA_MODULE_PATH}/${PROJECT_NAME}/scripts
MODULE_DATA_PATH=${MAYA_MODULE_PATH}/${PROJECT_NAME}/data
MAYA_SRC_PATH=${WORKSPACE}/src/maya

# Create Maya modules directory
mkdir -p ${MODULE_SCRIPTS_PATH}
mkdir -p ${MODULE_DATA_PATH}

# Copy python packages to the module scripts folder
cp -R ${MAYA_SRC_PATH}/icon_creation ${MODULE_SCRIPTS_PATH}
cp ${MAYA_SRC_PATH}/${PROJECT_NAME}.mod ${MAYA_MODULE_PATH}
cp ${MAYA_SRC_PATH}/userSetup.py ${MODULE_SCRIPTS_PATH}/userSetup.py
cp -R ${WORKSPACE}/files/models/. ${MODULE_DATA_PATH}

# Copy over tools
if [ "${PLATFORM}" == "MacOS" ]
then
    cp ${WORKSPACE}/tools/MacOS/icon-converter ${MODULE_DATA_PATH}/icon-converter
    cp ${WORKSPACE}/tools/MacOS/asset-previewer ${MODULE_DATA_PATH}/asset-previewer
elif [ "${PLATFORM}" == "Windows" ]
then
    cp ${WORKSPACE}/tools/Windows/icon-converter.exe ${MODULE_DATA_PATH}/icon-converter.exe
    cp ${WORKSPACE}/tools/Windows/asset-previewer.exe ${MODULE_DATA_PATH}/asset-previewer.exe
    cp ${WORKSPACE}/tools/Windows/assimp-vc140-mt.dll ${MODULE_DATA_PATH}/assimp-vc140-mt.dll
else
    echo "Platform is not supported. Cannot complete the build"
fi