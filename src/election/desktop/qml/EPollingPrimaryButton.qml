import QtQuick
import QtQuick.Controls

FormButton {
    id: control
    horizontalPadding: 20

    // Keep the voter actions visible with both hardware and software rendering.
    background: Rectangle {
        implicitWidth: 96
        radius: height / 2
        color: !control.enabled ? "#e8edf5"
            : control.down ? "#1152af" : control.hovered ? "#165ebf" : "#1967d2"
        border.width: control.visualFocus ? 2 : 0
        border.color: "#0b3d91"
    }
    contentItem: Label {
        text: control.text
        font: control.font
        color: control.enabled ? "white" : "#65758b"
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        Accessible.ignored: true
    }
}
