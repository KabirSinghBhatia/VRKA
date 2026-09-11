pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import QtQuick.Effects
import ".."

Button {
    id: root

    property string iconName: ""

    implicitWidth: Math.max(88, contentRow.implicitWidth + 28)
    implicitHeight: Theme.primaryButtonHeight
    hoverEnabled: true
    focusPolicy: Qt.StrongFocus
    font.family: Theme.fontFamily
    font.pixelSize: Theme.bodySize
    font.bold: true

    background: Rectangle {
        radius: Theme.controlRadius
        color: !root.enabled ? Theme.surfaceElevated
             : root.down ? Theme.accentPressed
             : root.hovered ? Theme.accentHover
             : Theme.accent
        opacity: root.enabled ? 1.0 : 0.45
        border.width: root.visualFocus ? 2 : 0
        border.color: Theme.focusRing

        Behavior on color {
            ColorAnimation { duration: 120 }
        }
    }

    contentItem: Item {
        anchors.fill: parent

        RowLayout {
            id: contentRow
            anchors.centerIn: parent
            spacing: 8

            Item {
                visible: root.iconName !== ""
                Layout.preferredWidth: 16
                Layout.preferredHeight: 16
                Layout.alignment: Qt.AlignVCenter

                Image {
                    id: btnRawIcon
                    anchors.fill: parent
                    source: root.iconName !== "" ? Qt.resolvedUrl("../../../assets/branding/v2icons/" + root.iconName + "-accent-32.png") : ""
                    fillMode: Image.PreserveAspectFit
                    mipmap: true
                    visible: false
                }

                MultiEffect {
                    anchors.fill: btnRawIcon
                    source: btnRawIcon
                    colorization: 1.0
                    colorizationColor: Theme.textOnAccent
                    brightness: 1.0
                    opacity: root.enabled ? 1.0 : 0.6
                }
            }

            Text {
                text: root.text
                font: root.font
                color: root.enabled ? Theme.textOnAccent : Theme.textDisabled
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                Layout.alignment: Qt.AlignVCenter
            }
        }
    }
}
