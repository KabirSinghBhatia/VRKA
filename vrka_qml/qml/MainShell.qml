pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import QtQuick.Window
import "."
import "components"
import "pages"

ApplicationWindow {
    id: shell

    property int currentPageIndex: 0

    function setDarkMode(dark) {
        Theme.mode = dark ? "dark" : "light"
    }

    width: 1240
    height: 820
    minimumWidth: 1020
    minimumHeight: 700
    visible: true
    title: "VRKA"
    color: (shell.visibility === Window.Maximized || shell.width >= 1900) ? Theme.bg : "transparent"
    flags: Qt.Window | Qt.FramelessWindowHint | Qt.WindowMinMaxButtonsHint

    // Outer Container for Application Shell
    Rectangle {
        id: appRoot
        anchors.fill: parent
        radius: (shell.visibility === Window.Maximized || shell.width >= 1900) ? 0 : Theme.cardRadius
        clip: true
        color: Theme.bg
        border.width: (shell.visibility === Window.Maximized || shell.width >= 1900) ? 0 : Theme.hairline
        border.color: (shell.visibility === Window.Maximized || shell.width >= 1900) ? "transparent" : Theme.borderStrong

        // Top Integrated Custom Windows Title Bar
        VTitleBar {
            id: customTitleBar
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            targetWindow: shell
            z: 100
        }

        // Main App Shell Body (Sidebar + Content Canvas)
        Item {
            id: shellBody
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: customTitleBar.bottom
            anchors.bottom: parent.bottom

            // Left Navigation Sidebar (Floating Neutral Island)
            Rectangle {
                id: sidebar
                objectName: "sidebar"
                anchors.left: parent.left
                anchors.leftMargin: 12
                anchors.top: parent.top
                anchors.topMargin: 8
                anchors.bottom: parent.bottom
                anchors.bottomMargin: 12
                width: Theme.sidebarWidth
                radius: Theme.sidebarRadius
                color: Theme.sidebarBg
                border.width: 1
                border.color: Theme.sidebarBorder
                clip: true

                ColumnLayout {
                    anchors.fill: parent
                    spacing: 0

                    // Brand Header Lockup (Compact Wolf + Title)
                    Item {
                        Layout.fillWidth: true
                        implicitHeight: 70

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 16
                            anchors.rightMargin: 16
                            anchors.topMargin: 12
                            anchors.bottomMargin: 8
                            spacing: 10

                            Image {
                                source: Qt.resolvedUrl("../../assets/branding/vrka-wolf-256.png")
                                Layout.preferredWidth: 42
                                Layout.preferredHeight: 42
                                Layout.alignment: Qt.AlignVCenter
                                fillMode: Image.PreserveAspectFit
                                mipmap: true
                            }

                            ColumnLayout {
                                spacing: 0
                                Layout.alignment: Qt.AlignVCenter

                                Label {
                                    text: "VRKA"
                                    font.family: Theme.fontFamily
                                    font.pixelSize: 20
                                    font.bold: true
                                    color: Theme.text
                                }

                                Label {
                                    text: "v" + APP_DISPLAY_VERSION
                                    font.family: Theme.fontFamily
                                    font.pixelSize: 11
                                    font.bold: true
                                    color: Theme.textDim
                                }
                            }

                            Item { Layout.fillWidth: true }
                        }
                    }

                    // Hairline separator below branding
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.leftMargin: 14
                        Layout.rightMargin: 14
                        implicitHeight: Theme.hairline
                        color: Theme.border
                    }

                    // Navigation Section
                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.leftMargin: 12
                        Layout.rightMargin: 12
                        Layout.topMargin: 12
                        spacing: 4

                        Label {
                            text: "NAVIGATION"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.microSize
                            font.bold: true
                            color: Theme.textDim
                            Layout.leftMargin: 8
                            Layout.bottomMargin: 4
                        }

                        VNavItem {
                            Layout.fillWidth: true
                            text: "Download"
                            iconName: "download"
                            selected: shell.currentPageIndex === 0
                            onClicked: shell.currentPageIndex = 0
                        }

                        VNavItem {
                            Layout.fillWidth: true
                            text: "Queue"
                            iconName: "list"
                            badgeCount: Bridge.activeCount
                            selected: shell.currentPageIndex === 1
                            onClicked: shell.currentPageIndex = 1
                        }

                        VNavItem {
                            Layout.fillWidth: true
                            text: "History"
                            iconName: "clock"
                            selected: shell.currentPageIndex === 2
                            onClicked: shell.currentPageIndex = 2
                        }

                        VNavItem {
                            Layout.fillWidth: true
                            text: "Settings"
                            iconName: "gear"
                            selected: shell.currentPageIndex === 3
                            onClicked: shell.currentPageIndex = 3
                        }
                    }

                    Item { Layout.fillHeight: true }

                    // DAY MODE / NIGHT MODE Capsule Toggle (Above Uplink Console)
                    AbstractButton {
                        id: themeToggle
                        Layout.alignment: Qt.AlignHCenter
                        Layout.preferredWidth: 124
                        Layout.preferredHeight: 34
                        Layout.bottomMargin: 10
                        hoverEnabled: true
                        onClicked: Theme.mode = Theme.isLight ? "dark" : "light"

                        background: Rectangle {
                            id: pillBg
                            radius: parent.height / 2
                            color: Theme.isLight ? (themeToggle.down ? "#DADDE6" : themeToggle.hovered ? "#E4E7EE" : "#ECEEF4")
                                                 : (themeToggle.down ? "#050508" : themeToggle.hovered ? "#16161E" : "#0D0D12")
                            border.width: 1
                            border.color: Theme.isLight ? (themeToggle.hovered ? "#A8ADC0" : "#C4C8D8")
                                                        : (themeToggle.hovered ? "#444458" : "#282836")

                            Rectangle {
                                anchors.fill: parent
                                radius: parent.radius
                                color: Theme.accent
                                opacity: themeToggle.hovered ? 0.08 : 0.0
                            }
                        }

                        contentItem: Item {
                            anchors.fill: parent

                            Rectangle {
                                id: circleBadge
                                width: 28
                                height: 28
                                radius: 14
                                x: Theme.isLight ? 93 : 3
                                y: 3
                                color: Theme.isLight ? "#FFFFFF" : "#1C1C26"
                                border.width: 1
                                border.color: Theme.isLight ? "#C8CBD8" : "#38384C"

                                Behavior on x {
                                    NumberAnimation { duration: 150; easing.type: Easing.OutCubic }
                                }

                                Image {
                                    anchors.centerIn: parent
                                    width: 15
                                    height: 15
                                    source: Theme.isLight ? Qt.resolvedUrl("../../assets/branding/v2icons/sun-lightMuted-32.png")
                                                          : Qt.resolvedUrl("../../assets/branding/v2icons/moon-lightMuted-32.png")
                                    fillMode: Image.PreserveAspectFit
                                    mipmap: true
                                }
                            }

                            Text {
                                x: Theme.isLight ? 6 : 34
                                y: 0
                                width: 86
                                height: 34
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                                text: Theme.isLight ? "LIGHT MODE" : "DARK MODE"
                                font.family: Theme.fontFamily
                                font.pixelSize: 10
                                font.bold: true
                                color: Theme.isLight ? "#111116" : "#FFFFFF"
                            }
                        }
                    }

                    // Authoritative UPLINK Status Console (Anchored at Very Bottom)
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.leftMargin: 12
                        Layout.rightMargin: 12
                        Layout.bottomMargin: 12
                        implicitHeight: footerCol.implicitHeight + 18
                        radius: Theme.controlRadius
                        color: Theme.card
                        border.width: 1
                        border.color: Theme.border

                        ColumnLayout {
                            id: footerCol
                            anchors.fill: parent
                            anchors.margins: 10
                            spacing: 8

                            // Engine Status Row (READY=green #2BCB77, ACTIVE=purple #9255E5, QUEUED=yellow #E7A93D)
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 8

                                Rectangle {
                                    width: 8
                                    height: 8
                                    radius: 4
                                    color: Bridge.activeCount > 0 ? Theme.accentHover : (Bridge.queuedCount > 0 ? Theme.warning : Theme.success)
                                }

                                Label {
                                    text: Bridge.activeCount > 0 ? "UPLINK ACTIVE" : (Bridge.queuedCount > 0 ? "UPLINK QUEUED" : "UPLINK READY")
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.microSize
                                    font.bold: true
                                    color: Bridge.activeCount > 0 ? Theme.accentHover : (Bridge.queuedCount > 0 ? Theme.warning : Theme.success)
                                }

                                Item { Layout.fillWidth: true }
                            }

                            // Hairline divider
                            Rectangle {
                                Layout.fillWidth: true
                                implicitHeight: Theme.hairline
                                color: Theme.border
                            }

                            // Symmetrical 2x2 Metrics Grid (Equal Column Widths, Aligned Labels & Values)
                            GridLayout {
                                Layout.fillWidth: true
                                columns: 2
                                columnSpacing: 14
                                rowSpacing: 6

                                RowLayout {
                                    Layout.fillWidth: true
                                    Layout.preferredWidth: 0
                                    spacing: 4
                                    Label {
                                        text: "QUEUED"
                                        font.family: Theme.fontFamily
                                        font.pixelSize: Theme.microSize
                                        font.bold: true
                                        color: Bridge.queuedCount > 0 ? Theme.warning : Theme.textDim
                                    }
                                    Item { Layout.fillWidth: true }
                                    Label {
                                        text: String(Bridge.queuedCount).padStart(2, "0")
                                        font.family: Theme.fontFamily
                                        font.pixelSize: Theme.smallSize
                                        font.bold: true
                                        color: Bridge.queuedCount > 0 ? Theme.warning : Theme.text
                                    }
                                }

                                RowLayout {
                                    Layout.fillWidth: true
                                    Layout.preferredWidth: 0
                                    spacing: 4
                                    Label {
                                        text: "ACTIVE"
                                        font.family: Theme.fontFamily
                                        font.pixelSize: Theme.microSize
                                        font.bold: true
                                        color: Bridge.activeCount > 0 ? Theme.accentHover : Theme.textDim
                                    }
                                    Item { Layout.fillWidth: true }
                                    Label {
                                        text: String(Bridge.activeCount).padStart(2, "0")
                                        font.family: Theme.fontFamily
                                        font.pixelSize: Theme.smallSize
                                        font.bold: true
                                        color: Bridge.activeCount > 0 ? Theme.accentHover : Theme.text
                                    }
                                }

                                RowLayout {
                                    Layout.fillWidth: true
                                    Layout.preferredWidth: 0
                                    spacing: 4
                                    Label {
                                        text: "ARCHIVED"
                                        font.family: Theme.fontFamily
                                        font.pixelSize: Theme.microSize
                                        font.bold: true
                                        color: Theme.textDim
                                    }
                                    Item { Layout.fillWidth: true }
                                    Label {
                                        text: String(Bridge.historyCount).padStart(2, "0")
                                        font.family: Theme.fontFamily
                                        font.pixelSize: Theme.smallSize
                                        font.bold: true
                                        color: Theme.text
                                    }
                                }

                                RowLayout {
                                    Layout.fillWidth: true
                                    Layout.preferredWidth: 0
                                    spacing: 4
                                    Label {
                                        text: "DONE"
                                        font.family: Theme.fontFamily
                                        font.pixelSize: Theme.microSize
                                        font.bold: true
                                        color: Theme.textDim
                                    }
                                    Item { Layout.fillWidth: true }
                                    Label {
                                        text: String(Bridge.completedCount).padStart(2, "0")
                                        font.family: Theme.fontFamily
                                        font.pixelSize: Theme.smallSize
                                        font.bold: true
                                        color: Theme.success
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // Main Content Canvas Area
            Item {
                id: mainCanvas
                anchors.left: sidebar.right
                anchors.leftMargin: 12
                anchors.right: parent.right
                anchors.rightMargin: 12
                anchors.top: parent.top
                anchors.topMargin: 8
                anchors.bottom: parent.bottom
                anchors.bottomMargin: 12

                StackLayout {
                    id: pageStack
                    anchors.fill: parent
                    anchors.margins: 12
                    currentIndex: shell.currentPageIndex

                    DownloadPage { id: downloadView }
                    QueuePage { id: queueView }
                    HistoryPage { id: historyView }
                    SettingsPage { id: settingsView }
                }
            }
        }

        // Non-blocking Startup Combined Component Update Dialog
        CombinedUpdateDialog {
            id: startupDialog
            visible: typeof Operational !== "undefined" && Operational && Operational.startupDialogVisible
            updatesList: (typeof Operational !== "undefined" && Operational) ? Operational.startupUpdates : []
            onUpdateRequested: {
                if (typeof Operational !== "undefined" && Operational) {
                    Operational.acceptStartupDialog()
                }
            }
            onDismissRequested: {
                if (typeof Operational !== "undefined" && Operational) {
                    Operational.dismissStartupDialog()
                }
            }
        }
    }

    // Native Window Edge & Corner Resize Handles
    MouseArea {
        visible: shell.visibility !== Window.Maximized
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: 6
        cursorShape: Qt.SizeHorCursor
        acceptedButtons: Qt.LeftButton
        onPressed: if (shell.visibility !== Window.Maximized) shell.startSystemResize(Qt.LeftEdge)
    }

    MouseArea {
        visible: shell.visibility !== Window.Maximized
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: 6
        cursorShape: Qt.SizeHorCursor
        acceptedButtons: Qt.LeftButton
        onPressed: if (shell.visibility !== Window.Maximized) shell.startSystemResize(Qt.RightEdge)
    }

    MouseArea {
        visible: shell.visibility !== Window.Maximized
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        height: 6
        cursorShape: Qt.SizeVerCursor
        acceptedButtons: Qt.LeftButton
        onPressed: if (shell.visibility !== Window.Maximized) shell.startSystemResize(Qt.BottomEdge)
    }

    MouseArea {
        visible: shell.visibility !== Window.Maximized
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        width: 10
        height: 10
        cursorShape: Qt.SizeFDiagCursor
        acceptedButtons: Qt.LeftButton
        onPressed: if (shell.visibility !== Window.Maximized) shell.startSystemResize(Qt.RightEdge | Qt.BottomEdge)
    }

    MouseArea {
        visible: shell.visibility !== Window.Maximized
        anchors.left: parent.left
        anchors.bottom: parent.bottom
        width: 10
        height: 10
        cursorShape: Qt.SizeBDiagCursor
        acceptedButtons: Qt.LeftButton
        onPressed: if (shell.visibility !== Window.Maximized) shell.startSystemResize(Qt.LeftEdge | Qt.BottomEdge)
    }
}
