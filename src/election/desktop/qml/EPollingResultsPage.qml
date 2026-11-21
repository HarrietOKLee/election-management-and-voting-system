pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ColumnLayout {
    id: page
    objectName: "epollingResultsPage"
    required property var results
    required property var workspace
    required property var words
    required property bool online
    readonly property var tallyState: results ? results.state : ({})
    readonly property var tally: tallyState.tally || ({})
    readonly property bool hasTally: !!tally.context
    readonly property var context: tally.context || ({})
    readonly property var candidates: tally.candidates || []
    signal reveal(var control)
    spacing: 20

    function t(key) { return words[key] || key }
    onVisibleChanged: if (results) results.setViewing(visible)

    component ScopeDetail: ColumnLayout {
        required property string caption
        required property string value
        id: detail
        Layout.fillWidth: true
        Layout.alignment: Qt.AlignTop
        spacing: 5
        FormCaption { text: detail.caption }
        Label {
            Layout.fillWidth: true
            text: detail.value
            textFormat: Text.PlainText
            color: "#25344b"
            wrapMode: Text.WordWrap
        }
    }

    component CandidateTally: RowLayout {
        id: row
        required property string candidateNumber
        required property string candidateName
        required property string votes
        property bool heading: false
        Layout.fillWidth: true
        spacing: 16

        Label {
            Layout.preferredWidth: 128
            Layout.fillWidth: false
            text: row.candidateNumber
            textFormat: Text.PlainText
            wrapMode: Text.WordWrap
            color: row.heading ? "#65758b" : "#25344b"
        }
        Label {
            Layout.fillWidth: true
            text: row.candidateName
            textFormat: Text.PlainText
            wrapMode: Text.WordWrap
            color: row.heading ? "#65758b" : "#25344b"
        }
        Label {
            Layout.preferredWidth: 126
            Layout.fillWidth: false
            text: row.votes
            textFormat: Text.PlainText
            wrapMode: Text.WordWrap
            horizontalAlignment: Text.AlignRight
            color: row.heading ? "#65758b" : "#25344b"
            font.weight: row.heading ? Font.Normal : Font.Medium
        }
    }

    RowLayout {
        Layout.fillWidth: true
        Label {
            Layout.fillWidth: true
            text: page.t("epolling_results_title")
            color: "#25344b"
            font.pixelSize: 28
            font.weight: Font.Medium
            wrapMode: Text.WordWrap
            Accessible.role: Accessible.Heading
        }
        BusyIndicator {
            running: page.visible && !!page.tallyState.refreshing
            visible: running
            implicitWidth: 28
            implicitHeight: 28
            Accessible.name: page.t("loading")
        }
        FormButton {
            objectName: "epollingResultsRefresh"
            text: page.t("refresh")
            flat: true
            highlighted: false
            working: !page.tallyState.station_id || !!page.tallyState.refreshing
            onClicked: page.results.refresh()
            onReveal: control => page.reveal(control)
        }
    }

    StationWorkspace {
        Layout.fillWidth: true
        compact: true
        votingMethod: "electronic"
        workspace: page.workspace
        words: page.words
        onReveal: control => page.reveal(control)
    }

    FormNotice {
        words: page.words
        error: page.tallyState.error || (page.online ? "" : "disconnected")
        autoReveal: false
    }

    FormPanel {
        visible: page.hasTally
        implicitHeight: summary.implicitHeight + 40
        ColumnLayout {
            id: summary
            anchors.fill: parent
            anchors.margins: 20
            spacing: 16

            GridLayout {
                Layout.fillWidth: true
                columns: page.width > 760 ? 3 : 1
                columnSpacing: 24
                rowSpacing: 12
                ScopeDetail { caption: page.t("selected_election"); value: page.context.election || "" }
                ScopeDetail { caption: page.t("constituency_name"); value: page.context.constituency || "" }
                ScopeDetail { caption: page.t("station_name"); value: page.context.station || "" }
            }

            Rectangle { Layout.fillWidth: true; height: 1; color: "#e1e7f0" }

            RowLayout {
                Layout.fillWidth: true
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 5
                    Label {
                        Layout.fillWidth: true
                        text: page.t("epolling_results_total")
                        color: "#25344b"
                        font.pixelSize: 18
                        font.weight: Font.Medium
                        wrapMode: Text.WordWrap
                    }
                    FormCaption { text: page.t("epolling_results_scope") }
                }
                Label {
                    objectName: "epollingResultsTotal"
                    text: page.tally.total || ""
                    textFormat: Text.PlainText
                    color: "#1967d2"
                    font.pixelSize: 32
                    font.weight: Font.Medium
                    Accessible.name: page.t("epolling_results_total") + " " + text
                }
            }

            FormCaption {
                text: page.t("epolling_results_last_update") + " · " + (page.tallyState.updated_at || "")
            }

            FormCaption {
                visible: !page.online || !!page.tallyState.error
                text: page.t("epolling_results_stale")
            }

            FormCaption {
                visible: page.candidates.length === 0 || !!page.tally.zero_votes
                text: page.t(page.candidates.length ? "epolling_results_zero" : "no_candidates")
            }

            CandidateTally {
                visible: page.candidates.length > 0
                heading: true
                candidateNumber: page.t("ballot_number")
                candidateName: page.t("candidate_name")
                votes: page.t("epolling_results_votes")
            }

            Repeater {
                model: page.candidates
                delegate: ColumnLayout {
                    id: candidate
                    required property var modelData
                    Layout.fillWidth: true
                    spacing: 12
                    Rectangle { Layout.fillWidth: true; height: 1; color: "#e1e7f0" }
                    CandidateTally {
                        objectName: "epollingResultCandidate" + candidate.modelData.number
                        candidateNumber: candidate.modelData.number
                        candidateName: candidate.modelData.name
                        votes: candidate.modelData.votes
                    }
                }
            }
        }
    }
}
