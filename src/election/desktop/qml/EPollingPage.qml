pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ScrollView {
    id: page
    required property var epolling
    required property var words
    required property bool online

    readonly property var votingState: epolling.state
    readonly property string stage: votingState.stage
    readonly property var context: votingState.context || ({})
    readonly property var election: context.election || ({})
    readonly property var constituency: context.constituency || ({})
    readonly property var station: context.station || ({})
    readonly property var candidates: votingState.candidates || []
    readonly property bool readyForNextVoter: stage === "waiting" || stage === "unavailable"
    readonly property Flickable voterViewport: contentItem as Flickable
    readonly property color ink: "#25344b"
    readonly property color accent: "#1967d2"
    readonly property color line: "#e1e7f0"
    property int selectedId: 0

    objectName: "epollingVoterView"
    contentWidth: availableWidth
    clip: true
    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

    function t(key) { return words[key] || key }
    function candidateLabel(candidate) { return candidate.number + " · " + candidate.name }
    function focusHeading() {
        Qt.callLater(function() {
            if (!page.visible) return
            if (page.voterViewport) page.voterViewport.contentY = 0
            heading.forceActiveFocus(Qt.OtherFocusReason)
        })
    }

    component VoterDialog: ConfirmationDialog {
        closePolicy: Popup.CloseOnEscape
        background: Rectangle {
            color: "white"
            border.color: page.line
            radius: 24
        }
    }

    onVisibleChanged: if (visible) focusHeading()
    onStageChanged: {
        if (stage !== "select") {
            selectedId = 0
            review.close()
            abandon.close()
        }
        focusHeading()
    }

    Item {
        width: page.availableWidth
        height: body.implicitHeight + 64

        ColumnLayout {
            id: body
            anchors.top: parent.top
            anchors.topMargin: 32
            anchors.horizontalCenter: parent.horizontalCenter
            width: Math.min(760, parent.width - 48)
            spacing: 20

            FormPanel {
                visible: !!page.election.name
                color: "#edf3fc"
                implicitHeight: electionName.implicitHeight + 24
                Label {
                    id: electionName
                    anchors.fill: parent
                    anchors.margins: 12
                    text: page.election.name || ""
                    textFormat: Text.PlainText
                    color: page.ink
                    wrapMode: Text.WordWrap
                }
            }

            ColumnLayout {
                visible: !!page.constituency.name || !!page.station.name
                Layout.fillWidth: true
                spacing: 6
                Label {
                    Layout.fillWidth: true
                    text: page.constituency.name || ""
                    textFormat: Text.PlainText
                    color: page.ink
                    font.pixelSize: 20
                    font.weight: Font.Medium
                    wrapMode: Text.WordWrap
                }
                FormCaption { text: page.station.name || "" }
            }

            FormPanel {
                implicitHeight: form.implicitHeight + 48

                ColumnLayout {
                    id: form
                    anchors.fill: parent
                    anchors.margins: 24
                    spacing: 16

                    RowLayout {
                        Layout.fillWidth: true
                        Label {
                            id: heading
                            objectName: "epollingStageHeading"
                            Layout.fillWidth: true
                            textFormat: Text.PlainText
                            color: page.ink
                            font.pixelSize: 28
                            font.weight: Font.Medium
                            wrapMode: Text.WordWrap
                            Accessible.role: Accessible.Heading
                            text: {
                                switch (page.stage) {
                                case "starting": return page.t("loading")
                                case "select": return page.t("epolling_choose")
                                case "casting": return page.t("epolling_casting")
                                case "checking": return page.t("epolling_checking")
                                case "recorded": return page.t("epolling_recorded")
                                case "waiting": return page.t("epolling_waiting")
                                default: return page.t("epolling_unavailable")
                                }
                            }
                        }
                        BusyIndicator {
                            running: parent.visible && !!page.votingState.busy
                            visible: running
                            implicitWidth: 28
                            implicitHeight: 28
                            Accessible.ignored: true
                        }
                    }

                    FormCaption {
                        visible: !!text
                        font.pixelSize: 14
                        text: {
                            switch (page.stage) {
                            case "select": return page.t("epolling_choose_hint")
                            case "checking": return page.t(page.votingState.retry
                                ? "epolling_retry_hint" : "epolling_check_hint")
                            case "recorded": return page.t("epolling_recorded_hint")
                            case "waiting": return page.t("epolling_next_voter_hint")
                            case "unavailable": return page.t("epolling_ask_officer")
                            default: return ""
                            }
                        }
                    }

                    FormNotice {
                        words: page.words
                        error: page.votingState.error
                            || (!page.online && (page.readyForNextVoter
                                || ["select", "checking"].includes(page.stage))
                                ? "epolling_offline" : "")
                        autoReveal: false
                    }

                    ButtonGroup { id: candidateGroup }
                    ColumnLayout {
                        Layout.fillWidth: true
                        visible: page.stage === "select"
                        spacing: 10
                        Repeater {
                            model: page.stage === "select" ? page.candidates : []
                            delegate: RadioButton {
                                id: candidate
                                required property var modelData
                                objectName: "epollingCandidate" + modelData.id
                                Layout.fillWidth: true
                                implicitHeight: Math.max(64, candidateName.implicitHeight + 24)
                                checked: page.selectedId === modelData.id
                                text: page.candidateLabel(modelData)
                                padding: 16
                                ButtonGroup.group: candidateGroup
                                onClicked: page.selectedId = modelData.id
                                background: Rectangle {
                                    color: candidate.checked ? "#edf4ff" : candidate.hovered ? "#f6f8fc" : "white"
                                    border.color: candidate.checked || candidate.visualFocus ? page.accent : page.line
                                    border.width: candidate.visualFocus ? 2 : 1
                                    radius: 12
                                }
                                contentItem: Label {
                                    id: candidateName
                                    leftPadding: candidate.indicator.width + 12
                                    verticalAlignment: Text.AlignVCenter
                                    text: candidate.text
                                    textFormat: Text.PlainText
                                    color: page.ink
                                    font.pixelSize: 17
                                    wrapMode: Text.WordWrap
                                    Accessible.ignored: true
                                }
                            }
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        visible: ["select", "checking", "recorded", "waiting", "unavailable"].includes(page.stage)
                        Item { Layout.fillWidth: true }
                        RowLayout {
                            visible: page.stage === "select"
                            FormButton {
                                objectName: "epollingAbandon"
                                text: page.t("epolling_abandon")
                                flat: true
                                highlighted: false
                                working: !page.online || page.votingState.busy
                                onClicked: abandon.open()
                            }
                            EPollingPrimaryButton {
                                objectName: "epollingReview"
                                text: page.t("epolling_review")
                                Layout.minimumWidth: 152
                                working: !page.online || !page.selectedId || page.votingState.busy
                                onClicked: review.open()
                            }
                        }
                        RowLayout {
                            visible: page.stage === "checking"
                            FormButton {
                                visible: !!page.votingState.retry
                                text: page.t("epolling_abandon")
                                flat: true
                                highlighted: false
                                working: !page.online || page.votingState.busy
                                onClicked: abandon.open()
                            }
                            FormButton {
                                objectName: "epollingCheckStatus"
                                text: page.t("epolling_check_status")
                                flat: true
                                highlighted: false
                                working: !page.online || page.votingState.busy
                                onClicked: page.epolling.checkStatus()
                            }
                            EPollingPrimaryButton {
                                visible: !!page.votingState.retry
                                objectName: "epollingRetryCast"
                                text: page.t("epolling_retry_cast")
                                working: !page.online || page.votingState.busy
                                onClicked: page.epolling.retryCast()
                            }
                        }
                        EPollingPrimaryButton {
                            objectName: "epollingDone"
                            Layout.minimumWidth: 152
                            visible: page.stage === "recorded"
                            text: page.t("epolling_done")
                            onClicked: page.epolling.done()
                        }
                        FormButton {
                            objectName: "epollingExit"
                            visible: page.readyForNextVoter
                                || (page.stage === "checking" && !!page.votingState.error)
                            text: page.t("epolling_exit")
                            flat: true
                            highlighted: false
                            working: !!page.votingState.busy
                            onClicked: page.epolling.exit()
                        }
                        EPollingPrimaryButton {
                            objectName: "epollingNextVoter"
                            visible: page.readyForNextVoter
                            text: page.t("epolling_next_voter")
                            working: !page.online || !!page.votingState.busy
                            onClicked: page.epolling.startNext()
                        }
                    }
                }
            }
        }
    }

    VoterDialog {
        id: review
        objectName: "epollingReviewDialog"
        readonly property var candidate: page.candidates.find(row => row.id === page.selectedId)
        title: page.t("epolling_confirm")
        message: candidate ? page.candidateLabel(candidate) : ""
        spacing: 12
        contentItem: ColumnLayout {
            spacing: 12
            Label {
                Layout.fillWidth: true
                text: review.message
                font.pixelSize: 18
                font.weight: Font.Medium
                color: page.ink
                textFormat: Text.PlainText
                wrapMode: Text.WordWrap
            }
            FormCaption {
                text: page.t("epolling_final")
                font.pixelSize: 14
            }
        }
        footer: DialogButtonBox {
            rightPadding: 24
            bottomPadding: 16
            spacing: 8
            Button {
                id: changeSelection
                objectName: "epollingChangeSelection"
                text: page.t("epolling_change")
                DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
            }
            EPollingPrimaryButton {
                objectName: "epollingCast"
                text: page.t("epolling_cast")
                working: !page.online || !review.candidate || page.votingState.busy
                DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole
            }
        }
        onOpened: changeSelection.forceActiveFocus(Qt.OtherFocusReason)
        onConfirmed: if (page.online && page.stage === "select" && page.selectedId)
            page.epolling.cast(page.selectedId)
    }

    VoterDialog {
        id: abandon
        title: page.t("epolling_abandon")
        message: page.t(page.stage === "checking"
            ? "epolling_recovery_abandon_prompt" : "epolling_abandon_prompt")
        acceptLabel: page.t("epolling_abandon")
        rejectLabel: page.t("cancel")
        onConfirmed: if (page.online) page.epolling.abandon()
    }
}
