import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import QtQuick.Effects
import ".."

Rectangle {
    id: root

    property int selectedIndex: 0
    property var options: ["Video", "Audio"]
    property var icons: ["play", "music"]
    signal optionSelected(int index)

    implicitWidth: 240
    implicitHeight: Theme.controlHeight
    radius: Theme.controlRadius
    color: Theme.cardAlt
    border.width: 1
    border.color: Theme.border

    RowLayout {
        anchors.fill: parent
        anchors.margins: 3
        spacing: 4

        Repeater {
            model: root.options

            delegate: AbstractButton {
                id: segBtn
                required property int index
                required property string modelData

                Layout.fillWidth: true
                Layout.fillHeight: true
                hoverEnabled: true

                background: Rectangle {
                    radius: Theme.controlRadius - 2
                    color: root.selectedIndex === segBtn.index ? Theme.accent
                         : segBtn.hovered ? Theme.surfaceElevated
                         : "transparent"

                    Behavior on color {
                        ColorAnimation { duration: 100 }
                    }
                }

                contentItem: Item {
                    anchors.fill: parent

                    RowLayout {
                        anchors.centerIn: parent
                        spacing: 8

                        Item {
                            Layout.preferredWidth: 14
                            Layout.preferredHeight: 14
                            Layout.alignment: Qt.AlignVCenter

                            Image {
                                id: segIcon
                                anchors.fill: parent
                                source: {
                                    var icon = (root.icons && root.icons.length > segBtn.index) ? root.icons[segBtn.index] : (segBtn.index === 0 ? "play" : "music")
                                    return Qt.resolvedUrl("../../../assets/branding/v2icons/" + icon + "-accent-32.png")
                                }
                                fillMode: Image.PreserveAspectFit
                                mipmap: true
                                visible: false
                            }

                            MultiEffect {
                                anchors.fill: segIcon
                                source: segIcon
                                colorization: root.selectedIndex === segBtn.index ? 1.0 : 0.0
                                colorizationColor: "#FFFFFF"
                                brightness: root.selectedIndex === segBtn.index ? 1.0 : 0.0
                                opacity: root.selectedIndex === segBtn.index ? 1.0 : 0.65
                            }
                        }

                        Text {
                            text: segBtn.modelData
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.bodySize
                            font.bold: root.selectedIndex === segBtn.index
                            color: root.selectedIndex === segBtn.index ? Theme.textOnAccent : Theme.text
                            verticalAlignment: Text.AlignVCenter
                            Layout.alignment: Qt.AlignVCenter
                        }
                    }
                }

                onClicked: {
                    root.selectedIndex = segBtn.index
                    root.optionSelected(segBtn.index)
                }
            }
        }
    }
}
