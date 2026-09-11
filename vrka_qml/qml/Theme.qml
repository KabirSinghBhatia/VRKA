pragma Singleton
pragma ComponentBehavior: Bound
import QtQuick

QtObject {
    id: root

    property string mode: "dark"
    readonly property bool isLight: mode === "light"

    // Dynamic Typography Preference (VRKA Space Mono vs System Font)
    readonly property string fontFamily: (typeof Settings !== "undefined" && Settings && Settings.fontFamilyMode === "system")
                                         ? "Segoe UI Variable, Segoe UI, -apple-system, sans-serif"
                                         : "Space Mono"

    // Exact Authoritative VRKA Semantic Colors & AMOLED Surfaces
    readonly property color bg:              isLight ? "#FFFFFF" : "#000000"
    readonly property color sidebar:         isLight ? "#F7F7F8" : "#050505"
    readonly property color card:            isLight ? "#FFFFFF" : "#08080B"
    readonly property color cardAlt:         isLight ? "#F1F3F8" : "#0F0F14"
    readonly property color surfaceElevated: isLight ? "#E8ECF4" : "#16161D"
    readonly property color surfaceHover:    isLight ? "#DFE4EE" : "#1F1F2A"
    readonly property color border:          isLight ? "#DCE1EC" : "#1C1C24"
    readonly property color borderStrong:    isLight ? "#C5CCDC" : "#2E2E3C"

    // Subtle Translucent / Frosted Material Tokens (Material 0 - 4 & Android-inspired glass)
    readonly property color material0: bg
    readonly property color material1: sidebar
    readonly property color material2: card
    readonly property color material3: cardAlt
    readonly property color material4: surfaceElevated
    readonly property color glassBg:      isLight ? Qt.rgba(1.0, 1.0, 1.0, 0.88) : Qt.rgba(0.04, 0.02, 0.08, 0.85)
    readonly property color glassBorder:  isLight ? Qt.rgba(0.86, 0.88, 0.93, 0.9) : Qt.rgba(0.20, 0.14, 0.32, 0.45)
    
    // Genuinely Visible Frosted Sidebar Tokens
    readonly property color sidebarGlassTop:    isLight ? Qt.rgba(0.98, 0.98, 1.0, 0.96) : Qt.rgba(0.07, 0.04, 0.12, 0.92)
    readonly property color sidebarGlassMid:    isLight ? Qt.rgba(0.96, 0.96, 0.98, 0.94) : Qt.rgba(0.04, 0.02, 0.08, 0.94)
    readonly property color sidebarGlassBottom: isLight ? Qt.rgba(0.93, 0.94, 0.97, 0.96) : Qt.rgba(0.02, 0.01, 0.05, 0.97)
    readonly property color sidebarGlow:        isLight ? Qt.rgba(0.51, 0.25, 0.86, 0.05) : Qt.rgba(0.51, 0.25, 0.86, 0.14)
    readonly property color sidebarHighlight:   isLight ? Qt.rgba(1.0, 1.0, 1.0, 0.85) : Qt.rgba(0.70, 0.50, 0.98, 0.12)
    readonly property color sidebarBorder:      isLight ? "#DCE1EC" : Qt.rgba(0.38, 0.22, 0.58, 0.38)
    
    readonly property color titleBarBg:   isLight ? "#FFFFFF" : "#000000"
    readonly property color titleBarBorder: isLight ? "#DCE1EC" : "transparent"

    // VRKA Signature Accent (Refined purple)
    readonly property color accent:          "#8140DC"
    readonly property color accentHover:     "#9255E5"
    readonly property color accentPressed:   "#6E31C3"
    readonly property color accentSoft:      isLight ? "#F1E8FC" : "#180D24"
    readonly property color accentSoftHover: isLight ? "#E8D9FA" : "#241236"
    readonly property color focusRing:       "#9255E5"

    // Text hierarchy
    readonly property color text:         isLight ? "#111116" : "#FAF9FC"
    readonly property color textMuted:    isLight ? "#4E5262" : "#C8C4CF"
    readonly property color textDim:      isLight ? "#6E7488" : "#9893A4"
    readonly property color textDisabled: isLight ? "#9BA1B4" : "#686472"
    readonly property color textOnAccent: "#FFFFFF"

    // Status Semantics
    readonly property color success:      "#2BCB77"
    readonly property color successSoft:  isLight ? "#EBF9F1" : "#0B2215"
    readonly property color warning:      "#E7A93D"
    readonly property color warningSoft:  isLight ? "#FDF6EB" : "#261905"
    readonly property color error:        "#EF5A67"
    readonly property color errorSoft:    isLight ? "#FDEEF0" : "#2B0B10"

    // Spacing & geometry system
    readonly property int sidebarWidth:         240
    readonly property int titleBarHeight:       38
    readonly property int navButtonHeight:      44
    readonly property int controlHeight:        40
    readonly property int controlRadius:        8
    readonly property int cardRadius:           12
    readonly property int primaryButtonHeight:  44
    readonly property int secondaryButtonHeight: 40
    readonly property int pagePadX:             28
    readonly property int pagePadY:             20
    readonly property int cardPadX:             18
    readonly property int cardPadY:             16
    readonly property int panelGap:             14
    readonly property int hairline:             1

    // Typography Ramp
    readonly property int logoSize:         64
    readonly property int brandTitleSize:   22
    readonly property int displayTitleSize: 24
    readonly property int pageTitleSize:    20
    readonly property int sectionTitleSize: 15
    readonly property int bodySize:         13
    readonly property int smallSize:        12
    readonly property int microSize:        11
}
