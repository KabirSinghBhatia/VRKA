pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import QtQuick.Window
import ".."

Rectangle {
    id: root

    required property Window targetWindow
    readonly property bool isMac: Qt.platform.os === "osx" || Qt.platform.os === "macos"

    height: Theme.titleBarHeight
    color: Theme.titleBarBg

    RowLayout {
        anchors.fill: parent
        spacing: 0

        // macOS Traffic Light Window Controls (Close, Minimize, Zoom) on the Left
        Item {
            visible: root.isMac
            Layout.preferredHeight: Theme.titleBarHeight
            Layout.preferredWidth: visible ? (macTrafficRow.implicitWidth + 24) : 0

            RowLayout {
                id: macTrafficRow
                anchors.left: parent.left
                anchors.leftMargin: 14
                anchors.verticalCenter: parent.verticalCenter
                spacing: 8

                property bool groupHovered: macCloseBtn.hovered || macMinBtn.hovered || macZoomBtn.hovered

                // Close (Red)
                AbstractButton {
                    id: macCloseBtn
                    Layout.preferredWidth: 12
                    Layout.preferredHeight: 12
                    hoverEnabled: true
                    onClicked: {
                        if (root.targetWindow) root.targetWindow.close()
                    }

                    background: Rectangle {
                        width: 12
                        height: 12
                        radius: 6
                        color: macCloseBtn.down ? "#BF3E38" : macCloseBtn.hovered ? "#E0443E" : "#FF5F56"
                        border.width: 0.5
                        border.color: "#D0413B"

                        Text {
                            anchors.centerIn: parent
                            visible: macTrafficRow.groupHovered
                            text: "\u2715"
                            font.pixelSize: 8
                            font.bold: true
                            color: "#4A0000"
                        }
                    }
                }

                // Minimize (Amber)
                AbstractButton {
                    id: macMinBtn
                    Layout.preferredWidth: 12
                    Layout.preferredHeight: 12
                    hoverEnabled: true
                    onClicked: {
                        if (root.targetWindow) root.targetWindow.showMinimized()
                    }

                    background: Rectangle {
                        width: 12
                        height: 12
                        radius: 6
                        color: macMinBtn.down ? "#BF8E1F" : macMinBtn.hovered ? "#DEA123" : "#FFBD2E"
                        border.width: 0.5
                        border.color: "#D89E24"

                        Rectangle {
                            anchors.centerIn: parent
                            visible: macTrafficRow.groupHovered
                            width: 6
                            height: 1
                            color: "#5C3E00"
                        }
                    }
                }

                // Zoom / Fullscreen (Green)
                AbstractButton {
                    id: macZoomBtn
                    Layout.preferredWidth: 12
                    Layout.preferredHeight: 12
                    hoverEnabled: true
                    readonly property bool isMaximized: root.targetWindow && root.targetWindow.visibility === Window.Maximized
                    onClicked: {
                        if (!root.targetWindow) return
                        if (isMaximized) {
                            root.targetWindow.showNormal()
                        } else {
                            root.targetWindow.showMaximized()
                        }
                    }

                    background: Rectangle {
                        width: 12
                        height: 12
                        radius: 6
                        color: macZoomBtn.down ? "#1F992E" : macZoomBtn.hovered ? "#1AAB29" : "#27C93F"
                        border.width: 0.5
                        border.color: "#1EA032"

                        Text {
                            anchors.centerIn: parent
                            visible: macTrafficRow.groupHovered
                            text: "+"
                            font.pixelSize: 9
                            font.bold: true
                            color: "#0B4710"
                        }
                    }
                }
            }
        }

        // Branding (Small Icon + Title VRKA)
        Item {
            Layout.preferredHeight: Theme.titleBarHeight
            Layout.preferredWidth: titleRow.implicitWidth + 20

            RowLayout {
                id: titleRow
                anchors.left: parent.left
                anchors.leftMargin: root.isMac ? 4 : 12
                anchors.verticalCenter: parent.verticalCenter
                spacing: 8

                Image {
                    source: Qt.resolvedUrl("../../../assets/branding/vrka-wolf-16.png")
                    Layout.preferredWidth: 16
                    Layout.preferredHeight: 16
                    Layout.alignment: Qt.AlignVCenter
                    fillMode: Image.PreserveAspectFit
                    mipmap: true
                }

                Label {
                    text: "VRKA"
                    font.family: Theme.fontFamily
                    font.pixelSize: 12
                    font.bold: true
                    color: Theme.text
                    Layout.alignment: Qt.AlignVCenter
                }
            }

            MouseArea {
                anchors.fill: parent
                acceptedButtons: Qt.LeftButton
                onPressed: (mouse) => {
                    if (mouse.button === Qt.LeftButton && root.targetWindow) {
                        root.targetWindow.startSystemMove()
                    }
                }
                onDoubleClicked: (mouse) => {
                    if (mouse.button === Qt.LeftButton && root.targetWindow) {
                        if (root.targetWindow.visibility === Window.Maximized) {
                            root.targetWindow.showNormal()
                        } else {
                            root.targetWindow.showMaximized()
                        }
                    }
                }
            }
        }

        // Center Draggable Region (Native System Move & Double-Click Maximize)
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            MouseArea {
                anchors.fill: parent
                acceptedButtons: Qt.LeftButton

                onPressed: (mouse) => {
                    if (mouse.button === Qt.LeftButton && root.targetWindow) {
                        root.targetWindow.startSystemMove()
                    }
                }

                onDoubleClicked: (mouse) => {
                    if (mouse.button === Qt.LeftButton && root.targetWindow) {
                        if (root.targetWindow.visibility === Window.Maximized) {
                            root.targetWindow.showNormal()
                        } else {
                            root.targetWindow.showMaximized()
                        }
                    }
                }
            }
        }

        // Right spacer on macOS to visually balance top-left traffic lights
        Item {
            visible: root.isMac
            Layout.preferredHeight: Theme.titleBarHeight
            Layout.preferredWidth: visible ? 70 : 0
        }

        // Right Window Control Buttons for Windows (Minimize, Maximize/Restore, Close)
        RowLayout {
            visible: !root.isMac
            Layout.preferredHeight: Theme.titleBarHeight
            spacing: 0

            // Minimize Button
            AbstractButton {
                id: minBtn
                Layout.preferredWidth: 46
                Layout.fillHeight: true
                hoverEnabled: true

                onClicked: {
                    if (root.targetWindow) root.targetWindow.showMinimized()
                }

                background: Rectangle {
                    color: minBtn.down ? Theme.surfaceElevated
                         : minBtn.hovered ? Theme.surfaceHover : "transparent"
                }

                contentItem: Item {
                    Rectangle {
                        anchors.centerIn: parent
                        width: 10
                        height: 1
                        color: Theme.text
                    }
                }
            }

            // Maximize / Restore Button
            AbstractButton {
                id: maxBtn
                Layout.preferredWidth: 46
                Layout.fillHeight: true
                hoverEnabled: true

                readonly property bool isMaximized: root.targetWindow && root.targetWindow.visibility === Window.Maximized

                onClicked: {
                    if (!root.targetWindow) return
                    if (isMaximized) {
                        root.targetWindow.showNormal()
                    } else {
                        root.targetWindow.showMaximized()
                    }
                }

                background: Rectangle {
                    color: maxBtn.down ? Theme.surfaceElevated
                         : maxBtn.hovered ? Theme.surfaceHover : "transparent"
                }

                contentItem: Item {
                    // Single rectangle when windowed; overlapping rectangles when maximized
                    Rectangle {
                        visible: !maxBtn.isMaximized
                        anchors.centerIn: parent
                        width: 10
                        height: 10
                        color: "transparent"
                        border.width: 1
                        border.color: Theme.text
                    }

                    Item {
                        visible: maxBtn.isMaximized
                        anchors.centerIn: parent
                        width: 12
                        height: 12

                        Rectangle {
                            x: 3
                            y: 0
                            width: 8
                            height: 8
                            color: "transparent"
                            border.width: 1
                            border.color: Theme.text
                        }

                        Rectangle {
                            x: 0
                            y: 3
                            width: 8
                            height: 8
                            color: Theme.titleBarBg
                            border.width: 1
                            border.color: Theme.text
                        }
                    }
                }
            }

            // Close Button
            AbstractButton {
                id: closeBtn
                Layout.preferredWidth: 46
                Layout.fillHeight: true
                hoverEnabled: true

                onClicked: {
                    if (root.targetWindow) root.targetWindow.close()
                }

                background: Rectangle {
                    color: closeBtn.down ? "#C42B1C"
                         : closeBtn.hovered ? "#E81123" : "transparent"
                }

                contentItem: Item {
                    Text {
                        anchors.centerIn: parent
                        text: "\u2715"
                        font.family: "Segoe UI, sans-serif"
                        font.pixelSize: 10
                        color: closeBtn.hovered ? "#FFFFFF" : Theme.text
                    }
                }
            }
        }
    }
}
