pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import QtQuick.Window
import ".."

Rectangle {
    id: root

    required property Window targetWindow

    height: Theme.titleBarHeight
    color: Theme.titleBarBg

    RowLayout {
        anchors.fill: parent
        spacing: 0

        // Left Branding (Small Icon + Title VRKA)
        Item {
            Layout.preferredHeight: Theme.titleBarHeight
            Layout.preferredWidth: titleRow.implicitWidth + 24

            RowLayout {
                id: titleRow
                anchors.left: parent.left
                anchors.leftMargin: 12
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

        // Center Draggable Region (Native Windows System Move & Double-Click Maximize)
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

        // Right Window Control Buttons (Minimize, Maximize/Restore, Close)
        RowLayout {
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
