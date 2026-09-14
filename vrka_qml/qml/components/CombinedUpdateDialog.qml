pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import ".."

Item {
    id: root

    property var updatesList: []
    signal updateRequested()
    signal dismissRequested()

    anchors.fill: parent
    z: 999

    // Dimmed Backdrop
    Rectangle {
        anchors.fill: parent
        color: Qt.rgba(0, 0, 0, 0.45)

        MouseArea {
            anchors.fill: parent
            onClicked: root.dismissRequested()
        }
    }

    // Modal Card
    Rectangle {
        id: dialogCard
        anchors.centerIn: parent
        width: Math.min(520, parent.width - 40)
        implicitHeight: dialogContent.implicitHeight + 36
        radius: Theme.cardRadius
        color: Theme.card
        border.width: 1
        border.color: Theme.borderStrong
        clip: true

        // Intercept clicks on the card
        MouseArea {
            anchors.fill: parent
            onClicked: {}
        }

        ColumnLayout {
            id: dialogContent
            anchors.fill: parent
            anchors.margins: 20
            spacing: 16

            // Header
            RowLayout {
                Layout.fillWidth: true
                spacing: 12

                Rectangle {
                    width: 36
                    height: 36
                    radius: 8
                    color: Theme.accentSoft
                    border.width: 1
                    border.color: Theme.accent

                    Image {
                        anchors.centerIn: parent
                        width: 20
                        height: 20
                        source: Qt.resolvedUrl("../../../assets/branding/v2icons/gear-accent-32.png")
                        fillMode: Image.PreserveAspectFit
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2

                    Label {
                        text: "Component Updates Available"
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.sectionTitleSize
                        font.bold: true
                        color: Theme.text
                    }

                    Label {
                        text: "Official updates are available for your desktop runtime components."
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.microSize
                        color: Theme.textDim
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                }
            }

            // Updates List
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 8

                Repeater {
                    model: root.updatesList

                    delegate: Rectangle {
                        required property var modelData
                        Layout.fillWidth: true
                        implicitHeight: compRow.implicitHeight + 16
                        radius: Theme.controlRadius
                        color: Theme.cardAlt
                        border.width: 1
                        border.color: Theme.border

                        RowLayout {
                            id: compRow
                            anchors.fill: parent
                            anchors.margins: 10
                            spacing: 12

                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 2

                                Label {
                                    text: modelData.display_name || modelData.name || "Component"
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.bodySize
                                    font.bold: true
                                    color: Theme.text
                                }

                                RowLayout {
                                    spacing: 8
                                    Label {
                                        text: "Installed: " + (modelData.current_version || "Unknown")
                                        font.family: Theme.fontFamily
                                        font.pixelSize: Theme.microSize
                                        color: Theme.textDim
                                    }
                                    Label {
                                        text: "→"
                                        font.family: Theme.fontFamily
                                        font.pixelSize: Theme.microSize
                                        color: Theme.textDim
                                    }
                                    Label {
                                        text: "Available: " + (modelData.available_version || "Latest")
                                        font.family: Theme.fontFamily
                                        font.pixelSize: Theme.microSize
                                        font.bold: true
                                        color: Theme.accentHover
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // Action Buttons
            RowLayout {
                Layout.fillWidth: true
                spacing: 10

                Item { Layout.fillWidth: true }

                VSecondaryButton {
                    text: "Later"
                    Layout.preferredHeight: 36
                    Layout.preferredWidth: 90
                    onClicked: root.dismissRequested()
                }

                VPrimaryButton {
                    text: "Update Now"
                    Layout.preferredHeight: 36
                    Layout.preferredWidth: 120
                    onClicked: root.updateRequested()
                }
            }
        }
    }
}
