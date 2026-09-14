pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import QtQuick.Dialogs
import ".."
import "../components"

ScrollView {
    id: settingsScroll
    objectName: "settingsScroll"
    clip: true
    contentWidth: availableWidth
    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

    property string feedbackMessage: ""

    FolderDialog {
        id: settingsFolderDialog
        title: "Select Default Download Directory"
        currentFolder: (typeof Settings !== "undefined" && Settings && Settings.outputFolder) ? ("file:///" + Settings.outputFolder.replace(/\\/g, "/")) : ""
        onAccepted: {
            var path = selectedFolder.toString().replace("file:///", "").replace(/\//g, "\\");
            if (Settings) {
                Settings.outputFolder = path;
                Settings.save();
            }
        }
    }

    FileDialog {
        id: cookieFileDialog
        title: "Select Cookie File"
        nameFilters: ["Text files (*.txt)", "All files (*)"]
        onAccepted: {
            var path = selectedFile.toString().replace("file:///", "").replace(/\//g, "\\");
            if (Settings) {
                Settings.cookieFile = path;
            }
        }
    }

    ColumnLayout {
        width: Math.max(100, settingsScroll.availableWidth - 16)
        spacing: Theme.panelGap

        // Page Header with Save Button
        GridLayout {
            Layout.fillWidth: true
            columns: settingsScroll.availableWidth > 640 ? 2 : 1
            columnSpacing: 14
            rowSpacing: 10

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2

                Label {
                    text: "Settings"
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.displayTitleSize
                    font.bold: true
                    color: Theme.text
                }

                Label {
                    Layout.fillWidth: true
                    text: "Configure downloader engine, network, output formats, browser privacy, and application updates."
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.bodySize
                    color: Theme.textDim
                    wrapMode: Text.WordWrap
                }
            }

            VPrimaryButton {
                text: "Save Preferences"
                Layout.preferredHeight: 38
                Layout.preferredWidth: 160
                Layout.alignment: settingsScroll.availableWidth > 640 ? (Qt.AlignRight | Qt.AlignVCenter) : Qt.AlignLeft
                onClicked: {
                    var ok = Settings.save();
                    settingsScroll.feedbackMessage = ok ? "Preferences saved successfully." : "Failed to save preferences.";
                }
            }
        }

        // Feedback Banner
        Rectangle {
            visible: settingsScroll.feedbackMessage !== ""
            Layout.fillWidth: true
            implicitHeight: feedbackLabel.implicitHeight + 16
            radius: Theme.controlRadius
            color: Theme.successSoft
            border.width: 1
            border.color: Theme.success

            RowLayout {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 8

                Label {
                    id: feedbackLabel
                    Layout.fillWidth: true
                    text: settingsScroll.feedbackMessage
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.bodySize
                    font.bold: true
                    color: Theme.success
                }
            }
        }

        // Section 1: Download Destination
        VCard {
            Layout.fillWidth: true
            headerTitle: "Download Destination"
            headerSubtitle: "Control default target directory and folder prompts"
            headerIcon: Qt.resolvedUrl("../../../assets/branding/v2icons/link-accent-32.png")

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 12

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 4

                    Label {
                        text: "DESTINATION MODE"
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.microSize
                        font.bold: true
                        color: Theme.textDim
                    }

                    VComboBox {
                        id: destModeCombo
                        Layout.fillWidth: true
                        model: [
                            "Remember Location (Persist output directory)",
                            "Ask Every Time (Prompt folder dialog per download)"
                        ]
                        currentIndex: Settings.destinationMode === "ask_every_time" ? 1 : 0
                        onActivated: (idx) => {
                            Settings.destinationMode = idx === 1 ? "ask_every_time" : "remember"
                        }
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 4

                    Label {
                        text: "DEFAULT OUTPUT FOLDER"
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
                                anchors.margins: 10
                                Label {
                                    Layout.fillWidth: true
                                    text: Settings.outputFolder || "Default directory"
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.smallSize
                                    color: Theme.text
                                    elide: Text.ElideMiddle
                                }
                            }
                        }

                        VSecondaryButton {
                            text: "Browse"
                            Layout.preferredHeight: 38
                            onClicked: settingsFolderDialog.open()
                        }
                    }
                }
            }
        }

        // Section 2: Fonts
        VCard {
            Layout.fillWidth: true
            headerTitle: "Fonts"
            iconText: "Aa"

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 6

                VComboBox {
                    id: fontCombo
                    Layout.fillWidth: true
                    model: ["Monospace", "System Default"]
                    currentIndex: Settings.fontFamilyMode === "system" ? 1 : 0
                    onActivated: (idx) => {
                        Settings.fontFamilyMode = idx === 1 ? "system" : "vrka"
                    }
                }
            }
        }

        // Section 3: Subsystems & Components
        VCard {
            Layout.fillWidth: true
            headerTitle: "Subsystems & Components"
            headerSubtitle: "Core downloader engine binaries and passive media detection sensors"
            headerIcon: Qt.resolvedUrl("../../../assets/branding/v2icons/gear-accent-32.png")

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 14

                // Authoritative Batch Operation Header Row
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 12

                    VPrimaryButton {
                        text: (typeof Operational !== "undefined" && Operational && Operational.batchBusy) ? "Checking All..." : "Check All Updates"
                        enabled: !(typeof Operational !== "undefined" && Operational && Operational.batchBusy)
                        Layout.preferredHeight: 34
                        Layout.preferredWidth: 160
                        onClicked: {
                            if (typeof Operational !== "undefined" && Operational) {
                                Operational.checkAllUpdates()
                            }
                        }
                    }

                    VSecondaryButton {
                        text: "Update All Available"
                        visible: (typeof Operational !== "undefined" && Operational && (Operational.updaterUpdateAvailable || Operational.ubolUpdateAvailable || Operational.puemosUpdateAvailable))
                        enabled: !(typeof Operational !== "undefined" && Operational && Operational.batchBusy)
                        Layout.preferredHeight: 34
                        onClicked: {
                            if (typeof Operational !== "undefined" && Operational) {
                                Operational.updateAllAvailable()
                            }
                        }
                    }

                    Label {
                        Layout.fillWidth: true
                        text: (typeof Operational !== "undefined" && Operational) ? Operational.batchStatusText : "Ready"
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.microSize
                        color: Theme.textDim
                        elide: Text.ElideRight
                    }
                }

                // Component 1: yt-dlp Engine
                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: ytdlpCol.implicitHeight + 24
                    radius: Theme.controlRadius
                    color: Theme.cardAlt
                    border.width: 1
                    border.color: Theme.border

                    ColumnLayout {
                        id: ytdlpCol
                        anchors.fill: parent
                        anchors.margins: 12
                        spacing: 10

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            Label {
                                text: "yt-dlp Core Engine"
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.bodySize
                                font.bold: true
                                color: Theme.text
                            }

                            Item { Layout.fillWidth: true }

                            Rectangle {
                                radius: 4
                                color: (typeof Operational !== "undefined" && Operational && Operational.updaterOperationalStatus === "Active") ? Theme.successSoft : Theme.errorSoft
                                border.width: 1
                                border.color: (typeof Operational !== "undefined" && Operational && Operational.updaterOperationalStatus === "Active") ? Theme.success : Theme.error
                                implicitWidth: ytVerText.implicitWidth + 12
                                implicitHeight: 20

                                Text {
                                    id: ytVerText
                                    anchors.centerIn: parent
                                    text: (typeof Operational !== "undefined" && Operational && Operational.updaterOperationalStatus) ? Operational.updaterOperationalStatus.toUpperCase() : "ACTIVE"
                                    font.family: Theme.fontFamily
                                    font.pixelSize: 9
                                    font.bold: true
                                    color: (typeof Operational !== "undefined" && Operational && Operational.updaterOperationalStatus === "Active") ? Theme.success : Theme.error
                                }
                            }
                        }

                        // Component Metadata Grid
                        GridLayout {
                            Layout.fillWidth: true
                            columns: settingsScroll.availableWidth > 600 ? 4 : 2
                            columnSpacing: 14
                            rowSpacing: 4

                            ColumnLayout {
                                spacing: 1
                                Label { text: "INSTALLED"; font.family: Theme.fontFamily; font.pixelSize: 10; font.bold: true; color: Theme.textDim }
                                Label { text: (typeof Operational !== "undefined" && Operational) ? Operational.updaterCurrentVersion : "2026.03.04"; font.family: Theme.fontFamily; font.pixelSize: Theme.smallSize; color: Theme.text; elide: Text.ElideRight }
                            }
                            ColumnLayout {
                                spacing: 1
                                Label { text: "LATEST"; font.family: Theme.fontFamily; font.pixelSize: 10; font.bold: true; color: Theme.textDim }
                                Label { text: (typeof Operational !== "undefined" && Operational && Operational.updaterAvailableVersion !== "") ? Operational.updaterAvailableVersion : "Current"; font.family: Theme.fontFamily; font.pixelSize: Theme.smallSize; color: Theme.text; elide: Text.ElideRight }
                            }
                            ColumnLayout {
                                spacing: 1
                                Label { text: "STATUS"; font.family: Theme.fontFamily; font.pixelSize: 10; font.bold: true; color: Theme.textDim }
                                Label { text: (typeof Operational !== "undefined" && Operational && Operational.updaterUpdateAvailable) ? "Update available" : "Up to date"; font.family: Theme.fontFamily; font.pixelSize: Theme.smallSize; color: (typeof Operational !== "undefined" && Operational && Operational.updaterUpdateAvailable) ? Theme.accentHover : Theme.success }
                            }
                            ColumnLayout {
                                spacing: 1
                                Label { text: "SECURITY"; font.family: Theme.fontFamily; font.pixelSize: 10; font.bold: true; color: Theme.textDim }
                                Label { text: "Signed Package"; font.family: Theme.fontFamily; font.pixelSize: Theme.smallSize; color: Theme.textMuted }
                            }
                        }

                        // Actions Row
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            VPrimaryButton {
                                text: (typeof Operational !== "undefined" && Operational && Operational.updaterBusy) ? "Working..." : "Check Engine Update"
                                enabled: !(typeof Operational !== "undefined" && Operational && Operational.updaterBusy)
                                Layout.preferredHeight: 32
                                onClicked: Operational.checkUpdater()
                            }

                            VSecondaryButton {
                                text: "Install Engine Update"
                                enabled: !(typeof Operational !== "undefined" && Operational && Operational.updaterBusy) && (typeof Operational !== "undefined" && Operational && Operational.updaterUpdateAvailable)
                                visible: (typeof Operational !== "undefined" && Operational && Operational.updaterUpdateAvailable)
                                Layout.preferredHeight: 32
                                onClicked: Operational.installUpdate()
                            }

                            VSecondaryButton {
                                text: "Roll Back Engine"
                                enabled: !(typeof Operational !== "undefined" && Operational && Operational.updaterBusy)
                                Layout.preferredHeight: 32
                                onClicked: Operational.rollbackUpdate()
                            }
                        }

                        // Channel & Policy Options
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 12

                            ColumnLayout {
                                Layout.preferredWidth: 160
                                spacing: 2
                                Label { text: "UPDATE CHANNEL"; font.family: Theme.fontFamily; font.pixelSize: 10; font.bold: true; color: Theme.textDim }
                                VComboBox {
                                    id: channelCombo
                                    Layout.fillWidth: true
                                    model: ["Stable", "Nightly", "Master", "Pre-release"]
                                    currentIndex: model.indexOf(Settings.ytdlpChannel) !== -1 ? model.indexOf(Settings.ytdlpChannel) : 0
                                    onActivated: (idx) => Settings.ytdlpChannel = model[idx]
                                }
                            }

                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 4
                                VCheckBox {
                                    text: "Check update channel at startup (once per 24h)"
                                    checked: Settings.ytdlpCheckOnStartup
                                    onToggled: Settings.ytdlpCheckOnStartup = checked
                                }
                                VCheckBox {
                                    text: "Allow fetching official challenge-solver components"
                                    checked: Settings.allowRemoteComponents
                                    onToggled: Settings.allowRemoteComponents = checked
                                }
                            }
                        }
                    }
                }

                // Component 2 & 3: uBlock Origin Lite & Puemos Media Observer
                GridLayout {
                    Layout.fillWidth: true
                    columns: settingsScroll.availableWidth > 680 ? 2 : 1
                    columnSpacing: 12
                    rowSpacing: 12

                    // uBlock Origin Lite Card
                    Rectangle {
                        Layout.fillWidth: true
                        implicitHeight: ublockCol.implicitHeight + 20
                        radius: Theme.controlRadius
                        color: Theme.cardAlt
                        border.width: 1
                        border.color: Theme.border

                        ColumnLayout {
                            id: ublockCol
                            anchors.fill: parent
                            anchors.margins: 12
                            spacing: 8

                            RowLayout {
                                Layout.fillWidth: true
                                Label { text: "uBlock Origin Lite (uBOL)"; font.family: Theme.fontFamily; font.pixelSize: Theme.bodySize; font.bold: true; color: Theme.text }
                                Item { Layout.fillWidth: true }
                                Rectangle {
                                    radius: 4
                                    color: (typeof Operational !== "undefined" && Operational && Operational.ubolOperationalStatus === "Active") ? Theme.successSoft : Theme.errorSoft
                                    border.width: 1
                                    border.color: (typeof Operational !== "undefined" && Operational && Operational.ubolOperationalStatus === "Active") ? Theme.success : Theme.error
                                    implicitWidth: ubolVerText.implicitWidth + 12
                                    implicitHeight: 20

                                    Text {
                                        id: ubolVerText
                                        anchors.centerIn: parent
                                        text: (typeof Operational !== "undefined" && Operational && Operational.ubolOperationalStatus) ? Operational.ubolOperationalStatus.toUpperCase() : "ACTIVE"
                                        font.family: Theme.fontFamily
                                        font.pixelSize: 9
                                        font.bold: true
                                        color: (typeof Operational !== "undefined" && Operational && Operational.ubolOperationalStatus === "Active") ? Theme.success : Theme.error
                                    }
                                }
                            }

                            Label {
                                text: "Web content filter and ad blocking for isolated browser fallback."
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.microSize
                                color: Theme.textDim
                                wrapMode: Text.WordWrap
                                Layout.fillWidth: true
                            }

                            RowLayout {
                                Layout.fillWidth: true
                                ColumnLayout {
                                    spacing: 1
                                    Label { text: "INSTALLED"; font.family: Theme.fontFamily; font.pixelSize: 10; font.bold: true; color: Theme.textDim }
                                    Label { text: (typeof Operational !== "undefined" && Operational) ? Operational.ubolCurrentVersion : "1.0.4 (MV3)"; font.family: Theme.fontFamily; font.pixelSize: Theme.smallSize; color: Theme.text }
                                }
                                Item { Layout.fillWidth: true }
                                ColumnLayout {
                                    spacing: 1
                                    Label { text: "STATUS"; font.family: Theme.fontFamily; font.pixelSize: 10; font.bold: true; color: Theme.textDim }
                                    Label { text: (typeof Operational !== "undefined" && Operational) ? Operational.ubolStatusText : "Up to date"; font.family: Theme.fontFamily; font.pixelSize: Theme.smallSize; color: Theme.success }
                                }
                                Item { Layout.fillWidth: true }
                                VSecondaryButton {
                                    text: (typeof Operational !== "undefined" && Operational && Operational.ubolBusy) ? "Working..." : "Check Update"
                                    enabled: !(typeof Operational !== "undefined" && Operational && Operational.ubolBusy)
                                    Layout.preferredHeight: 30
                                    onClicked: Operational.checkUbolUpdate()
                                }
                                VPrimaryButton {
                                    text: "Install"
                                    visible: (typeof Operational !== "undefined" && Operational && Operational.ubolUpdateAvailable)
                                    enabled: !(typeof Operational !== "undefined" && Operational && Operational.ubolBusy)
                                    Layout.preferredHeight: 30
                                    onClicked: Operational.installUbolUpdate()
                                }
                            }
                        }
                    }

                    // Puemos Media Observer Card
                    Rectangle {
                        Layout.fillWidth: true
                        implicitHeight: puemosCol.implicitHeight + 20
                        radius: Theme.controlRadius
                        color: Theme.cardAlt
                        border.width: 1
                        border.color: Theme.border

                        ColumnLayout {
                            id: puemosCol
                            anchors.fill: parent
                            anchors.margins: 12
                            spacing: 8

                            RowLayout {
                                Layout.fillWidth: true
                                Label { text: "Puemos Media Observer"; font.family: Theme.fontFamily; font.pixelSize: Theme.bodySize; font.bold: true; color: Theme.text }
                                Item { Layout.fillWidth: true }
                                Rectangle {
                                    radius: 4
                                    color: (typeof Operational !== "undefined" && Operational && Operational.puemosOperationalStatus === "Active") ? Theme.successSoft : Theme.errorSoft
                                    border.width: 1
                                    border.color: (typeof Operational !== "undefined" && Operational && Operational.puemosOperationalStatus === "Active") ? Theme.success : Theme.error
                                    implicitWidth: puemosVerText.implicitWidth + 12
                                    implicitHeight: 20

                                    Text {
                                        id: puemosVerText
                                        anchors.centerIn: parent
                                        text: (typeof Operational !== "undefined" && Operational && Operational.puemosOperationalStatus) ? Operational.puemosOperationalStatus.toUpperCase() : "ACTIVE"
                                        font.family: Theme.fontFamily
                                        font.pixelSize: 9
                                        font.bold: true
                                        color: (typeof Operational !== "undefined" && Operational && Operational.puemosOperationalStatus === "Active") ? Theme.success : Theme.error
                                    }
                                }
                            }

                            Label {
                                text: "Passive background sensor for HLS/DASH media stream detection."
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.microSize
                                color: Theme.textDim
                                wrapMode: Text.WordWrap
                                Layout.fillWidth: true
                            }

                            RowLayout {
                                Layout.fillWidth: true
                                ColumnLayout {
                                    spacing: 1
                                    Label { text: "INSTALLED"; font.family: Theme.fontFamily; font.pixelSize: 10; font.bold: true; color: Theme.textDim }
                                    Label { text: (typeof Operational !== "undefined" && Operational) ? Operational.puemosCurrentVersion : "5.5.0 (MV3)"; font.family: Theme.fontFamily; font.pixelSize: Theme.smallSize; color: Theme.text }
                                }
                                Item { Layout.fillWidth: true }
                                ColumnLayout {
                                    spacing: 1
                                    Label { text: "STATUS"; font.family: Theme.fontFamily; font.pixelSize: 10; font.bold: true; color: Theme.textDim }
                                    Label { text: (typeof Operational !== "undefined" && Operational) ? Operational.puemosStatusText : "Up to date"; font.family: Theme.fontFamily; font.pixelSize: Theme.smallSize; color: Theme.success }
                                }
                                Item { Layout.fillWidth: true }
                                VSecondaryButton {
                                    text: (typeof Operational !== "undefined" && Operational && Operational.puemosBusy) ? "Working..." : "Check Update"
                                    enabled: !(typeof Operational !== "undefined" && Operational && Operational.puemosBusy)
                                    Layout.preferredHeight: 30
                                    onClicked: Operational.checkPuemosUpdate()
                                }
                                VPrimaryButton {
                                    text: "Install"
                                    visible: (typeof Operational !== "undefined" && Operational && Operational.puemosUpdateAvailable)
                                    enabled: !(typeof Operational !== "undefined" && Operational && Operational.puemosBusy)
                                    Layout.preferredHeight: 30
                                    onClicked: Operational.applyObserverUpdate()
                                }
                            }
                        }
                    }
                }
            }
        }

        // Section 4: Authentication & Cookies
        VCard {
            Layout.fillWidth: true
            headerTitle: "Authentication & Cookies"
            headerSubtitle: "Browser session extraction for restricted media"
            headerIcon: Qt.resolvedUrl("../../../assets/branding/v2icons/lock-accent-32.png")

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 12

                GridLayout {
                    Layout.fillWidth: true
                    columns: settingsScroll.availableWidth > 680 ? 2 : 1
                    columnSpacing: 14
                    rowSpacing: 8

                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.preferredWidth: 0
                        spacing: 4

                        Label {
                            text: "BROWSER COOKIE SOURCE"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.microSize
                            font.bold: true
                            color: Theme.textDim
                        }

                        VComboBox {
                            Layout.fillWidth: true
                            model: ["Disabled", "Auto-detect", "Chrome", "Firefox", "Edge", "Brave", "Opera", "Chromium", "Vivaldi", "Safari", "Custom File"]
                            currentIndex: model.indexOf(Settings.cookieMode) !== -1 ? model.indexOf(Settings.cookieMode) : 0
                            onActivated: (idx) => Settings.cookieMode = model[idx]
                        }
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.preferredWidth: 0
                        spacing: 4

                        Label {
                            text: "COOKIE PROFILE"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.microSize
                            font.bold: true
                            color: Theme.textDim
                        }

                        VTextField {
                            Layout.fillWidth: true
                            text: Settings.cookieProfile
                            placeholderText: "Default or profile name"
                            onEditingFinished: Settings.cookieProfile = text
                        }
                    }
                }

                ColumnLayout {
                    visible: Settings.cookieMode === "Custom File"
                    Layout.fillWidth: true
                    spacing: 4

                    Label {
                        text: "COOKIE FILE PATH"
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.microSize
                        font.bold: true
                        color: Theme.textDim
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 6

                        VTextField {
                            Layout.fillWidth: true
                            Layout.preferredWidth: 0
                            text: Settings.cookieFile
                            onEditingFinished: Settings.cookieFile = text
                        }

                        VSecondaryButton {
                            text: "Browse"
                            Layout.preferredHeight: Theme.controlHeight
                            onClicked: cookieFileDialog.open()
                        }
                    }
                }

                // Row 1 of buttons: Verification Window + Clear Session
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    VSecondaryButton {
                        text: "Open Verification Window"
                        Layout.fillWidth: true
                        Layout.preferredWidth: 0
                        Layout.preferredHeight: Theme.controlHeight
                        onClicked: Operational.openVerificationWindow()
                    }

                    VSecondaryButton {
                        text: "Clear Session"
                        Layout.fillWidth: true
                        Layout.preferredWidth: 0
                        Layout.preferredHeight: Theme.controlHeight
                        onClicked: Operational.clearBrowserSession()
                    }
                }

                // Row 2 of buttons: Retry After Verification
                VPrimaryButton {
                    text: "Retry After Verification"
                    Layout.fillWidth: true
                    Layout.preferredHeight: Theme.controlHeight
                    onClicked: Operational.retryAfterVerification()
                }
            }
        }

        // Section 5: Subtitles & Captions
        VCard {
            Layout.fillWidth: true
            headerTitle: "Subtitles & Captions"
            headerSubtitle: "Subtitle language filters and embedding rules"
            headerIcon: Qt.resolvedUrl("../../../assets/branding/v2icons/subtitles-accent-32.png")

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 10

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 4

                    Label {
                        text: "LANGUAGE REGEX PATTERN"
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.microSize
                        font.bold: true
                        color: Theme.textDim
                    }

                    VTextField {
                        Layout.fillWidth: true
                        text: Settings.subLangs
                        placeholderText: "en.*, ja, zh-Hans"
                        onEditingFinished: Settings.subLangs = text
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 6

                    VCheckBox {
                        Layout.fillWidth: true
                        text: "Embed subtitles into the video (remuxes to MKV)"
                        checked: Settings.embedSubs
                        onToggled: Settings.embedSubs = checked
                    }

                    VCheckBox {
                        Layout.fillWidth: true
                        text: "Include automatically generated captions"
                        checked: Settings.autoCaptions
                        onToggled: Settings.autoCaptions = checked
                    }

                    VCheckBox {
                        Layout.fillWidth: true
                        text: "Download matching subtitles by default"
                        checked: Settings.downloadSubs
                        onToggled: Settings.downloadSubs = checked
                    }
                }
            }
        }

        // Section 6: Media Filters & Metadata
        VCard {
            Layout.fillWidth: true
            headerTitle: "Media Filters & Metadata"
            headerSubtitle: "Cover art, ID3 tags, and SponsorBlock rules"
            headerIcon: Qt.resolvedUrl("../../../assets/branding/v2icons/music-accent-32.png")

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 10

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 6

                    VCheckBox {
                        Layout.fillWidth: true
                        text: "Embed video thumbnail as album cover art"
                        checked: Settings.embedThumbnail
                        onToggled: Settings.embedThumbnail = checked
                    }

                    VCheckBox {
                        Layout.fillWidth: true
                        text: "Embed title, artist, and available metadata tags"
                        checked: Settings.embedMetadata
                        onToggled: Settings.embedMetadata = checked
                    }

                    VCheckBox {
                        Layout.fillWidth: true
                        text: "Remove selected sponsor and advertisement segments"
                        checked: Settings.sponsorblock
                        onToggled: Settings.sponsorblock = checked
                    }
                }

                ColumnLayout {
                    visible: Settings.sponsorblock
                    Layout.fillWidth: true
                    spacing: 4

                    Label {
                        text: "SPONSORBLOCK CATEGORIES"
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.microSize
                        font.bold: true
                        color: Theme.textDim
                    }

                    VTextField {
                        Layout.fillWidth: true
                        text: Settings.sponsorblockCategories
                        placeholderText: "sponsor,selfpromo,interaction,intro,outro"
                        onEditingFinished: Settings.sponsorblockCategories = text
                    }
                }
            }
        }

        // Section 7: Network & File Output
        VCard {
            Layout.fillWidth: true
            headerTitle: "Network & File Output"
            headerSubtitle: "Proxy settings, bandwidth throttling, and filename constraints"
            headerIcon: Qt.resolvedUrl("../../../assets/branding/v2icons/gear-accent-32.png")

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 12

                GridLayout {
                    Layout.fillWidth: true
                    columns: settingsScroll.availableWidth > 680 ? 2 : 1
                    columnSpacing: 14
                    rowSpacing: 8

                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.preferredWidth: 0
                        spacing: 4

                        Label {
                            text: "PROXY SERVER URL"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.microSize
                            font.bold: true
                            color: Theme.textDim
                        }

                        VTextField {
                            Layout.fillWidth: true
                            text: Settings.proxy
                            placeholderText: "http://127.0.0.1:8080 or socks5://..."
                            onEditingFinished: Settings.proxy = text
                        }
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.preferredWidth: 0
                        spacing: 4

                        Label {
                            text: "RATE LIMIT"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.microSize
                            font.bold: true
                            color: Theme.textDim
                        }

                        VTextField {
                            Layout.fillWidth: true
                            text: Settings.rateLimit
                            placeholderText: "2M or 500K"
                            onEditingFinished: Settings.rateLimit = text
                        }
                    }
                }

                GridLayout {
                    Layout.fillWidth: true
                    columns: settingsScroll.availableWidth > 680 ? 2 : 1
                    columnSpacing: 14
                    rowSpacing: 8

                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.preferredWidth: 0
                        spacing: 4

                        Label {
                            text: "OUTPUT FILENAME TEMPLATE"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.microSize
                            font.bold: true
                            color: Theme.textDim
                        }

                        VTextField {
                            Layout.fillWidth: true
                            text: Settings.outputTemplate
                            placeholderText: "%(title)s [%(id)s].%(ext)s"
                            onEditingFinished: Settings.outputTemplate = text
                        }
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.preferredWidth: 0
                        spacing: 4

                        Label {
                            text: "CLIENT IMPERSONATION"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.microSize
                            font.bold: true
                            color: Theme.textDim
                        }

                        VComboBox {
                            Layout.fillWidth: true
                            model: ["Automatic", "Chrome", "Safari", "Edge", "Firefox", "iOS", "Android"]
                            currentIndex: model.indexOf(Settings.impersonation) !== -1 ? model.indexOf(Settings.impersonation) : 0
                            onActivated: (idx) => Settings.impersonation = model[idx]
                        }
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 4

                    Label {
                        text: "FORMAT SORTING (-S)"
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.microSize
                        font.bold: true
                        color: Theme.textDim
                    }

                    VTextField {
                        Layout.fillWidth: true
                        text: Settings.formatSort
                        placeholderText: "res,ext:mp4:m4a (optional format sort override)"
                        onEditingFinished: Settings.formatSort = text
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 6

                    VCheckBox {
                        Layout.fillWidth: true
                        text: "Force IPv4 connections"
                        checked: Settings.forceIpv4
                        onToggled: Settings.forceIpv4 = checked
                    }

                    VCheckBox {
                        Layout.fillWidth: true
                        text: "Restrict safe ASCII filenames"
                        checked: Settings.restrictFilenames
                        onToggled: Settings.restrictFilenames = checked
                    }

                    VCheckBox {
                        Layout.fillWidth: true
                        text: "Use download archive to skip duplicates"
                        checked: Settings.useArchive
                        onToggled: Settings.useArchive = checked
                    }
                }
            }
        }

        // Section 8: Browser Fallback Subsystem & Privacy
        VCard {
            Layout.fillWidth: true
            headerTitle: "Browser Fallback Subsystem & Privacy"
            headerSubtitle: "Isolated WebView2 stream inspection, uBlock Origin Lite, and session purge"
            headerIcon: Qt.resolvedUrl("../../../assets/branding/v2icons/lock-accent-32.png")

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 12

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10

                    VSecondaryButton {
                        text: "Clear Browser Session Data"
                        Layout.preferredHeight: 36
                        onClicked: {
                            var msg = Operational.clearBrowserSessionData();
                            settingsScroll.feedbackMessage = msg;
                        }
                    }

                    VSecondaryButton {
                        text: "Clear Active Session"
                        Layout.preferredHeight: 36
                        onClicked: Operational.clearBrowserSession()
                    }
                }

                Label {
                    Layout.fillWidth: true
                    text: "Clearing browser session data purges WebView2 cookies, cache, and DOM storage without deleting your download history, queued tasks, or application settings."
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.smallSize
                    color: Theme.textDim
                    wrapMode: Text.WordWrap
                }
            }
        }

        // Section 9: Custom yt-dlp Command
        VCard {
            Layout.fillWidth: true
            headerTitle: "Custom yt-dlp Command"
            headerSubtitle: "Direct CLI argument injection with safety gate"
            headerIcon: Qt.resolvedUrl("../../../assets/branding/v2icons/terminal-accent-32.png")

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 10

                VCheckBox {
                    Layout.fillWidth: true
                    text: "Enable custom command for the next queued download"
                    checked: Settings.useCustomCommand
                    onToggled: Settings.useCustomCommand = checked
                }

                // Balanced Warning Box (Shown when enabled)
                Rectangle {
                    visible: Settings.useCustomCommand
                    Layout.fillWidth: true
                    implicitHeight: safetyRow.implicitHeight + 16
                    radius: Theme.controlRadius
                    color: Theme.warningSoft
                    border.width: 1
                    border.color: Theme.warning

                    RowLayout {
                        id: safetyRow
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 8

                        Text {
                            text: "⚠"
                            font.family: Theme.fontFamily
                            font.pixelSize: 14
                            color: Theme.warning
                            Layout.alignment: Qt.AlignVCenter
                        }

                        Label {
                            Layout.fillWidth: true
                            Layout.alignment: Qt.AlignVCenter
                            text: "Custom command overrides normal format options for the next queued download."
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.smallSize
                            font.bold: true
                            color: Theme.warning
                            wrapMode: Text.WordWrap
                        }
                    }
                }

                VTextField {
                    Layout.fillWidth: true
                    enabled: Settings.useCustomCommand
                    text: Settings.customCommand
                    placeholderText: "--write-auto-subs --concurrent-fragments 4"
                    onEditingFinished: Settings.customCommand = text
                }
            }
        }

        // Section 10: System Diagnostics
        VCard {
            Layout.fillWidth: true
            headerTitle: "System Diagnostics"
            headerSubtitle: "Sanitized diagnostic export for troubleshooting"
            headerIcon: Qt.resolvedUrl("../../../assets/branding/v2icons/gear-accent-32.png")

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 10

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10

                    VPrimaryButton {
                        text: "Export Sanitized Diagnostics"
                        Layout.preferredHeight: 36
                        onClicked: {
                            Operational.exportSanitizedDiagnostics();
                            settingsScroll.feedbackMessage = "Sanitized diagnostics copied to system clipboard.";
                        }
                    }
                }

                Label {
                    Layout.fillWidth: true
                    text: "Diagnostic reports automatically redact cookies, authorization headers, passwords, and private parameters before export."
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.smallSize
                    color: Theme.textDim
                    wrapMode: Text.WordWrap
                }
            }
        }

        // Section 11: VRKA Application Updates (Placed Near Bottom, Immediately Above About VRKA)
        VCard {
            Layout.fillWidth: true
            headerTitle: "VRKA Application Updates"
            headerSubtitle: "Official release information and update status"
            headerIcon: Qt.resolvedUrl("../../../assets/branding/v2icons/gear-accent-32.png")

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 16

                // Application Release Metadata (2-Column Responsive Grid with Generous Spacing)
                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: appMetaCol.implicitHeight + 28
                    radius: Theme.controlRadius
                    color: Theme.cardAlt
                    border.width: 1
                    border.color: Theme.border

                    ColumnLayout {
                        id: appMetaCol
                        anchors.fill: parent
                        anchors.margins: 16
                        spacing: 16

                        GridLayout {
                            Layout.fillWidth: true
                            columns: settingsScroll.availableWidth > 540 ? 2 : 1
                            columnSpacing: 32
                            rowSpacing: 14

                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 3
                                Label {
                                    text: "Current Version"
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.smallSize
                                    font.bold: true
                                    color: Theme.textDim
                                }
                                Label {
                                    text: APP_DISPLAY_VERSION + " (Build " + APP_BUILD + ")"
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.bodySize
                                    font.bold: true
                                    color: Theme.text
                                }
                            }

                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 3
                                Label {
                                    text: "Latest Version"
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.smallSize
                                    font.bold: true
                                    color: Theme.textDim
                                }
                                Label {
                                    text: (typeof Operational !== "undefined" && Operational && Operational.appUpdateLatestVersion !== "") ? ("v" + Operational.appUpdateLatestVersion) : "Unknown"
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.bodySize
                                    font.bold: true
                                    color: Theme.text
                                }
                            }

                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 3
                                Label {
                                    text: "Release Channel"
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.smallSize
                                    font.bold: true
                                    color: Theme.textDim
                                }
                                Label {
                                    text: "Official GitHub"
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.bodySize
                                    color: Theme.textMuted
                                }
                            }

                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 3
                                Label {
                                    text: "Authenticity"
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.smallSize
                                    font.bold: true
                                    color: Theme.textDim
                                }
                                Label {
                                    text: "OpenPGP Signed"
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.bodySize
                                    font.bold: true
                                    color: Theme.success
                                }
                            }
                        }

                        // Status Row (Visually Distinct from Metadata)
                        Rectangle {
                            Layout.fillWidth: true
                            implicitHeight: Math.max(38, appStatusRow.implicitHeight + 12)
                            radius: Theme.controlRadius
                            color: Theme.card
                            border.width: 1
                            border.color: Theme.border

                            RowLayout {
                                id: appStatusRow
                                anchors.fill: parent
                                anchors.leftMargin: 12
                                anchors.rightMargin: 12
                                spacing: 8

                                Label {
                                    text: "Status:"
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.smallSize
                                    font.bold: true
                                    color: Theme.textDim
                                }

                                Label {
                                    Layout.fillWidth: true
                                    text: (typeof Operational !== "undefined" && Operational) ? Operational.appUpdateStatusText : "Ready to check for application updates."
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.bodySize
                                    color: (typeof Operational !== "undefined" && Operational && Operational.appUpdateAvailable) ? Theme.accentHover : Theme.text
                                    wrapMode: Text.WordWrap
                                }
                            }
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Layout.topMargin: 4
                    spacing: 12

                    VPrimaryButton {
                        text: (typeof Operational !== "undefined" && Operational && Operational.appUpdateBusy) ? "Checking..." : "Check for Updates"
                        enabled: !(typeof Operational !== "undefined" && Operational && Operational.appUpdateBusy)
                        Layout.preferredHeight: 38
                        onClicked: Operational.checkAppUpdate()
                    }

                    VSecondaryButton {
                        visible: (typeof Operational !== "undefined" && Operational && Operational.appUpdateAvailable)
                        text: "Download & Install v" + ((typeof Operational !== "undefined" && Operational) ? Operational.appUpdateLatestVersion : "")
                        enabled: !(typeof Operational !== "undefined" && Operational && Operational.appUpdateBusy)
                        Layout.preferredHeight: 38
                        onClicked: Operational.downloadAndInstallAppUpdate()
                    }
                }
            }
        }

        // Section 12: About VRKA (Mobile-App-Style Identity Layout)
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 16

            // Primary Identity Row: Left text + Right wolf logo (Inset)
            RowLayout {
                Layout.fillWidth: true
                Layout.rightMargin: 48
                spacing: 24

                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.preferredWidth: 0
                    Layout.alignment: Qt.AlignVCenter
                    spacing: 6

                    Label {
                        text: "VRKA v" + APP_DISPLAY_VERSION
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.displayTitleSize
                        font.bold: true
                        color: Theme.text
                    }

                    Label {
                        text: "By MVRK"
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.bodySize
                        font.bold: true
                        color: Theme.accentHover
                    }

                    Item { Layout.preferredHeight: 6 }

                    // GitHub link row
                    AbstractButton {
                        Layout.fillWidth: true
                        implicitHeight: 30
                        hoverEnabled: true
                        onClicked: Operational.openUrl("https://github.com/MaverickRox/VRKA")

                        contentItem: Label {
                            text: "GitHub"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.bodySize
                            color: parent.hovered ? Theme.accentHover : Theme.text
                            verticalAlignment: Text.AlignVCenter
                        }
                    }

                    // Third-Party Notices link row
                    AbstractButton {
                        Layout.fillWidth: true
                        implicitHeight: 30
                        hoverEnabled: true
                        onClicked: Operational.openNotices()

                        contentItem: Label {
                            text: "Third Party Notices"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.bodySize
                            color: parent.hovered ? Theme.accentHover : Theme.text
                            verticalAlignment: Text.AlignVCenter
                        }
                    }
                }

                // Large Wolf Logo (Vertically centered, inset from right edge)
                Image {
                    source: Qt.resolvedUrl("../../../assets/branding/vrka-wolf-256.png")
                    Layout.preferredWidth: 80
                    Layout.preferredHeight: 80
                    Layout.alignment: Qt.AlignVCenter
                    fillMode: Image.PreserveAspectFit
                    mipmap: true
                }
            }
        }

        Item { Layout.preferredHeight: 16 }
    }
}
