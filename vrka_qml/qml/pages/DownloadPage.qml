pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import QtQuick.Dialogs
import ".."
import "../components"

ScrollView {
    id: downloadScroll
    objectName: "downloadScroll"
    clip: true
    contentWidth: availableWidth
    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

    property string errorText: ""
    property string infoText: ""
    property string pendingUrl: ""
    property var pendingOptions: ({})

    // Viewport-aware layout tokens matching SettingsPage architecture
    readonly property bool isWide: downloadScroll.availableWidth >= 1020
    readonly property int responsiveGap: {
        var vH = downloadScroll.height;
        if (vH <= 720) return Theme.panelGap;
        return Math.min(22, Math.max(Theme.panelGap, Math.round(Theme.panelGap + (vH - 720) * 0.025)));
    }

    function currentOptions(folderOverride) {
        var isAudio = modeSegment.selectedIndex === 1;
        var opts = {
            "mode": isAudio ? "audio" : "video",
            "quality": qualityCombo.currentText,
            "fps60": fps60Check.checked,
            "audio_format": audioFormatCombo.currentText,
            "mp3_bitrate": mp3BitrateCombo.currentText,
            "download_subs": subsCheck.checked || advSubsCheck.checked,
            "sub_langs": advSubLangsInput.text.trim() || Settings.subLangs,
            "embed_subs": advEmbedSubsCheck.checked,
            "auto_captions": advAutoCaptionsCheck.checked,
            "embed_thumbnail": advEmbedThumbCheck.checked,
            "embed_metadata": advEmbedMetaCheck.checked,
            "sponsorblock": advSponsorblockCheck.checked,
            "sponsorblock_categories": advSponsorblockCategoriesInput.text.trim() || Settings.sponsorblockCategories,
            "output_folder": folderOverride || Settings.outputFolder,
            "referer": refererInput.text.trim(),
            "origin": originInput.text.trim(),
            "proxy": proxyInput.text.trim() || Settings.proxy,
            "force_ipv4": Settings.forceIpv4,
            "custom_headers": customHeadersInput.text.trim(),
            "is_playlist": playlistCheck.checked,
            "playlist_start": parseInt(playlistStartField.text.trim()) || 1,
            "playlist_end": parseInt(playlistEndField.text.trim()) || 0,
            "trim_enabled": trimCheck.checked,
            "start_time": trimCheck.checked ? trimStartField.text.trim() : "",
            "end_time": trimCheck.checked ? trimEndField.text.trim() : "",
            "cookie_source": Settings.cookieMode,
            "cookie_profile": Settings.cookieProfile,
            "output_template": Settings.outputTemplate,
            "format_sort": Settings.formatSort,
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
        implicitHeight: Math.max(mainLayout.implicitHeight + (downloadScroll.height > mainLayout.implicitHeight ? 0 : 32), downloadScroll.height)

        ColumnLayout {
            id: mainLayout
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: parent.top
            anchors.topMargin: {
                var excess = downloadScroll.height - mainLayout.implicitHeight;
                return excess > 20 ? Math.round(excess * 0.5) : 16;
            }
            width: Math.max(100, downloadScroll.availableWidth - 16)
            spacing: downloadScroll.responsiveGap

            // Page Header
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 4

                Label {
                    text: "Download Media"
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.displayTitleSize
                    font.bold: true
                    color: Theme.text
                }

                Label {
                    Layout.fillWidth: true
                    text: "Download media from supported sources with control over quality, format, network, and output."
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

            // Primary Workflow Grid (2-Column on Wide/Maximized, 1-Column on Narrow)
            GridLayout {
                Layout.fillWidth: true
                columns: downloadScroll.isWide ? 2 : 1
                columnSpacing: Theme.panelGap
                rowSpacing: downloadScroll.responsiveGap

                // Section 1: Media Source & Destination
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: downloadScroll.isWide
                    implicitHeight: sourceCol.implicitHeight + 36
                    radius: Theme.cardRadius
                    color: Theme.card
                    border.width: 1
                    border.color: Theme.border

                    ColumnLayout {
                        id: sourceCol
                        anchors.fill: parent
                        anchors.margins: 18
                        spacing: 12

                        RowLayout {
                            spacing: 10
                            Image {
                                source: Qt.resolvedUrl("../../../assets/branding/v2icons/link-accent-32.png")
                                Layout.preferredWidth: 16
                                Layout.preferredHeight: 16
                                Layout.alignment: Qt.AlignVCenter
                                fillMode: Image.PreserveAspectFit
                                mipmap: true
                            }
                            ColumnLayout {
                                spacing: 2
                                Label {
                                    text: "Media Source & Destination"
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.sectionTitleSize
                                    font.bold: true
                                    color: Theme.text
                                }
                                Label {
                                    text: "Target media link and destination folder"
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.microSize
                                    color: Theme.textDim
                                }
                            }
                        }

                        // Field 1: Media URL
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4

                            Label {
                                text: "MEDIA URL"
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.microSize
                                font.bold: true
                                color: Theme.textDim
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                implicitHeight: 38
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
                                        Layout.preferredHeight: 28
                                        Layout.preferredWidth: 64
                                        onClicked: {
                                            var clip = Controller.getClipboardText();
                                            if (clip) {
                                                urlInputInner.text = clip.trim();
                                            }
                                        }
                                    }
                                }
                            }
                        }

                        // Field 2: Save Location
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4

                            Label {
                                text: "SAVE LOCATION"
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.microSize
                                font.bold: true
                                color: Theme.textDim
                            }

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 8

                                Rectangle {
                                    Layout.fillWidth: true
                                    implicitHeight: 38
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
                                    Layout.preferredHeight: 38
                                    Layout.preferredWidth: 80
                                    onClicked: browseFolderDialog.open()
                                }
                            }
                        }
                    }
                }

                // Section 2: Output Configuration (Video Stream vs Audio Only)
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: downloadScroll.isWide
                    implicitHeight: configCol.implicitHeight + 36
                    radius: Theme.cardRadius
                    color: Theme.card
                    border.width: 1
                    border.color: Theme.border

                    ColumnLayout {
                        id: configCol
                        anchors.fill: parent
                        anchors.margins: 18
                        spacing: 12

                        RowLayout {
                            spacing: 10
                            Image {
                                source: Qt.resolvedUrl("../../../assets/branding/v2icons/gear-accent-32.png")
                                Layout.preferredWidth: 16
                                Layout.preferredHeight: 16
                                Layout.alignment: Qt.AlignVCenter
                                fillMode: Image.PreserveAspectFit
                                mipmap: true
                            }
                            ColumnLayout {
                                spacing: 2
                                Label {
                                    text: "Output Configuration"
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.sectionTitleSize
                                    font.bold: true
                                    color: Theme.text
                                }
                                Label {
                                    text: "Select media format, resolution, and stream preferences"
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.microSize
                                    color: Theme.textDim
                                }
                            }
                        }

                        // Field 1: Download Mode
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4

                            Label {
                                text: "DOWNLOAD MODE"
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.microSize
                                font.bold: true
                                color: Theme.textDim
                            }

                            VSegmentedButton {
                                id: modeSegment
                                options: ["Video", "Audio"]
                                selectedIndex: 0
                            }
                        }

                        // Video Options Grid
                        GridLayout {
                            visible: modeSegment.selectedIndex === 0
                            Layout.fillWidth: true
                            columns: downloadScroll.availableWidth > 680 ? 2 : 1
                            columnSpacing: 16
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
                                        text: "Subtitles"
                                        checked: false
                                    }
                                }
                            }
                        }

                        // Audio Options Grid
                        GridLayout {
                            visible: modeSegment.selectedIndex === 1
                            Layout.fillWidth: true
                            columns: downloadScroll.availableWidth > 680 ? 2 : 1
                            columnSpacing: 16
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
                                        "best",
                                        "mp3",
                                        "m4a",
                                        "flac",
                                        "opus",
                                        "wav",
                                        "aac"
                                    ]
                                    currentIndex: 0
                                }
                            }

                            ColumnLayout {
                                Layout.fillWidth: true
                                visible: audioFormatCombo.currentIndex === 0 || audioFormatCombo.currentText === "mp3"
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

            // Section 3: ONE Unified Expandable Advanced Options Section
            Rectangle {
                id: advancedOptionsCard
                objectName: "advancedOptionsCard"
                property bool isExpanded: false
                Layout.fillWidth: true
                Layout.columnSpan: downloadScroll.isWide ? 2 : 1
                implicitHeight: isExpanded ? (advancedCol.implicitHeight + 36) : (advHeaderRow.implicitHeight + 28)
                radius: Theme.cardRadius
                color: Theme.card
                border.width: 1
                border.color: advHeaderMouse.containsMouse ? Theme.borderStrong : Theme.border

                Behavior on border.color { ColorAnimation { duration: 120 } }

                ColumnLayout {
                    id: advancedCol
                    anchors.fill: parent
                    anchors.margins: 18
                    spacing: 14

                    // Interactive Collapsible Header Row (Clean, no inner grey hover fill)
                    Item {
                        id: advHeaderRow
                        Layout.fillWidth: true
                        implicitHeight: 40

                        RowLayout {
                            anchors.fill: parent
                            spacing: 12

                            Image {
                                source: Qt.resolvedUrl("../../../assets/branding/v2icons/sliders-accent-32.png")
                                Layout.preferredWidth: 16
                                Layout.preferredHeight: 16
                                Layout.alignment: Qt.AlignVCenter
                                fillMode: Image.PreserveAspectFit
                                mipmap: true
                            }

                            ColumnLayout {
                                Layout.fillWidth: true
                                Layout.alignment: Qt.AlignVCenter
                                spacing: 2

                                Label {
                                    text: advancedOptionsCard.isExpanded ? "Hide Advanced Options" : "Advanced Options"
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.sectionTitleSize
                                    font.bold: true
                                    color: Theme.text
                                }

                                Label {
                                    text: "Quality ranking, subtitles, metadata, playlist scope, trimming, and network headers"
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.microSize
                                    color: Theme.textDim
                                    elide: Text.ElideRight
                                }
                            }

                            // Rotating Chevron Indicator
                            Label {
                                text: advancedOptionsCard.isExpanded ? "▲" : "▼"
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.smallSize
                                font.bold: true
                                color: advHeaderMouse.containsMouse ? Theme.accentHover : Theme.accent
                                Layout.alignment: Qt.AlignVCenter
                            }
                        }

                        MouseArea {
                            id: advHeaderMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: advancedOptionsCard.isExpanded = !advancedOptionsCard.isExpanded
                        }
                    }

                    // Unified Collapsible Content (Organized Clean Sections with Subtle Separators)
                    ColumnLayout {
                        visible: advancedOptionsCard.isExpanded
                        Layout.fillWidth: true
                        spacing: 16

                        Rectangle {
                            Layout.fillWidth: true
                            height: Theme.hairline
                            color: Theme.border
                        }

                        // --- SECTION A: STREAM AND QUALITY RANKING ---
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            Label {
                                text: "STREAM & QUALITY RANKING"
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.microSize
                                font.bold: true
                                color: Theme.accentHover
                            }

                            Label {
                                text: "Multi-factor quality ranking prioritizes optimal resolution, stream bitrate, and codec efficiency without blind format preferences."
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.smallSize
                                color: Theme.textDim
                                wrapMode: Text.WordWrap
                                Layout.fillWidth: true
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            height: Theme.hairline
                            color: Theme.border
                        }

                        // --- SECTION B: SUBTITLES & CAPTIONS ---
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            Label {
                                text: "SUBTITLES & CAPTIONS"
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.microSize
                                font.bold: true
                                color: Theme.accentHover
                            }

                            GridLayout {
                                Layout.fillWidth: true
                                columns: downloadScroll.availableWidth > 680 ? 2 : 1
                                columnSpacing: 16
                                rowSpacing: 8

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 4
                                    Label {
                                        text: "SUBTITLE LANGUAGE REGEX"
                                        font.family: Theme.fontFamily
                                        font.pixelSize: Theme.microSize
                                        font.bold: true
                                        color: Theme.textDim
                                    }
                                    VTextField {
                                        id: advSubLangsInput
                                        Layout.fillWidth: true
                                        text: Settings.subLangs
                                        placeholderText: "en.*, ja, zh-Hans"
                                    }
                                }

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 6
                                    VCheckBox {
                                        id: advSubsCheck
                                        text: "Download matching subtitles"
                                        checked: subsCheck.checked
                                        onToggled: subsCheck.checked = checked
                                    }
                                    VCheckBox {
                                        id: advEmbedSubsCheck
                                        text: "Embed subtitles into media container"
                                        checked: Settings.embedSubs
                                    }
                                    VCheckBox {
                                        id: advAutoCaptionsCheck
                                        text: "Include automatically generated captions"
                                        checked: Settings.autoCaptions
                                    }
                                }
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            height: Theme.hairline
                            color: Theme.border
                        }

                        // --- SECTION C: METADATA & MEDIA FILTERS ---
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            Label {
                                text: "METADATA & SPONSORBLOCK"
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.microSize
                                font.bold: true
                                color: Theme.accentHover
                            }

                            GridLayout {
                                Layout.fillWidth: true
                                columns: downloadScroll.availableWidth > 680 ? 2 : 1
                                columnSpacing: 16
                                rowSpacing: 8

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 6
                                    VCheckBox {
                                        id: advEmbedThumbCheck
                                        text: "Embed thumbnail as album/cover art"
                                        checked: Settings.embedThumbnail
                                    }
                                    VCheckBox {
                                        id: advEmbedMetaCheck
                                        text: "Embed title, artist, and ID3 metadata"
                                        checked: Settings.embedMetadata
                                    }
                                    VCheckBox {
                                        id: advSponsorblockCheck
                                        text: "Remove SponsorBlock advertisement segments"
                                        checked: Settings.sponsorblock
                                    }
                                }

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    visible: advSponsorblockCheck.checked
                                    spacing: 4
                                    Label {
                                        text: "SPONSORBLOCK CATEGORIES"
                                        font.family: Theme.fontFamily
                                        font.pixelSize: Theme.microSize
                                        font.bold: true
                                        color: Theme.textDim
                                    }
                                    VTextField {
                                        id: advSponsorblockCategoriesInput
                                        Layout.fillWidth: true
                                        text: Settings.sponsorblockCategories
                                        placeholderText: "sponsor,selfpromo,interaction"
                                    }
                                }
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            height: Theme.hairline
                            color: Theme.border
                        }

                        // --- SECTION D: PLAYLIST SCOPE & TIME TRIMMING ---
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            Label {
                                text: "PLAYLIST SCOPE & TIME TRIMMING"
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.microSize
                                font.bold: true
                                color: Theme.accentHover
                            }

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 18

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
                                spacing: 14

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
                                spacing: 14

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    Layout.preferredWidth: 0
                                    spacing: 4
                                    Label {
                                        text: "START TIME (HH:MM:SS)"
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
                                        text: "END TIME (HH:MM:SS)"
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

                        Rectangle {
                            Layout.fillWidth: true
                            height: Theme.hairline
                            color: Theme.border
                        }

                        // --- SECTION E: NETWORK DIRECTIVES & CUSTOM HEADERS ---
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            Label {
                                text: "NETWORK DIRECTIVES & CUSTOM HEADERS"
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.microSize
                                font.bold: true
                                color: Theme.accentHover
                            }

                            GridLayout {
                                Layout.fillWidth: true
                                columns: downloadScroll.availableWidth > 800 ? 3 : (downloadScroll.availableWidth > 540 ? 2 : 1)
                                columnSpacing: 16
                                rowSpacing: 10

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 4
                                    Label {
                                        text: "Referer URL:"
                                        font.family: Theme.fontFamily
                                        font.pixelSize: Theme.microSize
                                        font.bold: true
                                        color: Theme.textDim
                                    }
                                    VTextField {
                                        id: refererInput
                                        Layout.fillWidth: true
                                        placeholderText: "https://example.com/page"
                                    }
                                }

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 4
                                    Label {
                                        text: "Origin URL:"
                                        font.family: Theme.fontFamily
                                        font.pixelSize: Theme.microSize
                                        font.bold: true
                                        color: Theme.textDim
                                    }
                                    VTextField {
                                        id: originInput
                                        Layout.fillWidth: true
                                        placeholderText: "https://example.com"
                                    }
                                }

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 4
                                    Label {
                                        text: "Proxy Override (For This Download):"
                                        font.family: Theme.fontFamily
                                        font.pixelSize: Theme.microSize
                                        font.bold: true
                                        color: Theme.textDim
                                    }
                                    VTextField {
                                        id: proxyInput
                                        Layout.fillWidth: true
                                        placeholderText: (typeof Settings !== "undefined" && Settings && Settings.proxy) ? Settings.proxy : "http://user:pass@host:port"
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
                                    color: Theme.textDim
                                }
                                Rectangle {
                                    Layout.fillWidth: true
                                    implicitHeight: 74
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
            }

            // Primary Action: Add to Queue
            Item {
                Layout.fillWidth: true
                Layout.columnSpan: downloadScroll.isWide ? 2 : 1
                implicitHeight: 46

                VPrimaryButton {
                    anchors.fill: parent
                    text: "Add to Queue"
                    iconName: "download"
                    onClicked: downloadScroll.submit()
                }
            }
        } // Close GridLayout

        Item {
            Layout.preferredHeight: (downloadScroll.height <= mainLayout.implicitHeight + 20) ? 16 : 0
        }
        }
    }
}
