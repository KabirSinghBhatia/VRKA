pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import QtQuick.Dialogs
import ".."
import "../components"

ScrollView {
    id: settingsScroll
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
                    text: "Settings & Preferences"
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.displayTitleSize
                    font.bold: true
                    color: Theme.text
                }

                Label {
                    Layout.fillWidth: true
                    text: "Configure application updates, downloader engine, browser sessions, network, and security."
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

        // Section 1: Application Updates & Release Status (OpenPGP Authenticated)
        VCard {
            Layout.fillWidth: true
            headerTitle: "VRKA Application Updates"
            headerSubtitle: "Official releases from GitHub repository (MaverickRox/VRKA) with OpenPGP authenticity"
            headerIcon: Qt.resolvedUrl("../../../assets/branding/v2icons/gear-accent-32.png")

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 12

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10

                    VPrimaryButton {
                        text: (typeof Operational !== "undefined" && Operational && Operational.appUpdateBusy) ? "Checking..." : "Check for Updates"
                        enabled: !(typeof Operational !== "undefined" && Operational && Operational.appUpdateBusy)
                        Layout.preferredHeight: 36
                        onClicked: Operational.checkAppUpdate()
                    }

                    VSecondaryButton {
                        visible: (typeof Operational !== "undefined" && Operational && Operational.appUpdateAvailable)
                        text: "Download & Install v" + ((typeof Operational !== "undefined" && Operational) ? Operational.appUpdateLatestVersion : "")
                        enabled: !(typeof Operational !== "undefined" && Operational && Operational.appUpdateBusy)
                        Layout.preferredHeight: 36
                        onClicked: Operational.downloadAndInstallAppUpdate()
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: Math.max(38, updateStatusRow.implicitHeight + 14)
                    radius: Theme.controlRadius
                    color: Theme.cardAlt
                    border.width: 1
                    border.color: Theme.border

                    RowLayout {
                        id: updateStatusRow
                        anchors.fill: parent
                        anchors.margins: 12
                        spacing: 8

                        Label {
                            text: "Status:"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.microSize
                            font.bold: true
                            color: Theme.textDim
                        }

                        Label {
                            Layout.fillWidth: true
                            text: (typeof Operational !== "undefined" && Operational) ? Operational.appUpdateStatusText : "Up to date"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.bodySize
                            color: (typeof Operational !== "undefined" && Operational && Operational.appUpdateAvailable) ? Theme.accentHover : Theme.text
                            wrapMode: Text.WordWrap
                        }
                    }
                }
            }
        }

        // Section 2: Typography & Appearance
        VCard {
            Layout.fillWidth: true
            headerTitle: "Typography & Interface Appearance"
            headerSubtitle: "Customize application font style and day/night theme"
            headerIcon: Qt.resolvedUrl("../../../assets/branding/v2icons/gear-accent-32.png")

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 12

                GridLayout {
                    Layout.fillWidth: true
                    columns: settingsScroll.availableWidth > 680 ? 2 : 1
                    columnSpacing: 18
                    rowSpacing: 10

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4

                        Label {
                            text: "APPLICATION FONT FAMILY"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.microSize
                            font.bold: true
                            color: Theme.textDim
                        }

                        VComboBox {
                            id: fontCombo
                            Layout.fillWidth: true
                            model: ["VRKA Monospace (Space Mono)", "System UI Font (Segoe UI)"]
                            currentIndex: Settings.fontFamilyMode === "system" ? 1 : 0
                            onActivated: (idx) => {
                                Settings.fontFamilyMode = idx === 1 ? "system" : "vrka"
                            }
                        }
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4

                        Label {
                            text: "COLOR PALETTE THEME"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.microSize
                            font.bold: true
                            color: Theme.textDim
                        }

                        VComboBox {
                            id: themeModeCombo
                            Layout.fillWidth: true
                            model: ["Dark Theme", "Light Theme"]
                            currentIndex: Theme.isLight ? 1 : 0
                            onActivated: (idx) => {
                                Theme.mode = idx === 1 ? "light" : "dark"
                                Settings.appearanceMode = idx === 1 ? "Light" : "Dark"
                            }
                        }
                    }
                }
            }
        }

        // Section 3: Download Destination Mode
        VCard {
            Layout.fillWidth: true
            headerTitle: "Download Destination & Location Mode"
            headerSubtitle: "Control how VRKA determines download target folders"
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

        // Section 4: Engine Components & Downloader Core
        VCard {
            Layout.fillWidth: true
            headerTitle: "Engine Components & Downloader Core"
            headerSubtitle: "Isolated update pipeline with atomic stage and SHA-256 verification"
            headerIcon: Qt.resolvedUrl("../../../assets/branding/v2icons/gear-accent-32.png")

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 12

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    VPrimaryButton {
                        text: (typeof Operational !== "undefined" && Operational && Operational.updaterBusy) ? "Working..." : "Check Engine Update"
                        enabled: !(typeof Operational !== "undefined" && Operational && Operational.updaterBusy)
                        Layout.preferredHeight: 34
                        onClicked: Operational.checkUpdater()
                    }

                    VSecondaryButton {
                        text: "Install Engine Update"
                        enabled: !(typeof Operational !== "undefined" && Operational && Operational.updaterBusy) && (typeof Operational !== "undefined" && Operational && Operational.updaterUpdateAvailable)
                        visible: (typeof Operational !== "undefined" && Operational && Operational.updaterUpdateAvailable)
                        Layout.preferredHeight: 34
                        onClicked: Operational.installUpdate()
                    }

                    VSecondaryButton {
                        text: "Roll Back Engine"
                        enabled: !(typeof Operational !== "undefined" && Operational && Operational.updaterBusy)
                        Layout.preferredHeight: 34
                        onClicked: Operational.rollbackUpdate()
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: Math.max(38, engineStatusRow.implicitHeight + 14)
                    radius: Theme.controlRadius
                    color: Theme.cardAlt
                    border.width: 1
                    border.color: Theme.border

                    RowLayout {
                        id: engineStatusRow
                        anchors.fill: parent
                        anchors.margins: 12
                        spacing: 8

                        Label {
                            text: "yt-dlp Status:"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.microSize
                            font.bold: true
                            color: Theme.textDim
                        }

                        Label {
                            Layout.fillWidth: true
                            text: (typeof Operational !== "undefined" && Operational) ? Operational.updaterStatusText : "Current engine operational"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.bodySize
                            color: Theme.text
                            wrapMode: Text.WordWrap
                        }
                    }
                }

                ColumnLayout {
                    Layout.preferredWidth: 240
                    Layout.maximumWidth: 240
                    Layout.fillWidth: false
                    spacing: 4

                    Label {
                        text: "UPDATE CHANNEL"
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.microSize
                        font.bold: true
                        color: Theme.textDim
                    }

                    VComboBox {
                        id: channelCombo
                        Layout.fillWidth: true
                        model: ["Stable", "Nightly", "Master", "Pre-release"]
                        currentIndex: model.indexOf(Settings.ytdlpChannel) !== -1 ? model.indexOf(Settings.ytdlpChannel) : 0
                        onActivated: (idx) => Settings.ytdlpChannel = model[idx]
                    }
                }

                VCheckBox {
                    Layout.fillWidth: true
                    text: "Check update channel at startup (once per 24h)"
                    checked: Settings.ytdlpCheckOnStartup
                    onToggled: Settings.ytdlpCheckOnStartup = checked
                }

                VCheckBox {
                    Layout.fillWidth: true
                    text: "Allow yt-dlp to fetch official challenge-solver components when required"
                    checked: Settings.allowRemoteComponents
                    onToggled: Settings.allowRemoteComponents = checked
                }
            }
        }

        // Section 5: Authentication & Cookies
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

        // Section 6: Subtitles & Captions
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

        // Section 7: Media Filters & Metadata
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

        // Section 8: Network & File Output
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

        // Section 9: Passive Media Observer
        VCard {
            Layout.fillWidth: true
            headerTitle: "Passive Media Observer"
            headerSubtitle: "Background browser media stream detection & uBOL coexistence"
            headerIcon: Qt.resolvedUrl("../../../assets/branding/v2icons/terminal-accent-32.png")

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 12

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredWidth: 0
                        implicitHeight: Math.max(38, obsRow.implicitHeight + 14)
                        radius: Theme.controlRadius
                        color: Theme.cardAlt
                        border.width: 1
                        border.color: Theme.border

                        RowLayout {
                            id: obsRow
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.leftMargin: 12
                            anchors.rightMargin: 12
                            spacing: 8

                            Label {
                                text: "Observer Status:"
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.microSize
                                font.bold: true
                                color: Theme.textDim
                            }

                            Label {
                                Layout.fillWidth: true
                                Layout.preferredWidth: 0
                                text: (typeof Operational !== "undefined" && Operational && Operational.observerStatusText !== "") ? Operational.observerStatusText : "Passive sensor operational."
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.microSize
                                color: Theme.text
                                wrapMode: Text.WordWrap
                            }
                        }
                    }

                    VSecondaryButton {
                        text: "Check Update"
                        Layout.preferredHeight: 38
                        onClicked: Operational.checkObserverUpdate()
                    }

                    VPrimaryButton {
                        text: "Apply Update"
                        Layout.preferredHeight: 38
                        onClicked: Operational.applyObserverUpdate()
                    }
                }

                Label {
                    Layout.fillWidth: true
                    text: "Component Updates: Integrated uBlock Origin Lite (uBOL) and Puemos media observer modules operate passively alongside the downloader core."
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.microSize
                    color: Theme.textDim
                    wrapMode: Text.WordWrap
                }
            }
        }

        // Section 10: Browser Fallback Subsystem & Privacy
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

        // Section 11: Advanced: Explicit Custom yt-dlp Command
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: advancedCol.implicitHeight + 28
            radius: Theme.cardRadius
            color: Theme.card
            border.width: 1
            border.color: Settings.useCustomCommand ? Theme.warning : Theme.border

            ColumnLayout {
                id: advancedCol
                anchors.fill: parent
                anchors.margins: 14
                spacing: 10

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10

                    Image {
                        source: Qt.resolvedUrl("../../../assets/branding/v2icons/terminal-accent-32.png")
                        Layout.preferredWidth: 16
                        Layout.preferredHeight: 16
                        fillMode: Image.PreserveAspectFit
                        mipmap: true
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.preferredWidth: 0
                        spacing: 2

                        Label {
                            text: "Advanced: Explicit Custom yt-dlp Command"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.sectionTitleSize
                            font.bold: true
                            color: Settings.useCustomCommand ? Theme.warning : Theme.text
                        }

                        Label {
                            text: "Direct CLI argument injection with safety gate"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.microSize
                            color: Theme.textDim
                        }
                    }
                }

                VCheckBox {
                    Layout.fillWidth: true
                    text: "I understand: use this custom command for the next queued download"
                    checked: Settings.useCustomCommand
                    onToggled: Settings.useCustomCommand = checked
                }

                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: safetyCol.implicitHeight + 14
                    radius: Theme.controlRadius
                    color: Theme.warningSoft
                    border.width: 1
                    border.color: Theme.warning
                    opacity: Settings.useCustomCommand ? 1.0 : 0.6

                    ColumnLayout {
                        id: safetyCol
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 2

                        Label {
                            Layout.fillWidth: true
                            Layout.preferredWidth: 0
                            text: "SAFETY GATE / Text below is inert until the checkbox is explicitly enabled. Custom mode overrides most normal format options."
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.microSize
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

        // Section 12: System Diagnostics
        VCard {
            Layout.fillWidth: true
            headerTitle: "System Diagnostics & Telemetry"
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

        // Section 13: About VRKA (Wolf Branding, Version, Author, GitHub Link, Third-Party Notices)
        VCard {
            Layout.fillWidth: true
            headerTitle: "About VRKA"
            headerSubtitle: "Engine metadata, copyright, author attribution, and third-party notices"
            headerIcon: Qt.resolvedUrl("../../../assets/branding/vrka-wolf-256.png")

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 14

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 16

                    Image {
                        source: Qt.resolvedUrl("../../../assets/branding/vrka-wolf-256.png")
                        Layout.preferredWidth: 52
                        Layout.preferredHeight: 52
                        fillMode: Image.PreserveAspectFit
                        mipmap: true
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.preferredWidth: 0
                        spacing: 2

                        Label {
                            text: "VRKA Media Engine — v" + APP_DISPLAY_VERSION
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.bodySize
                            font.bold: true
                            color: Theme.text
                        }

                        Label {
                            text: "By MVRK"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.smallSize
                            font.bold: true
                            color: Theme.accentHover
                        }

                        Label {
                            text: "High-performance generic media downloader and passive web capture suite."
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.smallSize
                            color: Theme.textMuted
                        }
                    }
                }

                // Hairline divider
                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: Theme.hairline
                    color: Theme.border
                }

                // GitHub Repository Link Row
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 12

                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.preferredWidth: 0
                        spacing: 2

                        Label {
                            text: "GitHub Repository"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.bodySize
                            font.bold: true
                            color: Theme.text
                        }

                        Label {
                            text: "https://github.com/MaverickRox/VRKA"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.smallSize
                            color: Theme.textDim
                        }
                    }

                    VSecondaryButton {
                        text: "View Source ↗"
                        Layout.preferredHeight: 34
                        onClicked: Operational.openUrl("https://github.com/MaverickRox/VRKA")
                    }
                }

                // Third-Party Notices Action Row
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 12

                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.preferredWidth: 0
                        spacing: 2

                        Label {
                            text: "Third-Party Notices"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.bodySize
                            font.bold: true
                            color: Theme.text
                        }

                        Label {
                            text: "yt-dlp, FFmpeg, WebView2, uBlock Origin Lite, Puemos, Space Mono licenses"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.smallSize
                            color: Theme.textDim
                        }
                    }

                    VSecondaryButton {
                        text: "View Notices"
                        Layout.preferredHeight: 34
                        onClicked: Operational.openNotices()
                    }
                }
            }
        }

        Item { Layout.preferredHeight: 16 }
    }
}
