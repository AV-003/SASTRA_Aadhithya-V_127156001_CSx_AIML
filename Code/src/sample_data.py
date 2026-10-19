"""Synthetic demonstration data used by the local demo and tests.

This material is fictional. It is not an AUTOSAR specification, not OEM
documentation, and not suitable for production engineering decisions.
"""

SAMPLE_DOCUMENT_NAME = "vehicle_lighting_hld_sample.pdf"

SAMPLE_PAGES = [
    """
Synthetic AUTOSAR-Style HLD Demonstration Document
Document: Vehicle Lighting Controller HLD
Notice: This document is synthetic demonstration data only.

Page 1. System Overview
The Vehicle Lighting Controller is a fictional high-level design for a simple
exterior lighting feature. The Light Control application component receives
driver lighting requests and decides whether the headlamp command should be ON
or OFF. The component that controls the exterior lamp decision is Light Control.
The Vehicle Signal Interface component adapts vehicle network values
into application-level signals for the Light Control component.

Identified components:
- Light Control application component
- Vehicle Signal Interface component
- Lamp Driver Interface component

The design goal is to show traceable document question answering with source
pages, not to define a certified automotive architecture.
""",
    """
Page 2. Interfaces, Ports, and Signals
The Light Control application component has a required port named
R_HeadlampSwitch. This port receives the input signal HeadlampSwitchRequest from
the Vehicle Signal Interface component.

The Light Control application component has a provided port named P_LampStatus.
This port publishes the output signal LampStatus for diagnostic display and
operator feedback. LampStatus can report OFF, LOW_BEAM_ON, or FAULT_DETECTED in
this synthetic example. The signal that reports lamp status is LampStatus.

The interface I_LightCommand carries the internal command LightCommand from the
Light Control application component to the Lamp Driver Interface component. The
Lamp Driver Interface converts LightCommand into a hardware-oriented lamp drive
request.
""",
    """
Page 3. Dependencies and Functional Flow
The Light Control application component depends on HeadlampSwitchRequest being
available from the Vehicle Signal Interface component. It also depends on the
Lamp Driver Interface accepting the LightCommand signal.

Functional flow:
1. Vehicle Signal Interface reads HeadlampSwitchRequest from a fictional
vehicle network source.
2. Light Control evaluates HeadlampSwitchRequest. If the request is ON and no
fault condition is present, Light Control sets LightCommand to LOW_BEAM_ON.
3. Lamp Driver Interface receives LightCommand and issues a lamp drive request.
4. Light Control publishes LampStatus so a display or diagnostic function can
show the current lamp state.

Architecture decision:
The signal adaptation responsibility is kept in Vehicle Signal Interface so the
Light Control component does not depend directly on network frame details.

Safety note:
This sample is for academic demonstration only. Real vehicle lighting behavior,
safety analysis, fault handling, and production changes require qualified human
review and project-specific engineering evidence.
""",
]

SAMPLE_EVALUATION_QUESTIONS = [
    {
        "question": "Which component controls the exterior lamp decision?",
        "expected_pages": [1],
        "expected_terms": ["Light Control"],
    },
    {
        "question": "What signal reports the lamp status?",
        "expected_pages": [2],
        "expected_terms": ["LampStatus"],
    },
    {
        "question": "Which input signal is received through R_HeadlampSwitch?",
        "expected_pages": [2],
        "expected_terms": ["HeadlampSwitchRequest"],
    },
    {
        "question": "What does Light Control depend on?",
        "expected_pages": [3],
        "expected_terms": ["depends on", "HeadlampSwitchRequest"],
    },
    {
        "question": "What happens when the headlamp request is ON and no fault is present?",
        "expected_pages": [3],
        "expected_terms": ["LOW_BEAM_ON"],
    },
    {
        "question": "What is the brake pressure calibration threshold?",
        "expected_pages": [],
        "expected_terms": [],
        "insufficient_evidence": True,
    },
]
