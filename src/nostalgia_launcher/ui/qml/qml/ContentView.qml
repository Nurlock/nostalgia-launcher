// Shared ADDONS/MODS/ASSETS manage list: banner (title + search +
// reload), rows (checkbox, name, repo link, description), empty state,
// Uninstall footer. Instantiated per tab with a `contentModel`
// (ui/qml/content.py:ContentListModel) plus tab wording.

pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material
import QtQuick.Layouts

ColumnLayout {
    id: root
    objectName: "qmlContentView"
    spacing: 0

    property var contentModel
    property string tabTitle: ""
    property string legendText: ""
    property string loadingText: "Loading…"

    ToolBar {
        Layout.fillWidth: true
        background: Rectangle {
            color: appTheme.colors["C_PANEL"]
        }
        ColumnLayout {
            anchors.fill: parent
            anchors.leftMargin: 16
            anchors.rightMargin: 12
            spacing: 2
            RowLayout {
                Layout.fillWidth: true
                Label {
                    objectName: "qmlContentTitle"
                    Layout.fillWidth: true
                    text: "INSTALLED " + root.tabTitle
                    font.bold: true
                    font.pointSize: 12
                    color: appTheme.colors["C_GOLD"]
                }
                Label {
                    text: root.legendText
                    font.pointSize: 9
                    color: appTheme.colors["C_TEXT_DIM"]
                    visible: root.legendText !== ""
                }
                ToolButton {
                    objectName: "qmlContentReload"
                    text: "⟳"
                    Accessible.name: "Reload catalog"
                    ToolTip.text: "Reload the catalog from the server"
                    ToolTip.visible: hovered
                    onClicked: root.contentModel.reloadCatalog()
                }
            }
            RowLayout {
                Layout.fillWidth: true
                Layout.topMargin: 0
                Layout.bottomMargin: 2
                spacing: 8
                TextField {
                    objectName: "qmlContentSearch"
                    Layout.fillWidth: true
                    Layout.preferredHeight: 36
                    Layout.alignment: Qt.AlignVCenter
                    topPadding: 4
                    bottomPadding: 4
                    font.pointSize: 9
                    placeholderText: "⌕  Filter"
                    Accessible.name: "Filter entries"
                    onTextChanged: root.contentModel.setFilterText(text)
                }
                Button {
                    objectName: "qmlContentBrowseMore"
                    Layout.preferredHeight: 36
                    Layout.alignment: Qt.AlignVCenter
                    topPadding: 4
                    bottomPadding: 4
                    text: "Add " + root.tabTitle.toLowerCase()
                    onClicked: root.contentModel.requestBrowse()
                }
            }
        }
    }

    Rectangle {
        Layout.fillWidth: true
        Layout.preferredHeight: 1
        color: appTheme.colors["C_DIVIDER"]
    }

    ColumnLayout {
        Layout.fillWidth: true
        Layout.leftMargin: 16
        Layout.rightMargin: 16
        Layout.topMargin: 12
        spacing: 8
        visible: root.contentModel ? (!root.contentModel.scanning && root.contentModel.emptyVisible) : false
        Label {
            objectName: "qmlContentEmpty"
            Layout.fillWidth: true
            text: root.contentModel ? root.contentModel.emptyText : ""
            font.pointSize: 10
            color: appTheme.colors["C_TEXT_DIM"]
            wrapMode: Text.WordWrap
        }
        Button {
            objectName: "qmlContentBrowse"
            text: "Browse " + root.tabTitle.toLowerCase()
            highlighted: true
            onClicked: root.contentModel.requestBrowse()
        }
    }
    ColumnLayout {
        objectName: "qmlContentWaiting"
        Layout.fillWidth: true
        Layout.topMargin: 32
        spacing: 12
        visible: root.contentModel ? root.contentModel.scanning : false
        BusyIndicator {
            Layout.alignment: Qt.AlignHCenter
            running: parent.visible
        }
        Label {
            Layout.alignment: Qt.AlignHCenter
            text: root.loadingText
            font.pointSize: 10
            color: appTheme.colors["C_TEXT_DIM"]
        }
    }

    ListView {
        id: entryList
        objectName: "qmlContentList"
        Layout.fillWidth: true
        Layout.fillHeight: true
        clip: true
        model: root.contentModel
        ScrollBar.vertical: ScrollBar {
            objectName: "qmlContentScrollBar"
        }
        delegate: ColumnLayout {
            id: entryDelegate
            required property var model
            width: ListView.view.width
            spacing: 2
            RowLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 12
                spacing: 4
                CheckBox {
                    Accessible.name: "Uninstall " + entryDelegate.model.name
                    checked: entryDelegate.model.enabled
                    enabled: !(entryDelegate.model.serverManaged || false)
                    onCheckedChanged: root.contentModel.toggleEntry(entryDelegate.model.eid, checked)
                }
                Label {
                    text: "●"
                    font.pointSize: 8
                    color: appTheme.colors["C_GOLD"]
                    visible: (entryDelegate.model.staged || false) && !(entryDelegate.model.serverManaged || false)
                    Accessible.name: "Marked for uninstall: " + entryDelegate.model.name
                }
                Label {
                    text: "SERVER"
                    font.pointSize: 8
                    font.bold: true
                    color: appTheme.colors["C_GOLD"]
                    visible: entryDelegate.model.serverManaged || false
                    Accessible.name: "Server-managed entry for " + entryDelegate.model.name
                }
                Label {
                    Layout.fillWidth: true
                    text: entryDelegate.model.name
                    font.bold: true
                    font.pointSize: 11
                    color: (entryDelegate.model.needsUpdate || false) ? appTheme.colors["C_GOLD"] : appTheme.colors["C_TEXT"]
                    elide: Text.ElideRight
                }
                Button {
                    objectName: "qmlContentUpdateOne"
                    text: "↑"
                    Accessible.name: "Update " + entryDelegate.model.name
                    ToolTip.text: "Update " + entryDelegate.model.name
                    ToolTip.visible: hovered
                    visible: (entryDelegate.model.needsUpdate || false) && !(entryDelegate.model.serverManaged || false)
                    enabled: root.contentModel ? !root.contentModel.busy : true
                    flat: true
                    contentItem: Text {
                        text: "↑"
                        font.bold: true
                        font.pointSize: 15
                        color: appTheme.colors["C_GOLD"]
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    onClicked: if (root.contentModel) root.contentModel.updateOne(entryDelegate.model.eid)
                }
                Button {
                    text: "⧉"
                    font.pointSize: 15
                    Accessible.name: "Open repository for " + entryDelegate.model.name
                    ToolTip.text: "Open repository in browser"
                    ToolTip.visible: hovered
                    visible: entryDelegate.model.repoUrl !== ""
                    flat: true
                    onClicked: Qt.openUrlExternally(entryDelegate.model.repoUrl)
                }
            }
            Label {
                Layout.fillWidth: true
                Layout.leftMargin: 48
                Layout.rightMargin: 12
                text: entryDelegate.model.description
                font.pointSize: 10
                color: appTheme.colors["C_TEXT_DIM"]
                wrapMode: Text.WordWrap
                visible: entryDelegate.model.description !== ""
            }
            Rectangle {
                Layout.fillWidth: true
                Layout.topMargin: 3
                Layout.bottomMargin: 3
                Layout.preferredHeight: 1
                color: appTheme.colors["C_DIVIDER"]
            }
        }
    }

    Rectangle {
        Layout.fillWidth: true
        Layout.preferredHeight: 1
        color: appTheme.colors["C_DIVIDER"]
    }

    RowLayout {
        Layout.fillWidth: true
        Layout.leftMargin: 16
        Layout.rightMargin: 16
        Layout.topMargin: 2
        Layout.bottomMargin: 4
        spacing: 8
        Button {
            objectName: "qmlContentUpdate"
            text: root.contentModel ? (root.contentModel.busy && root.contentModel.busyAction === "update" ? "Updating…" : (root.contentModel.updatesCount > 0 ? "Update (" + root.contentModel.updatesCount + ")" : "Update")) : "Update"
            visible: root.contentModel ? (root.contentModel.updatesCount > 0) : false
            enabled: root.contentModel ? (!root.contentModel.busy && root.contentModel.updatesCount > 0) : false
            highlighted: true
            topPadding: 2
            bottomPadding: 2
            onClicked: if (root.contentModel) root.contentModel.updateAll()
        }
        Button {
            objectName: "qmlContentApply"
            text: root.contentModel ? (root.contentModel.busy && root.contentModel.busyAction !== "update" ? "Uninstalling…" : (root.contentModel.pendingCount > 0 ? "Uninstall (" + root.contentModel.pendingCount + ")" : "Uninstall")) : "Uninstall"
            enabled: root.contentModel ? (!root.contentModel.busy && root.contentModel.pendingCount > 0) : false
            highlighted: root.contentModel ? (root.contentModel.pendingCount > 0 && root.contentModel.updatesCount === 0) : false
            topPadding: 2
            bottomPadding: 2
            onClicked: if (root.contentModel) root.contentModel.applyAll()
        }
        Item { Layout.fillWidth: true }
    }
}
