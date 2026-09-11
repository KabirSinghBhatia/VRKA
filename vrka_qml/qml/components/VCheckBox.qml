pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import ".."

CheckBox {
    id: root

    implicitHeight: Math.max(28, labelText.implicitHeight)
    implicitWidth: indicatorBox.width + 10 + labelText.implicitWidth
    hoverEnabled: true
    focusPolicy: Qt.StrongFocus
    font.family: Theme.fontFamily
    font.pixelSize: Theme.bodySize

    indicator: Rectangle {
        id: indicatorBox
        x: 0
        anchors.verticalCenter: parent.verticalCenter
        width: 18
        height: 18
        radius: 4
        color: root.checked ? Theme.accent : (root.hovered ? Theme.surfaceHover : Theme.cardAlt)
        border.width: root.visualFocus ? 2 : 1
        border.color: root.visualFocus ? Theme.focusRing
                    : root.checked ? Theme.accent
                    : (root.hovered ? Theme.borderStrong : Theme.border)

        Behavior on color {
            ColorAnimation { duration: 100 }
        }

        Text {
            anchors.centerIn: parent
            visible: root.checked
            text: "\u2713"
            font.family: "Segoe UI, sans-serif"
            font.pixelSize: 11
            font.bold: true
            color: Theme.textOnAccent
        }
    }

    contentItem: Text {
        id: labelText
        leftPadding: indicatorBox.width + 10
        anchors.verticalCenter: parent.verticalCenter
        text: root.text
        font: root.font
        color: !root.enabled ? Theme.textDisabled : (root.hovered ? Theme.text : Theme.text)
        verticalAlignment: Text.AlignVCenter
    }
}
