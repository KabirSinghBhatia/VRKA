pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import ".."

Rectangle {
    id: root

    property string title: ""
    property string description: ""
    default property alias content: controlSlot.children

    implicitHeight: Math.max(54, rowLayout.implicitHeight + 16)
    Layout.fillWidth: true
    radius: Theme.controlRadius
    color: Theme.cardAlt
    border.width: 1
    border.color: Theme.border

    RowLayout {
        id: rowLayout
        anchors.fill: parent
        anchors.leftMargin: 14
        anchors.rightMargin: 14
        spacing: 12

        ColumnLayout {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignVCenter
            spacing: 2

            Label {
                text: root.title
                font.family: Theme.fontFamily
                font.pixelSize: Theme.bodySize
                font.bold: true
                color: Theme.text
                elide: Text.ElideRight
            }

            Label {
                visible: root.description !== ""
                text: root.description
                font.family: Theme.fontFamily
                font.pixelSize: Theme.smallSize
                color: Theme.textDim
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
        }

        Item {
            id: controlSlot
            Layout.alignment: Qt.AlignVCenter
            implicitWidth: childrenRect.width
            implicitHeight: childrenRect.height
        }
    }
}
