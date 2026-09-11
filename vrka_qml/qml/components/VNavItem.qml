pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import ".."

AbstractButton {
    id: root

    property alias label: root.text
    property alias active: root.checked
    property alias selected: root.checked
    property string iconSource: ""
    property string iconName: ""
    property int badgeCount: 0

    implicitWidth: 196
    implicitHeight: Theme.navButtonHeight
    focusPolicy: Qt.TabFocus
    hoverEnabled: true

    background: Rectangle {
        color: "transparent"
        border.width: root.visualFocus ? 1 : 0
        border.color: Theme.focusRing

        // Small 3px vertical accent indicator (only visual indicator for active state)
        Rectangle {
            anchors.left: parent.left
            anchors.leftMargin: 2
            anchors.verticalCenter: parent.verticalCenter
            width: 3
            height: root.checked ? 18 : 0
            radius: 1.5
            color: Theme.accent
            visible: root.checked

            Behavior on height { NumberAnimation { duration: 140; easing.type: Easing.OutCubic } }
        }
    }

    contentItem: RowLayout {
        spacing: 12
        anchors.verticalCenter: parent.verticalCenter
        anchors.left: parent.left
        anchors.leftMargin: 14
        anchors.right: parent.right
        anchors.rightMargin: 10

        Image {
            Layout.preferredWidth: 16
            Layout.preferredHeight: 16
            source: {
                if (root.iconSource !== "") return root.iconSource
                var base = ""
                if (root.iconName !== "") base = root.iconName
                else if (root.text === "Download") base = "download"
                else if (root.text === "Queue") base = "list"
                else if (root.text === "History") base = "clock"
                else if (root.text === "Settings") base = "gear"
                else return ""
                var variant = root.checked ? "accent" : (root.hovered ? "accentHover" : (Theme.isLight ? "lightMuted" : "muted"))
                return Qt.resolvedUrl("../../../assets/branding/nav/" + base + "-" + variant + "-32.png")
            }
            fillMode: Image.PreserveAspectFit
            mipmap: true
            smooth: true
        }

        Text {
            Layout.fillWidth: true
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
            text: root.text
            font.family: Theme.fontFamily
            font.pixelSize: Theme.bodySize
            font.bold: root.checked
            color: root.checked ? Theme.accent : (root.hovered ? Theme.text : Theme.textMuted)
        }

        // Active Badge
        Rectangle {
            visible: root.badgeCount > 0
            implicitWidth: badgeLabel.implicitWidth + 10
            implicitHeight: 18
            radius: 9
            color: Theme.accent

            Label {
                id: badgeLabel
                anchors.centerIn: parent
                text: String(root.badgeCount)
                font.family: Theme.fontFamily
                font.pixelSize: 10
                font.bold: true
                color: Theme.textOnAccent
            }
        }
    }
}
