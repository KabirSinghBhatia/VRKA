pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import QtQuick.Dialogs
import ".."
import "../components"

ScrollView {
    id: downloadScroll
    clip: true
    contentWidth: availableWidth
    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

    property string errorText: ""
    property string infoText: ""
    property string pendingUrl: ""
    property var pendingOptions: ({})

    // Responsive Spacing Tokens (Scale gracefully across 720p, 900p, 1080p, and 4K displays)
    readonly property real vH: downloadScroll.height
    readonly property int responsiveGap: Math.min(24, Math.max(10, Math.round((vH - 600) * 0.035) + 12))
    readonly property int topMarginPad: Math.min(32, Math.max(12, Math.round((vH - 600) * 0.045) + 14))
    readonly property int cardPadY: Math.min(20, Math.max(14, Math.round((vH - 600) * 0.012) + 14))
    readonly property int cardPadX: Math.min(24, Math.max(18, Math.round((downloadScroll.width - 1000) * 0.012) + 18))
    readonly property int contentMaxW: Math.min(downloadScroll.availableWidth - 56, Math.max(880, Math.min(1120, Math.round(downloadScroll.availableWidth * 0.88))))

    function currentOptions(folderOverride) {
        var isAudio = modeSegment.selectedIndex === 1;
        var opts = {
            "mode": isAudio ? "audio" : "video",
            "quality": qualityCombo.currentText,
            "fps60": fps60Check.checked,
            "audio_format": audioFormatCombo.currentText,
            "mp3_bitrate": mp3BitrateCombo.currentText,
            "download_subs": subsCheck.checked,
            "sub_langs": Settings.subLangs,
            "embed_subs": Settings.embedSubs,
            "auto_captions": Settings.autoCaptions,
            "embed_thumbnail": Settings.embedThumbnail,
            "embed_metadata": Settings.embedMetadata,
            "sponsorblock": Settings.sponsorblock,
            "output_folder": folderOverride || Settings.outputFolder,
            "referer": refererInput.text.trim(),
            "origin": originInput.text.trim(),
            "proxy": proxyInput.text.trim() || Settings.proxy,
            "force_ipv4": ipv4Check.checked || Settings.forceIpv4,
            "custom_headers": customHeadersInput.text.trim(),
            "is_playlist": playlistCheck.checked,
            "playlist_start": parseInt(playlistStartField.text.trim()) || 1,
            "playlist_end": parseInt(playlistEndField.text.trim()) || 0,
            "trim_enabled": trimCheck.checked,
            "start_time": trimCheck.checked ? trimStartField.text.trim() : "",
            "end_time": trimCheck.checked ? trimEndField.text.trim() : "",
            "use_custom_command": Settings.useCustomCommand,
            "custom_command": Settings.customCommand
        };
        return opts;
    }

    function submit() {
        var rawUrl = urlInputInner.text.trim();
        if (rawUrl === "") {
            downloadScroll.errorText = "Please enter a valid media URL to download.";
            downloadScroll.infoText = "";
            return;
        }
        downloadScroll.errorText = "";
        downloadScroll.infoText = "";

        if (Settings.destinationMode === "ask_every_time") {
            downloadScroll.pendingUrl = rawUrl;
            downloadScroll.pendingOptions = downloadScroll.currentOptions("");
            askFolderDialog.open();
            return;
        }

        Controller.submitDownload(rawUrl, downloadScroll.currentOptions(""));
    }

    FolderDialog {
        id: browseFolderDialog
        title: "Select Download Folder"
        currentFolder: (typeof Settings !== "undefined" && Settings && Settings.outputFolder) ? ("file:///" + Settings.outputFolder.replace(/\\/g, "/")) : ""
        onAccepted: {
            var selectedPath = selectedFolder.toString().replace("file:///", "").replace(/\//g, "\\");
            if (Settings) {
                Settings.outputFolder = selectedPath;
                Settings.save();
            }
        }
    }

    FolderDialog {
        id: askFolderDialog
        title: "Choose Destination For This Download"
        currentFolder: (typeof Settings !== "undefined" && Settings && Settings.outputFolder) ? ("file:///" + Settings.outputFolder.replace(/\\/g, "/")) : ""
        onAccepted: {
            var selectedPath = selectedFolder.toString().replace("file:///", "").replace(/\//g, "\\");
            if (downloadScroll.pendingUrl) {
                var opts = downloadScroll.currentOptions(selectedPath);
                Controller.submitDownload(downloadScroll.pendingUrl, opts);
                downloadScroll.pendingUrl = "";
                downloadScroll.pendingOptions = ({});
            }
        }
        onRejected: {
            downloadScroll.infoText = "Download cancelled — destination selection was dismissed.";
            downloadScroll.pendingUrl = "";
            downloadScroll.pendingOptions = ({});
        }
    }

    Connections {
        target: Controller
        function onSubmissionAccepted(taskId, url) {
            urlInputInner.text = "";
            downloadScroll.errorText = "";
            downloadScroll.infoText = "";
            shell.currentPageIndex = 1;
        }
        function onSubmissionFailed(title, message) {
            downloadScroll.errorText = title + ": " + message;
            downloadScroll.infoText = "";
        }
        function onPrefillRequested(url) {
            urlInputInner.text = url;
            urlInputInner.forceActiveFocus();
        }
    }

    Item {
        width: downloadScroll.availableWidth
        implicitHeight: mainLayout.implicitHeight + downloadScroll.topMarginPad * 2 + 16

        ColumnLayout {
            id: mainLayout
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: parent.top
            anchors.topMargin: downloadScroll.topMarginPad
            width: downloadScroll.contentMaxW
            spacing: downloadScroll.responsiveGap

            // Page Header
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2

                Label {
                    text: "Download Media"
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.displayTitleSize
                    font.bold: true
                    color: Theme.text
                }

                Label {
                    Layout.fillWidth: true
                    text: "Capture high-fidelity media streams directly from supported sources."
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.bodySize
                    color: Theme.textDim
                    wrapMode: Text.WordWrap
                }
            }

            // Feedback Banners (Error / Info)
            Rectangle {
                visible: downloadScroll.errorText !== ""
                Layout.fillWidth: true
                implicitHeight: errorLabel.implicitHeight + 16
                radius: Theme.controlRadius
                color: Theme.errorSoft
                border.width: 1
                border.color: Theme.error

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 8

                    Label {
                        id: errorLabel
                        Layout.fillWidth: true
                        text: downloadScroll.errorText
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.bodySize
                        font.bold: true
                        color: Theme.error
                        wrapMode: Text.WordWrap
                    }
                }
            }

            Rectangle {
                visible: downloadScroll.infoText !== ""
                Layout.fillWidth: true
                implicitHeight: infoLabel.implicitHeight + 16
                radius: Theme.controlRadius
                color: Theme.warningSoft
                border.width: 1
                border.color: Theme.warning

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 8

                    Label {
                        id: infoLabel
                        Layout.fillWidth: true
                        text: downloadScroll.infoText
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.bodySize
                        font.bold: true
                        color: Theme.warning
                        wrapMode: Text.WordWrap
                    }
                }
            }

            // Section 1: Media Source & Destination
            Rectangle {
                Layout.fillWidth: true
                implicitHeight: sourceCol.implicitHeight + 28
                radius: Theme.cardRadius
                color: Theme.card
                border.width: 1
                border.color: Theme.border

                ColumnLayout {
                    id: sourceCol
                    anchors.fill: parent
                    anchors.margins: Theme.cardPadX
                    spacing: 12

                    RowLayout {
                        spacing: 8
                        Image {
                            source: Qt.resolvedUrl("../../../assets/branding/v2icons/link-accent-32.png")
                            Layout.preferredWidth: 14
                            Layout.preferredHeight: 14
                            fillMode: Image.PreserveAspectFit
                            mipmap: true
                        }
                        Label {
                            text: "MEDIA SOURCE & DESTINATION"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.microSize
                            font.bold: true
                            color: Theme.textDim
                        }
                    }

                    // URL Input Field with Integrated Paste Pill
                    Rectangle {
                        Layout.fillWidth: true
                        implicitHeight: 44
                        radius: Theme.controlRadius
                        color: Theme.cardAlt
                        border.width: urlInputInner.activeFocus ? 2 : 1
                        border.color: urlInputInner.activeFocus ? Theme.focusRing : Theme.borderStrong

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 12
                            anchors.rightMargin: 6
                            spacing: 8

                            TextInput {
                                id: urlInputInner
                                Layout.fillWidth: true
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.bodySize
                                color: Theme.text
                                selectByMouse: true
                                clip: true

                                Text {
                                    anchors.fill: parent
                                    text: "https://..."
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.bodySize
                                    color: Theme.textDisabled
                                    visible: !urlInputInner.text && !urlInputInner.activeFocus
                                    verticalAlignment: Text.AlignVCenter
                                }

                                Keys.onReturnPressed: downloadScroll.submit()
                            }

                            VPrimaryButton {
                                text: "Paste"
                                Layout.preferredHeight: 32
                                Layout.preferredWidth: 68
                                onClicked: {
                                    var clip = Controller.getClipboardText();
                                    if (clip) {
                                        urlInputInner.text = clip.trim();
                                    }
                                }
                            }
                        }
                    }

                    // Save Location Row
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10

                        Label {
                            text: "Save Location:"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.bodySize
                            font.bold: true
                            color: Theme.text
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            implicitHeight: 36
                            radius: Theme.controlRadius
                            color: Theme.cardAlt
                            border.width: 1
                            border.color: Theme.border

                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 12
                                anchors.rightMargin: 12
                                spacing: 8

                                Label {
                                    Layout.fillWidth: true
                                    text: (typeof Settings !== "undefined" && Settings && Settings.destinationMode === "ask_every_time")
                                          ? "(Ask destination every time)"
                                          : ((typeof Settings !== "undefined" && Settings && Settings.outputFolder) ? Settings.outputFolder : "Default folder")
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.smallSize
                                    color: (typeof Settings !== "undefined" && Settings && Settings.destinationMode === "ask_every_time") ? Theme.accentHover : Theme.textMuted
                                    elide: Text.ElideMiddle
                                }
                            }
                        }

                        VSecondaryButton {
                            text: "Browse"
                            Layout.preferredHeight: 36
                            onClicked: browseFolderDialog.open()
                        }
                    }
                }
            }

            // Section 2: Output Configuration (Video Stream vs Audio Only)
            Rectangle {
                Layout.fillWidth: true
                implicitHeight: configCol.implicitHeight + 28
                radius: Theme.cardRadius
                color: Theme.card
                border.width: 1
                border.color: Theme.border

                ColumnLayout {
                    id: configCol
                    anchors.fill: parent
                    anchors.margins: Theme.cardPadX
                    spacing: 12

                    RowLayout {
                        spacing: 8
                        Image {
                            source: Qt.resolvedUrl("../../../assets/branding/v2icons/gear-accent-32.png")
                            Layout.preferredWidth: 14
                            Layout.preferredHeight: 14
                            fillMode: Image.PreserveAspectFit
                            mipmap: true
                        }
                        Label {
                            text: "OUTPUT CONFIGURATION"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.microSize
                            font.bold: true
                            color: Theme.textDim
                        }
                    }

                    VSegmentedButton {
                        id: modeSegment
                        options: ["Video", "Audio"]
                        selectedIndex: 0
                    }

                    // Video Options Grid
                    GridLayout {
                        visible: modeSegment.selectedIndex === 0
                        Layout.fillWidth: true
                        columns: downloadScroll.availableWidth > 680 ? 2 : 1
                        columnSpacing: 18
                        rowSpacing: 8

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4

                            Label {
                                text: "TARGET QUALITY"
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.microSize
                                font.bold: true
                                color: Theme.textDim
                            }

                            VComboBox {
                                id: qualityCombo
                                Layout.fillWidth: true
                                model: [
                                    "Best Available",
                                    "8K (4320p)",
                                    "4K (2160p)",
                                    "1440p (2K)",
                                    "1080p (Full HD)",
                                    "720p (HD)",
                                    "480p (SD)",
                                    "360p"
                                ]
                                currentIndex: 0
                            }
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4

                            Label {
                                text: "FRAME RATE & SUBTITLES"
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.microSize
                                font.bold: true
                                color: Theme.textDim
                            }

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 14

                                VCheckBox {
                                    id: fps60Check
                                    text: "Prefer 60 FPS"
                                    checked: true
                                }

                                VCheckBox {
                                    id: subsCheck
                                    text: "Download Subtitles"
                                    checked: false
                                }
                            }
                        }
                    }

                    // Audio Options Grid (MP3 with bitrate, Opus, WAV)
                    GridLayout {
                        visible: modeSegment.selectedIndex === 1
                        Layout.fillWidth: true
                        columns: downloadScroll.availableWidth > 680 ? 2 : 1
                        columnSpacing: 18
                        rowSpacing: 8

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4

                            Label {
                                text: "AUDIO FORMAT"
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.microSize
                                font.bold: true
                                color: Theme.textDim
                            }

                            VComboBox {
                                id: audioFormatCombo
                                Layout.fillWidth: true
                                model: [
                                    "MP3",
                                    "Opus (High Efficiency)",
                                    "WAV (Uncompressed PCM)"
                                ]
                                currentIndex: 0
                            }
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            visible: audioFormatCombo.currentIndex === 0
                            spacing: 4

                            Label {
                                text: "MP3 BITRATE"
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.microSize
                                font.bold: true
                                color: Theme.textDim
                            }

                            VComboBox {
                                id: mp3BitrateCombo
                                Layout.fillWidth: true
                                model: [
                                    "320 kbps (Best)",
                                    "256 kbps",
                                    "192 kbps (Standard)",
                                    "128 kbps"
                                ]
                                currentIndex: 0
                            }
                        }
                    }
                }
            }

            // Section 3: Advanced Network & Custom Headers (Android 4.5.2 Collapsible Header Card)
            Rectangle {
                id: headersCard
                objectName: "headersCard"
                property bool isExpanded: false
                Layout.fillWidth: true
                implicitHeight: headersCol.implicitHeight + 20
                radius: Theme.cardRadius
                color: Theme.card
                border.width: 1
                border.color: isExpanded ? Theme.accentHover : Theme.border

                ColumnLayout {
                    id: headersCol
                    anchors.fill: parent
                    anchors.margins: Theme.cardPadX
                    spacing: 12

                    // Interactive Collapsible Header Row
                    Item {
                        Layout.fillWidth: true
                        implicitHeight: 40

                        Rectangle {
                            anchors.fill: parent
                            anchors.margins: -4
                            radius: Theme.controlRadius
                            color: headerMouse.containsMouse ? Theme.surfaceHover : "transparent"
                        }

                        RowLayout {
                            anchors.fill: parent
                            spacing: 10

                            Image {
                                source: Qt.resolvedUrl("../../../assets/branding/v2icons/gear-accent-32.png")
                                Layout.preferredWidth: 16
                                Layout.preferredHeight: 16
                                fillMode: Image.PreserveAspectFit
                                mipmap: true
                            }

                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 2

                                Label {
                                    text: "ADVANCED NETWORK & HEADERS"
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.smallSize
                                    font.bold: true
                                    color: Theme.text
                                }

                                Label {
                                    text: "HTTP Referer, Origin, Proxy, IPv4, and custom request headers"
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.microSize
                                    color: Theme.textDim
                                }
                            }

                            // Rotating Chevron Indicator
                            Label {
                                text: headersCard.isExpanded ? "▲" : "▼"
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.smallSize
                                font.bold: true
                                color: Theme.accent
                            }
                        }

                        MouseArea {
                            id: headerMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: headersCard.isExpanded = !headersCard.isExpanded
                        }
                    }

                    // Collapsible Content
                    ColumnLayout {
                        visible: headersCard.isExpanded
                        Layout.fillWidth: true
                        spacing: 12

                        Rectangle {
                            Layout.fillWidth: true
                            height: 1
                            color: Theme.border
                        }

                        // Network Directives Grid
                        GridLayout {
                            Layout.fillWidth: true
                            columns: downloadScroll.availableWidth > 680 ? 2 : 1
                            columnSpacing: 14
                            rowSpacing: 8

                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 2
                                Label {
                                    text: "Referer URL:"
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.microSize
                                    font.bold: true
                                    color: Theme.textMuted
                                }
                                VTextField {
                                    id: refererInput
                                    Layout.fillWidth: true
                                    placeholderText: "https://example.com/page"
                                }
                            }

                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 2
                                Label {
                                    text: "Origin URL:"
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.microSize
                                    font.bold: true
                                    color: Theme.textMuted
                                }
                                VTextField {
                                    id: originInput
                                    Layout.fillWidth: true
                                    placeholderText: "https://example.com"
                                }
                            }

                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 2
                                Label {
                                    text: "Custom Proxy (HTTP/SOCKS5):"
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.microSize
                                    font.bold: true
                                    color: Theme.textMuted
                                }
                                VTextField {
                                    id: proxyInput
                                    Layout.fillWidth: true
                                    placeholderText: (typeof Settings !== "undefined" && Settings && Settings.proxy) ? Settings.proxy : "http://user:pass@host:port"
                                }
                            }

                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 2
                                Label {
                                    text: "Network Protocol Policy:"
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.microSize
                                    font.bold: true
                                    color: Theme.textMuted
                                }
                                VCheckBox {
                                    id: ipv4Check
                                    text: "Force IPv4 Resolution"
                                    checked: (typeof Settings !== "undefined" && Settings && Settings.forceIpv4)
                                }
                            }
                        }

                        // Custom Headers Multiline Field
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            Label {
                                text: "Custom HTTP Headers (Name: Value per line):"
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.microSize
                                font.bold: true
                                color: Theme.textMuted
                            }
                            Rectangle {
                                Layout.fillWidth: true
                                implicitHeight: 68
                                radius: Theme.controlRadius
                                color: Theme.cardAlt
                                border.width: customHeadersInput.activeFocus ? 2 : 1
                                border.color: customHeadersInput.activeFocus ? Theme.focusRing : Theme.border

                                ScrollView {
                                    anchors.fill: parent
                                    anchors.margins: 6
                                    TextArea {
                                        id: customHeadersInput
                                        font.family: Theme.fontFamily
                                        font.pixelSize: Theme.smallSize
                                        color: Theme.text
                                        placeholderText: "X-Custom-Header: value\nAccept-Language: en-US"
                                        wrapMode: Text.WordWrap
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // Section 4: Playlist Scope & Trimming (Android 4.5.2 Collapsible Header Card)
            Rectangle {
                id: playlistCard
                objectName: "playlistCard"
                property bool isExpanded: false
                Layout.fillWidth: true
                implicitHeight: playlistScopeCol.implicitHeight + 20
                radius: Theme.cardRadius
                color: Theme.card
                border.width: 1
                border.color: isExpanded ? Theme.accentHover : Theme.border

                ColumnLayout {
                    id: playlistScopeCol
                    anchors.fill: parent
                    anchors.margins: Theme.cardPadX
                    spacing: 12

                    // Interactive Collapsible Header Row
                    Item {
                        Layout.fillWidth: true
                        implicitHeight: 40

                        Rectangle {
                            anchors.fill: parent
                            anchors.margins: -4
                            radius: Theme.controlRadius
                            color: playlistMouse.containsMouse ? Theme.surfaceHover : "transparent"
                        }

                        RowLayout {
                            anchors.fill: parent
                            spacing: 10

                            Image {
                                source: Qt.resolvedUrl("../../../assets/branding/v2icons/list-accent-32.png")
                                Layout.preferredWidth: 16
                                Layout.preferredHeight: 16
                                fillMode: Image.PreserveAspectFit
                                mipmap: true
                            }

                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 2

                                Label {
                                    text: "PLAYLIST & TRIMMING"
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.smallSize
                                    font.bold: true
                                    color: Theme.text
                                }

                                Label {
                                    text: "Playlist range extraction and ffmpeg time trimming"
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.microSize
                                    color: Theme.textDim
                                }
                            }

                            // Rotating Chevron Indicator
                            Label {
                                text: playlistCard.isExpanded ? "▲" : "▼"
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.smallSize
                                font.bold: true
                                color: Theme.accent
                            }
                        }

                        MouseArea {
                            id: playlistMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: playlistCard.isExpanded = !playlistCard.isExpanded
                        }
                    }

                    // Collapsible Content
                    ColumnLayout {
                        visible: playlistCard.isExpanded
                        Layout.fillWidth: true
                        spacing: 12

                        Rectangle {
                            Layout.fillWidth: true
                            height: 1
                            color: Theme.border
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 14

                            VCheckBox {
                                id: playlistCheck
                                text: "Download entire playlist"
                                checked: false
                            }

                            VCheckBox {
                                id: trimCheck
                                text: "Enable trim range"
                                checked: false
                            }
                        }

                        RowLayout {
                            visible: playlistCheck.checked
                            Layout.fillWidth: true
                            spacing: 10

                            ColumnLayout {
                                Layout.fillWidth: true
                                Layout.preferredWidth: 0
                                spacing: 4

                                Label {
                                    text: "START INDEX"
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.microSize
                                    font.bold: true
                                    color: Theme.textDim
                                }

                                VTextField {
                                    id: playlistStartField
                                    Layout.fillWidth: true
                                    text: "1"
                                    placeholderText: "1"
                                }
                            }

                            ColumnLayout {
                                Layout.fillWidth: true
                                Layout.preferredWidth: 0
                                spacing: 4

                                Label {
                                    text: "END INDEX"
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.microSize
                                    font.bold: true
                                    color: Theme.textDim
                                }

                                VTextField {
                                    id: playlistEndField
                                    Layout.fillWidth: true
                                    text: "last"
                                    placeholderText: "last"
                                }
                            }
                        }

                        RowLayout {
                            visible: trimCheck.checked
                            Layout.fillWidth: true
                            spacing: 10

                            ColumnLayout {
                                Layout.fillWidth: true
                                Layout.preferredWidth: 0
                                spacing: 4

                                Label {
                                    text: "START (HH:MM:SS)"
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.microSize
                                    font.bold: true
                                    color: Theme.textDim
                                }

                                VTextField {
                                    id: trimStartField
                                    Layout.fillWidth: true
                                    text: "00:00:00"
                                    placeholderText: "00:00:00"
                                }
                            }

                            ColumnLayout {
                                Layout.fillWidth: true
                                Layout.preferredWidth: 0
                                spacing: 4

                                Label {
                                    text: "END (HH:MM:SS)"
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.microSize
                                    font.bold: true
                                    color: Theme.textDim
                                }

                                VTextField {
                                    id: trimEndField
                                    Layout.fillWidth: true
                                    text: "00:00:00"
                                    placeholderText: "00:00:00"
                                }
                            }
                        }
                    }
                }
            }

            // Primary Action: Add to Queue
            Item {
                Layout.fillWidth: true
                implicitHeight: 48

                VPrimaryButton {
                    anchors.fill: parent
                    text: "Add to Queue"
                    iconName: "download"
                    onClicked: downloadScroll.submit()
                }
            }

            Item { Layout.preferredHeight: 12 }
        }
    }
}
