// BROWSE dialog: catalog search + one-click Install per row.
// Reads the `browseModel` property (ui/qml/browse.py:BrowseModel).
// Installed via the tab's existing apply-one path; no staging here.

import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material
import QtQuick.Layouts

Dialog {
    id: root

    property var browseModel
    property string formSource: ""

    objectName: "qmlBrowseDialog"
    title: "BROWSE"
    modal: true
    // Fill 95% of the mother window; the tab container fills the dialog.
    width: parent ? parent.width * 0.95 : 560
    height: parent ? parent.height * 0.95 : 420
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
                text: root.title
                font.bold: true
                font.pointSize: 13
                color: appTheme.colors["C_GOLD_LT"]
                elide: Text.ElideRight
            }
            ToolButton {
                objectName: "qmlBrowseClose"
                text: "✕"
                Accessible.name: "Close"
                ToolTip.text: "Close"
                ToolTip.visible: hovered
                onClicked: root.close()
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        TabBar {
            id: browseTabs
            objectName: "qmlBrowseTabs"
            Layout.fillWidth: true
            TabButton { text: "Catalog" }
            TabButton { text: "Custom" }
        }

        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: browseTabs.currentIndex

            // ── Catalog ──────────────────────────────────────────
            ColumnLayout {
                spacing: 6

                RowLayout {
                    Layout.fillWidth: true
                    Layout.leftMargin: 16
                    Layout.rightMargin: 16
                    Layout.topMargin: 6
                    Layout.bottomMargin: 4
                    TextField {
                        objectName: "qmlBrowseSearch"
                        Layout.fillWidth: true
                        Layout.preferredHeight: 32
                        Layout.alignment: Qt.AlignVCenter
                        topPadding: 2
                        bottomPadding: 2
                        font.pointSize: 9
                        placeholderText: "⌕  Filter"
                        Accessible.name: "Search catalog"
                        onTextChanged: if (root.browseModel) root.browseModel.setFilterText(text)
                    }
                }

                Label {
                    Layout.fillWidth: true
                    Layout.leftMargin: 16
                    Layout.rightMargin: 16
                    text: root.browseModel ? root.browseModel.emptyText : ""
                    color: appTheme.colors["C_TEXT_DIM"]
                    visible: root.browseModel ? root.browseModel.emptyVisible : false
                    wrapMode: Text.WordWrap
                }

                ListView {
                    id: browseList
                    objectName: "qmlBrowseList"
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.leftMargin: 8
                    Layout.rightMargin: 8
                    clip: true
                    model: root.browseModel ? root.browseModel : null
                    ScrollBar.vertical: ScrollBar {
                        objectName: "qmlBrowseScrollBar"
                    }
                    delegate: Item {
                        width: ListView.view.width
                        height: rowCol.height
                        Rectangle {
                            anchors.fill: parent
                            color: appTheme.colors["C_TEXT"]
                            opacity: (index % 2) ? 0.08 : 0
                        }
                        ColumnLayout {
                            id: rowCol
                            anchors.left: parent.left
                            anchors.right: parent.right
                            spacing: 0
                            RowLayout {
                                Layout.fillWidth: true
                                Layout.leftMargin: 16
                                Layout.rightMargin: 16
                                spacing: 4
                                Label {
                                    Layout.fillWidth: true
                                    text: model.entryName
                                    font.bold: true
                                    font.pointSize: 10
                                    font.underline: titleHover.containsMouse
                                            && (model.entryRepoUrl || "") !== ""
                                    color: (model.entryRepoUrl || "") !== ""
                                        ? appTheme.colors["C_GOLD"]
                                        : appTheme.colors["C_TEXT"]
                                    elide: Text.ElideRight
                                    Accessible.name: (model.entryRepoUrl || "") !== ""
                                        ? "Open repository for " + model.entryName
                                        : "Addon " + model.entryName
                                    ToolTip.text: "Open repository in browser"
                                    ToolTip.visible: titleHover.containsMouse
                                        && (model.entryRepoUrl || "") !== ""
                                    MouseArea {
                                        id: titleHover
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        cursorShape: (model.entryRepoUrl || "") !== ""
                                            ? Qt.PointingHandCursor
                                            : Qt.ArrowCursor
                                        enabled: (model.entryRepoUrl || "") !== ""
                                        onClicked: Qt.openUrlExternally(model.entryRepoUrl)
                                    }
                                }
                                CheckBox {
                                    Accessible.name: "Select " + model.entryName
                                    checked: model.entrySelected || false
                                    topPadding: 0
                                    bottomPadding: 0
                                    onToggled: if (root.browseModel) root.browseModel.setSelected(
                                        model.entryId, checked
                                    )
                                }
                            }
                            Label {
                                Layout.fillWidth: true
                                Layout.leftMargin: 16
                                Layout.rightMargin: 16
                                Layout.topMargin: -4
                                text: model.entryDescription
                                font.pointSize: 9
                                color: appTheme.colors["C_TEXT"]
                                wrapMode: Text.WordWrap
                                maximumLineCount: 1
                                elide: Text.ElideRight
                                visible: model.entryDescription !== ""
                            }
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
                    Label {
                        Layout.fillWidth: true
                        text: (root.browseModel && root.browseModel.selectedCount > 0)
                            ? root.browseModel.selectedCount + " selected"
                            : ""
                        color: appTheme.colors["C_TEXT_DIM"]
                    }
                    Button {
                        objectName: "qmlBrowseInstall"
                        text: (root.browseModel && root.browseModel.selectedCount > 0)
                            ? "Install (" + root.browseModel.selectedCount + ")"
                            : "Install"
                        Accessible.name: "Install selected entries"
                        enabled: Boolean(root.browseModel
                            && root.browseModel.selectedCount > 0
                            && !root.browseModel.busy)
                        highlighted: true
                        topPadding: 2
                        bottomPadding: 2
                        onClicked: if (root.browseModel) root.browseModel.installSelected()
                    }
                }
            }

            // ── Custom ───────────────────────────────────────────
            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Loader {
                    id: formLoader
                    anchors.fill: parent
                    anchors.leftMargin: 16
                    anchors.rightMargin: 16
                    anchors.topMargin: 16
                    anchors.bottomMargin: 16
                    source: root.formSource
                }
            }
        }

        Connections {
            target: formLoader.item
            function onAccepted() { browseTabs.currentIndex = 0; }
            function onRejected() { browseTabs.currentIndex = 0; }
        }
    }
}
