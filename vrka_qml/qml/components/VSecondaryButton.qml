pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import ".."

Button {
    id: root

    property string iconName: ""

    implicitWidth: Math.max(76, contentRow.implicitWidth + 24)
    implicitHeight: Theme.secondaryButtonHeight
    hoverEnabled: true
    focusPolicy: Qt.StrongFocus
    font.family: Theme.fontFamily
    font.pixelSize: Theme.smallSize
    font.bold: true

    background: Rectangle {
        radius: Theme.controlRadius
        color: !root.enabled ? Theme.surfaceElevated
             : root.down ? Theme.surfaceHover
             : root.hovered ? Theme.surfaceElevated
             : Theme.cardAlt
        border.width: root.visualFocus ? 2 : 1
        border.color: root.visualFocus ? Theme.focusRing : (root.hovered ? Theme.borderStrong : Theme.border)
        opacity: root.enabled ? 1.0 : 0.45

        Behavior on color {
            ColorAnimation { duration: 120 }
        }
    }

    contentItem: Item {
        anchors.fill: parent

        RowLayout {
            id: contentRow
            anchors.centerIn: parent
            spacing: 6

            Image {
                visible: root.iconName !== ""
                source: root.iconName !== "" ? Qt.resolvedUrl("../../../assets/branding/v2icons/" + root.iconName + "-" + (Theme.isLight ? "lightMuted" : "muted") + "-32.png") : ""
                Layout.preferredWidth: 14
                Layout.preferredHeight: 14
                Layout.alignment: Qt.AlignVCenter
                fillMode: Image.PreserveAspectFit
                mipmap: true
            }

            Text {
                text: root.text
                font: root.font
                color: root.enabled ? Theme.text : Theme.textDisabled
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                Layout.alignment: Qt.AlignVCenter
            }
        }
    }
}
