// Import wizard dialog (Phase 6b). Mirrors
// Import wizard: input (file/URL) → install folder →
// trust stages. Reads the `wizard` context property
// (ui/qml/wizard.py:WizardModel). Used standalone at first launch
// (WizardWindow.qml) and embedded for profile import.

pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material
import QtQuick.Dialogs
import QtQuick.Layouts

Dialog {
    id: root
    title: "Welcome to Nostalgia Launcher"
    modal: true
    width: 600
    height: 520
    anchors.centerIn: parent

    header: ToolBar {
        background: Rectangle {
            color: appTheme.colors["C_HDR"]
        }
        ColumnLayout {
            anchors.fill: parent
            anchors.leftMargin: 18
            anchors.rightMargin: 8
            RowLayout {
                Layout.fillWidth: true
                Label {
                    objectName: "qmlWizardTitle"
                    Layout.fillWidth: true
                    text: wizard ? wizard.title : ""
                    font.bold: true
                    font.pointSize: 13
                    color: appTheme.colors["C_GOLD_LT"]
                    elide: Text.ElideRight
                }
                ToolButton {
                    objectName: "qmlWizardClose"
                    text: "✕"
                    Accessible.name: "Close"
                    ToolTip.text: "Close"
                    ToolTip.visible: hovered
                    onClicked: root.reject()
                }
            }
            Label {
                objectName: "qmlWizardStep"
                Layout.fillWidth: true
                text: wizard ? wizard.step : ""
                font.pointSize: 9
                color: appTheme.colors["C_TEXT_DIM"]
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 8

        Label {
            objectName: "qmlWizardIntro"
            Layout.fillWidth: true
            visible: wizard ? wizard.stage === "input" : false
            text: "This launcher doesn't include any server list.\n\nTo continue, import a configuration supplied independently by your community or server operator. The configuration controls where the launcher retrieves game files, news, mods, and addons from."
            font.pointSize: 10
            color: appTheme.colors["C_TEXT_DIM"]
            wrapMode: Text.WordWrap
        }

        Label {
            objectName: "qmlWizardStatus"
            Layout.fillWidth: true
            visible: wizard ? wizard.statusText !== "" : false
            text: wizard ? wizard.statusText : ""
            font.pointSize: 9
            color: appTheme.colors["C_TEXT_DIM"]
            wrapMode: Text.WordWrap
        }

        // ── input stage ─────────────────────────────────────
        ColumnLayout {
            Layout.fillWidth: true
            visible: wizard ? wizard.stage === "input" : false
            spacing: 4
            RadioButton {
                objectName: "qmlWizardSourceUrl"
                text: "A configuration URL"
                checked: wizard ? wizard.source === "url" : false
                onClicked: if (wizard) wizard.setSource("url")
            }
            RadioButton {
                objectName: "qmlWizardSourceFile"
                text: "A configuration file"
                checked: wizard ? wizard.source === "file" : false
                onClicked: if (wizard) wizard.setSource("file")
            }
            TextField {
                Accessible.name: "Configuration URL"
                objectName: "qmlWizardUrl"
                Layout.fillWidth: true
                visible: wizard ? wizard.source === "url" : false
                text: wizard ? wizard.url : ""
                placeholderText: "Configuration URL (https://example.com/community-config.json)"
                font.family: "monospace"
                onTextChanged: if (wizard) wizard.setUrl(text)
            }
            RowLayout {
                Layout.fillWidth: true
                visible: wizard ? wizard.source === "file" : false
                TextField {
                    Accessible.name: "Configuration file"
                    objectName: "qmlWizardPath"
                    Layout.fillWidth: true
                    text: wizard ? wizard.configPath : ""
                    readOnly: true
                    placeholderText: "Select a local configuration file"
                    font.family: "monospace"
                }
                Button {
                    objectName: "qmlWizardBrowse"
                    text: "Browse…"
                    onClicked: configPicker.open()
                }
            }
        }

        // ── folder stage ────────────────────────────────────
        ColumnLayout {
            Layout.fillWidth: true
            visible: wizard ? wizard.stage !== "input" : false
            spacing: 4
            Label {
                text: "INSTALL FOLDER"
                font.bold: true
                font.pointSize: 10
                color: appTheme.colors["C_GOLD"]
            }
            Label {
                Layout.fillWidth: true
                text: "Where the game client lives. Each launcher profile keeps its own install folder."
                font.pointSize: 9
                color: appTheme.colors["C_TEXT_DIM"]
                wrapMode: Text.WordWrap
            }
            RowLayout {
                Layout.fillWidth: true
                TextField {
                    Accessible.name: "INSTALL FOLDER"
                    objectName: "qmlWizardFolder"
                    Layout.fillWidth: true
                    text: wizard ? wizard.folder : ""
                    enabled: wizard ? wizard.stage === "folder" : false
                    font.family: "monospace"
                    onTextChanged: if (wizard) wizard.setFolder(text)
                }
                Button {
                    objectName: "qmlWizardFolderBrowse"
                    text: "Browse…"
                    enabled: wizard ? wizard.stage === "folder" : false
                    onClicked: folderPicker.open()
                }
            }
        }

        // ── trust stage ─────────────────────────────────────
        ScrollView {
            objectName: "qmlWizardTrust"
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: wizard ? wizard.stage === "trust" : false
            clip: true
            contentWidth: availableWidth
            ColumnLayout {
                width: parent.width
                spacing: 6
                Label {
                    objectName: "qmlWizardTrustName"
                    Layout.fillWidth: true
                    text: wizard ? wizard.trustName : ""
                    font.bold: true
                    font.pointSize: 13
                    color: appTheme.colors["C_TEXT"]
                    wrapMode: Text.WordWrap
                }
                Label {
                    objectName: "qmlWizardTrustSource"
                    Layout.fillWidth: true
                    text: wizard ? wizard.trustSource : ""
                    color: appTheme.colors["C_TEXT_DIM"]
                    wrapMode: Text.WordWrap
                }
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 1
                    color: appTheme.colors["C_DIVIDER"]
                }
                Label {
                    text: "Will contact:"
                    font.bold: true
                    font.pointSize: 10
                    color: appTheme.colors["C_GOLD"]
                }
                Label {
                    objectName: "qmlWizardTrustHosts"
                    Layout.fillWidth: true
                    text: wizard && wizard.trustHosts ? wizard.trustHosts.join("\n") : ""
                    font.family: "monospace"
                    color: appTheme.colors["C_TEXT"]
                    wrapMode: Text.WordWrap
                }
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 1
                    color: appTheme.colors["C_DIVIDER"]
                }
                Label {
                    text: "Will download:"
                    font.bold: true
                    font.pointSize: 10
                    color: appTheme.colors["C_GOLD"]
                }
                Repeater {
                    model: wizard ? wizard.trustCaps : []
                    Label {
                        id: trustCapLabel
                        required property var modelData
                        Layout.fillWidth: true
                        text: (trustCapLabel.modelData.enabled ? "✓ " : "— ") + trustCapLabel.modelData.detail
                        color: trustCapLabel.modelData.enabled ? appTheme.colors["C_TEXT"] : appTheme.colors["C_TEXT_DIM"]
                        wrapMode: Text.WordWrap
                    }
                }
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 1
                    color: appTheme.colors["C_DIVIDER"]
                }
                Label {
                    Layout.fillWidth: true
                    text: "Only trust this configuration if you trust its source. It controls where game files, mods, and addons are downloaded from and can modify the selected game folder."
                    color: appTheme.colors["C_TEXT_DIM"]
                    wrapMode: Text.WordWrap
                }
            }
        }

        Label {
            objectName: "qmlWizardError"
            Layout.fillWidth: true
            visible: wizard ? wizard.errorText !== "" : false
            text: wizard ? wizard.errorText : ""
            color: appTheme.colors["C_ERR"]
            wrapMode: Text.WordWrap
        }

        Item { Layout.fillHeight: true }

        RowLayout {
            Layout.fillWidth: true
            Item { Layout.fillWidth: true }
            Button {
                objectName: "qmlWizardBack"
                text: "Back"
                visible: wizard ? wizard.backVisible : false
                flat: true
                onClicked: if (wizard) wizard.goBack()
            }
            Button {
                objectName: "qmlWizardCancel"
                text: "Cancel"
                flat: true
                onClicked: root.reject()
            }
            Button {
                objectName: "qmlWizardOk"
                text: wizard ? wizard.okText : "Continue"
                highlighted: true
                enabled: wizard ? wizard.okEnabled : false
                onClicked: {
                    if (wizard && wizard.submit())
                        root.accept();
                }
            }
        }
    }

    FileDialog {
        id: configPicker
        title: "Select launcher configuration"
        fileMode: FileDialog.OpenFile
        nameFilters: ["Launcher configuration (*.json)"]
        onAccepted: wizard.setPath(currentFile.toString().replace(/^file:\/\//, ""))
    }

    FolderDialog {
        id: folderPicker
        title: "Select game client folder"
        onAccepted: wizard.setFolder(selectedFolder.toString().replace(/^file:\/\//, ""))
    }
}
