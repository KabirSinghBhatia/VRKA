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
        currentFolder: Settings.outputFolder ? ("file:///" + Settings.outputFolder.replace(/\\/g, "/")) : ""
        onAccepted: {
            var path = selectedFolder.toString().replace("file:///", "").replace(/\//g, "\\");
            Settings.outputFolder = path;
            Settings.save();
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
                    text: "Settings & System Preferences"
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.displayTitleSize
                    font.bold: true
                    color: Theme.text
                }

                Label {
                    Layout.fillWidth: true
                    text: "Configure application typography, destination modes, runtime maintenance, and security."
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

        // Section 1: Application Updates & Release Status
        VCard {
            Layout.fillWidth: true
            headerTitle: "VRKA Application Updates"
            headerSubtitle: "Official releases from GitHub repository (MaverickRox/VRKA)"
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

        // Section 2: Typography & Appearance (Phase 14)
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

        // Section 3: Download Destination Mode (Phase 15)
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
            }
        }

        // Section 5: Browser Fallback & Privacy (Phase 21)
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

        // Section 6: Diagnostics & Secret Sanitization (Phase 22)
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

                    VSecondaryButton {
                        text: "Third-Party Notices"
                        Layout.preferredHeight: 36
                        onClicked: Operational.openNotices()
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

        Item { Layout.preferredHeight: 16 }
    }
}
