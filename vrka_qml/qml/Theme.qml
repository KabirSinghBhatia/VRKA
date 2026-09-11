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
    readonly property color bg:              isLight ? "#F8F8F8" : "#000000"
    readonly property color sidebar:         isLight ? "#EDEDED" : "#070707"
    readonly property color card:            isLight ? "#FFFFFF" : "#070707"
    readonly property color cardAlt:         isLight ? "#F2F2F2" : "#0E0E0E"
    readonly property color surfaceElevated: isLight ? "#E6E6E6" : "#141414"
    readonly property color surfaceHover:    isLight ? "#DCDCDC" : "#1B1B1B"
    readonly property color border:          isLight ? "#DFDFDF" : "#161616"
    readonly property color borderStrong:    isLight ? "#C8C8C8" : "#262626"

    // Subtle Translucent / Frosted Material Tokens (Material 0 - 4 & Neutral Frosted Glass)
    readonly property color material0: bg
    readonly property color material1: sidebar
    readonly property color material2: card
    readonly property color material3: cardAlt
    readonly property color material4: surfaceElevated
    readonly property color glassBg:      isLight ? Qt.rgba(0.96, 0.96, 0.96, 0.88) : Qt.rgba(0.04, 0.04, 0.04, 0.85)
    readonly property color glassBorder:  isLight ? Qt.rgba(0.85, 0.85, 0.85, 0.8)  : Qt.rgba(0.16, 0.16, 0.16, 0.35)
    
    // Completely Neutral Floating Sidebar Island Tokens (R=G=B, Zero Purple/Blue/Lavender)
    readonly property color sidebarBg:          isLight ? "#EDEDED" : "#0A0A0A"
    readonly property color sidebarBorder:      isLight ? "#D8D8D8" : "#1A1A1A"
    readonly property color sidebarHighlight:   isLight ? Qt.rgba(1.0, 1.0, 1.0, 0.7) : Qt.rgba(1.0, 1.0, 1.0, 0.03)
    readonly property color sidebarGlassTop:    isLight ? "#EDEDED" : "#0A0A0A"
    readonly property color sidebarGlassMid:    isLight ? "#EDEDED" : "#0A0A0A"
    readonly property color sidebarGlassBottom: isLight ? "#EDEDED" : "#0A0A0A"
    readonly property int   sidebarRadius:      12
    
    readonly property color titleBarBg:     isLight ? "#F8F8F8" : "#000000"
    readonly property color titleBarBorder: isLight ? "#DFDFDF" : "transparent"

    // VRKA Signature Accent (Refined purple strictly for active controls, badges, and primary buttons)
    readonly property color accent:          "#8140DC"
    readonly property color accentHover:     "#9255E5"
    readonly property color accentPressed:   "#6E31C3"
    readonly property color accentSoft:      isLight ? "#EEE6FC" : "#180D24"
    readonly property color accentSoftHover: isLight ? "#E4D5FA" : "#241236"
    readonly property color focusRing:       "#9255E5"

    // Text hierarchy
    readonly property color text:         isLight ? "#111116" : "#FAF9FC"
    readonly property color textMuted:    isLight ? "#454350" : "#C8C4CF"
    readonly property color textDim:      isLight ? "#6A6778" : "#9893A4"
    readonly property color textDisabled: isLight ? "#9894A6" : "#686472"
    readonly property color textOnAccent: "#FFFFFF"

    // Status Semantics
    readonly property color success:      isLight ? "#16A34A" : "#2BCB77"
    readonly property color successSoft:  isLight ? "#EBF9F1" : "#0B2215"
    readonly property color warning:      isLight ? "#D97706" : "#E7A93D"
    readonly property color warningSoft:  isLight ? "#FEF3C7" : "#261905"
    readonly property color error:        isLight ? "#DC2626" : "#EF5A67"
    readonly property color errorSoft:    isLight ? "#FEE2E2" : "#2B0B10"

    // Spacing & geometry system
    readonly property int sidebarWidth:         232
    readonly property int titleBarHeight:       38
    readonly property int navButtonHeight:      38
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
