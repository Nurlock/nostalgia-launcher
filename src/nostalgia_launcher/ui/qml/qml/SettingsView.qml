// Settings dialog (Phase 6a): Game /
// Sources / Profiles / Troubleshooting tabs. Reads the `settingsModel`
// context property (ui/qml/settings.py:SettingsModel). Modal in-app
// dialog (blocks the main window; the session log stays an independent
// window so it can be watched while interacting with the app). Hosts
// the Linux (UMU) dialog and the profile-import wizard (Phase 6b).

pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material
import QtQuick.Dialogs
import QtQuick.Layouts

Dialog {
    id: root
    objectName: "qmlSettingsDialog"
    title: "Settings"
    modal: true
    // Fill 95% of the mother window; the tab container fills the dialog.
    // No footer (the header ✕ closes).
    width: parent.width * 0.95
    height: parent.height * 0.95
    anchors.centerIn: parent
    padding: 0
    topPadding: 0
    bottomPadding: 0
    leftPadding: 0
    rightPadding: 0

    header: ToolBar {
        background: Rectangle {
            color: appTheme.colors["C_HDR"]
        }
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 16
            anchors.rightMargin: 8
            Label {
                Layout.fillWidth: true
                verticalAlignment: Text.AlignVCenter
                text: "SETTINGS"
                font.bold: true
                font.pointSize: 13
                color: appTheme.colors["C_GOLD_LT"]
                elide: Text.ElideRight
            }
            ToolButton {
                objectName: "qmlSettingsClose"
                text: "✕"
                Accessible.name: "Close"
                ToolTip.text: "Close"
                ToolTip.visible: hovered
                onClicked: root.reject()
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        TabBar {
            id: settingsTabs
            objectName: "qmlSettingsTabs"
            Layout.fillWidth: true
            TabButton { text: "Game" }
            TabButton { text: "Sources" }
            TabButton { text: "Profiles" }
            TabButton { text: "Troubleshooting" }
        }

        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: settingsTabs.currentIndex

            // ── Game ────────────────────────────────────────────
            ScrollView {
                clip: true
                contentWidth: availableWidth
                ColumnLayout {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.leftMargin: 16
                    anchors.rightMargin: 16
                    anchors.topMargin: 16
                    anchors.bottomMargin: 16
                    spacing: 8
                    Label {
                        text: "GAME FOLDER"
                        font.bold: true
                        font.pointSize: 10
                        color: appTheme.colors["C_GOLD"]
                    }
                    TextField {
                        Accessible.name: "GAME FOLDER"
                        objectName: "qmlSettingsPath"
                        Layout.fillWidth: true
                        text: settingsModel ? settingsModel.gamePath : ""
                        readOnly: true
                        selectByMouse: true
                        placeholderText: text === "" ? ((settingsModel && settingsModel.gameSuggestion !== "") ? settingsModel.gameSuggestion : "Select the game folder containing WoW.exe") : ""
                        placeholderTextColor: appTheme.colors["C_TEXT_DIM"]
                        font.family: "monospace"
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        Button {
                            objectName: "qmlSettingsChange"
                            text: "Change"
                            onClicked: folderPicker.open()
                        }
                        Button {
                            text: "Open folder"
                            flat: true
                            onClicked: if (settingsModel) settingsModel.openClientFolder()
                        }
                        Item { Layout.fillWidth: true }
                    }
                    Label {
                        text: "GENERAL"
                        font.bold: true
                        font.pointSize: 10
                        color: appTheme.colors["C_GOLD"]
                    }
                    CheckBox {
                        objectName: "qmlSettingsClearWdb"
                        text: "Clear WDB on game launch"
                        visible: settingsModel ? settingsModel.canLaunch : false
                        checked: settingsModel ? settingsModel.clearWdb : false
                        onToggled: if (settingsModel) settingsModel.setClearWdb(checked)
                    }
                    CheckBox {
                        objectName: "qmlSettingsCloseOnLaunch"
                        text: "Close Nostalgia Launcher on game launch"
                        visible: settingsModel ? settingsModel.canLaunch : false
                        checked: settingsModel ? settingsModel.closeOnLaunch : false
                        onToggled: if (settingsModel) settingsModel.setCloseOnLaunch(checked)
                    }
                    CheckBox {
                        objectName: "qmlSettingsWarp"
                        text: "Route game traffic via WARP tunnel"
                        visible: settingsModel ? settingsModel.canLaunch : false
                        checked: settingsModel ? settingsModel.warpEnabled : false
                        onToggled: if (settingsModel) settingsModel.setWarpEnabled(checked)
                    }
                    CheckBox {
                        objectName: "qmlSettingsClientUpdate"
                        text: "Enable client updates"
                        checked: settingsModel ? settingsModel.clientUpdates : false
                        onToggled: if (settingsModel) settingsModel.setClientUpdates(checked)
                    }
                    Button {
                        objectName: "qmlSettingsLinuxButton"
                        text: "Linux (UMU) Settings…"
                        visible: settingsModel ? settingsModel.isLinux : false
                        flat: true
                        onClicked: if (settingsModel) settingsModel.requestLinux()
                    }
                    Item { Layout.fillHeight: true }
                }
            }

            // ── Sources ─────────────────────────────────────────
            ScrollView {
                clip: true
                contentWidth: availableWidth
                ColumnLayout {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.leftMargin: 16
                    anchors.rightMargin: 16
                    anchors.topMargin: 16
                    anchors.bottomMargin: 16
                    spacing: 8
                    Label {
                        text: "DOWNLOAD SOURCE"
                        font.bold: true
                        font.pointSize: 10
                        color: appTheme.colors["C_GOLD"]
                    }
                    Repeater {
                        model: settingsModel ? settingsModel.sources : []
                        RowLayout {
                            id: sourceRow
                            required property var modelData
                            width: parent.width
                            Label {
                                text: "●"
                                color: sourceRow.modelData.status === "online" ? appTheme.colors["C_OK"] : (sourceRow.modelData.status === "offline" ? appTheme.colors["C_ERR"] : appTheme.colors["C_TEXT_DIM"])
                            }
                            Label {
                                text: sourceRow.modelData.name
                                font.bold: true
                                font.pointSize: 10
                                color: appTheme.colors["C_TEXT"]
                            }
                            Label {
                                text: sourceRow.modelData.status
                                font.pointSize: 9
                                color: appTheme.colors["C_TEXT_DIM"]
                            }
                        }
                    }
                    Button {
                        objectName: "qmlSettingsSourceRefresh"
                        text: "⟳  Check source"
                        flat: true
                        onClicked: if (settingsModel) settingsModel.checkSources()
                    }
                    Label {
                        text: "CATALOG REGISTRIES"
                        font.bold: true
                        font.pointSize: 10
                        color: appTheme.colors["C_GOLD"]
                    }
                    CheckBox {
                        text: "Use community default addons catalog"
                        enabled: settingsModel ? settingsModel.addonsDefaultAvail : false
                        checked: settingsModel ? (settingsModel.addonsDefault && settingsModel.addonsDefaultAvail) : false
                        onToggled: if (settingsModel) settingsModel.setAddonsDefault(checked)
                    }
                    CheckBox {
                        text: "Use community default mods catalog"
                        enabled: settingsModel ? settingsModel.modsDefaultAvail : false
                        checked: settingsModel ? (settingsModel.modsDefault && settingsModel.modsDefaultAvail) : false
                        onToggled: if (settingsModel) settingsModel.setModsDefault(checked)
                    }
                    RegistryRow {
                        label: "ADDONS"
                        url: settingsModel ? settingsModel.addonsUrl : ""
                        onApply: (text) => { if (settingsModel) settingsModel.applyAddonsUrl(text) }
                        onReset: () => { if (settingsModel) settingsModel.resetAddonsUrl() }
                        onReload: () => { if (settingsModel) settingsModel.reloadAddons() }
                        onOpenCustom: () => { if (settingsModel) settingsModel.openAddonsCustom() }
                        onClearCustom: () => { if (settingsModel) settingsModel.clearAddonsCustom() }
                    }
                    RegistryRow {
                        label: "MODS"
                        url: settingsModel ? settingsModel.modsUrl : ""
                        onApply: (text) => { if (settingsModel) settingsModel.applyModsUrl(text) }
                        onReset: () => { if (settingsModel) settingsModel.resetModsUrl() }
                        onReload: () => { if (settingsModel) settingsModel.reloadMods() }
                        onOpenCustom: () => { if (settingsModel) settingsModel.openModsCustom() }
                        onClearCustom: () => { if (settingsModel) settingsModel.clearModsCustom() }
                    }
                    Label {
                        objectName: "qmlSettingsRegistryStatus"
                        Layout.fillWidth: true
                        text: settingsModel ? settingsModel.registryStatus : ""
                        font.pointSize: 9
                        color: appTheme.colors["C_ERR"]
                        wrapMode: Text.WordWrap
                        visible: settingsModel ? settingsModel.registryStatus !== "" : false
                    }
                    Item { Layout.fillHeight: true }
                }
            }

            // ── Profiles ────────────────────────────────────────
            ScrollView {
                clip: true
                contentWidth: availableWidth
                ColumnLayout {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.leftMargin: 16
                    anchors.rightMargin: 16
                    anchors.topMargin: 16
                    anchors.bottomMargin: 16
                    spacing: 8
                    Label {
                        text: "PROFILES"
                        font.bold: true
                        font.pointSize: 10
                        color: appTheme.colors["C_GOLD"]
                    }
                    Label {
                        Layout.fillWidth: true
                        text: "One profile per server — importing a configuration creates its profile, named after the server. Switch profiles from the selector in the main-window header; switching restarts the launcher."
                        font.pointSize: 9
                        color: appTheme.colors["C_TEXT_DIM"]
                        wrapMode: Text.WordWrap
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        ComboBox {
                            Accessible.name: "Profiles"
                            id: profilesCombo
                            objectName: "qmlProfilesCombo"
                            Layout.fillWidth: true
                            Layout.minimumWidth: 120
                            model: settingsModel ? settingsModel.profiles : []
                            currentIndex: Math.max(0, settingsModel ? settingsModel.profiles.indexOf(settingsModel.activeProfile) : 0)
                            // Elide long server names so Import/Delete stay
                            // visible (same pattern as the header combo).
                            contentItem: Text {
                                text: profilesCombo.displayText
                                elide: Text.ElideRight
                                verticalAlignment: Text.AlignVCenter
                                leftPadding: 8
                                rightPadding: 28
                                color: appTheme.colors["C_TEXT"]
                            }
                        }
                        Button {
                            objectName: "qmlProfilesImport"
                            text: "Import…"
                            onClicked: {
                                wizard.reset();
                                importWizard.open();
                            }
                        }
                        Button {
                            objectName: "qmlProfilesDelete"
                            text: "Delete"
                            onClicked: deleteConfirm.open()
                        }
                    }
                    Label {
                        objectName: "qmlProfilesStatus"
                        Layout.fillWidth: true
                        text: settingsModel ? settingsModel.profilesStatus : ""
                        font.pointSize: 9
                        color: appTheme.colors["C_ERR"]
                        wrapMode: Text.WordWrap
                        visible: settingsModel ? settingsModel.profilesStatus !== "" : false
                    }
                    Item { Layout.fillHeight: true }
                }
            }

            // ── Troubleshooting ─────────────────────────────────
            ScrollView {
                clip: true
                contentWidth: availableWidth
                ColumnLayout {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.leftMargin: 16
                    anchors.rightMargin: 16
                    anchors.topMargin: 16
                    anchors.bottomMargin: 16
                    spacing: 8
                    Label {
                        text: "TROUBLESHOOTING"
                        font.bold: true
                        font.pointSize: 10
                        color: appTheme.colors["C_GOLD"]
                    }
                    Button {
                        objectName: "qmlSettingsVerify"
                        text: "✓  Verify game files"
                        flat: true
                        onClicked: if (settingsModel) settingsModel.verifyFiles()
                    }
                    Button {
                        objectName: "qmlSettingsLogs"
                        text: (settingsModel && settingsModel.logsOpen) ? "Hide logs" : "Show logs"
                        flat: true
                        onClicked: if (settingsModel) settingsModel.requestLogs()
                    }
                    Button {
                        objectName: "qmlSettingsAv"
                        text: "⛊  Add game folder to Defender exclusions"
                        visible: settingsModel ? settingsModel.canAntivirus : false
                        flat: true
                        onClicked: if (settingsModel) settingsModel.allowAntivirus()
                    }
                    Item { Layout.fillHeight: true }
                }
            }
        }
    }

    // No footer: the header ✕ closes (DialogButtonBox.Close added a
    // full-width white bar that ate the bottom of every tab).
    FolderDialog {
        id: folderPicker
        objectName: "qmlSettingsFolderPicker"
        title: "Select game client folder"
        onAccepted: if (settingsModel) settingsModel.setGameFolder(selectedFolder.toString().replace(/^file:\/\//, ""))
    }

    MessageDialog {
        id: deleteConfirm
        title: "Delete profile"
        text: "Delete this profile? Its server config, state and caches will be removed."
        buttons: MessageDialog.Yes | MessageDialog.No
        onAccepted: if (settingsModel) settingsModel.deleteProfile(profilesCombo.currentText)
    }

    LinuxSettingsView {
        id: linuxDialog
        objectName: "qmlLinuxSettingsDialog"
    }

    WizardView {
        id: importWizard
        objectName: "qmlImportWizard"
        onAccepted: if (settingsModel) settingsModel.finishImport()
    }

    Connections {
        target: settingsModel
        function onLinuxRequested() {
            linuxModel.refresh();
            linuxDialog.open();
        }
    }

    // One shared registry row (ADDONS / MODS).
    component RegistryRow: ColumnLayout {
        id: regRow
        property string label: ""
        property string url: ""
        signal apply(string text)
        signal reset()
        signal reload()
        signal openCustom()
        signal clearCustom()
        Layout.fillWidth: true
        spacing: 2
        Label {
            text: regRow.label
            font.bold: true
            font.pointSize: 9
            color: appTheme.colors["C_TEXT"]
        }
        TextField {
            Accessible.name: regRow.label
            id: urlField
            Layout.fillWidth: true
            text: regRow.url
            selectByMouse: true
            font.family: "monospace"
        }
        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            Button {
                text: "Apply"
                onClicked: regRow.apply(urlField.text)
            }
            Button {
                text: "Reset"
                flat: true
                ToolTip.text: "Use the default server catalog"
                ToolTip.visible: hovered
                onClicked: regRow.reset()
            }
            Button {
                text: "Reload"
                flat: true
                ToolTip.text: "Fetch the catalog now and refresh the tab"
                ToolTip.visible: hovered
                onClicked: regRow.reload()
            }
            Button {
                text: "Open custom file"
                flat: true
                onClicked: regRow.openCustom()
            }
            Button {
                text: "Clear custom entries"
                flat: true
                onClicked: regRow.clearCustom()
            }
        }
    }
}
