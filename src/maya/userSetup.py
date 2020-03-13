"""userSetup module sets the initial Maya environment up on startup.
"""

# maya imports
import maya.utils
import pymel.core

# constants
HELP_URL = 'https://creator.magicleap.com/learn/guides/maya-portal-icon-guide'

MAYA_UI_ROOT = 'MayaWindow'

ICON_NEW_CMD = 'from icon_creation import view;view.newIcon();'
ICON_EXPORTER_CMD = 'from icon_creation import view;view.PortalIconTool.run();'

HELP_CMD = 'import webbrowser;webbrowser.open_new_tab("{0}");'.format(HELP_URL)


def setup_menu():
    """Adds the `Portal Icon` submenu to the `Magic Leap` menu.
    """
    mlMenu = pymel.core.menu(parent=MAYA_UI_ROOT, label='Magic Leap', tearOff=True)
    portalIconItem = pymel.core.menuItem(parent=mlMenu, label='Portal Icon', subMenu=True)

    pymel.core.menuItem(
        parent=portalIconItem,
        label='Create New Portal Icon..',
        command=ICON_NEW_CMD
    )

    pymel.core.menuItem(
        parent=portalIconItem,
        label='Open Portal Icon Settings..',
        command=ICON_EXPORTER_CMD
    )

    pymel.core.menuItem(parent=portalIconItem, label='Help', command=HELP_CMD)


def main():
    """Main entrypoint for running the userSetup scripts.
    """
    setup_menu()


maya.utils.executeDeferred(main)
