"""
Unit tests for the 5G/O-RAN Real-Time Protocol Engine, UE State Machine, and 7-Phase Cognitive Demonstration Protocol.
"""

import unittest
from analysis.realtime_protocol_engine import (
    PHASE_DEFINITIONS,
    STAGE_DEFINITIONS,
    CognitiveDemonstrationProtocol,
    DemonstrationPhase,
    ProtocolStage,
    RealTimeProtocolEngine,
    ScenarioType,
    SignalingEvent,
    UESessionFSM,
)


class TestRealTimeProtocolEngine(unittest.TestCase):

    def test_stage_definitions_integrity(self):
        """Verify the 5 canonical stages match the 3GPP and O-RAN specifications."""
        self.assertEqual(len(STAGE_DEFINITIONS), 5)
        self.assertAlmostEqual(STAGE_DEFINITIONS[1].nominal_delta_ms, 4.2)
        self.assertAlmostEqual(STAGE_DEFINITIONS[2].nominal_delta_ms, 8.5)
        self.assertAlmostEqual(STAGE_DEFINITIONS[3].nominal_delta_ms, 16.4)
        self.assertAlmostEqual(STAGE_DEFINITIONS[4].nominal_delta_ms, 11.2)
        self.assertAlmostEqual(STAGE_DEFINITIONS[5].nominal_delta_ms, 5.5)

        self.assertAlmostEqual(STAGE_DEFINITIONS[1].nominal_accumulated_ms, 4.2)
        self.assertAlmostEqual(STAGE_DEFINITIONS[2].nominal_accumulated_ms, 12.7)
        self.assertAlmostEqual(STAGE_DEFINITIONS[3].nominal_accumulated_ms, 29.1)
        self.assertAlmostEqual(STAGE_DEFINITIONS[4].nominal_accumulated_ms, 40.3)
        self.assertAlmostEqual(STAGE_DEFINITIONS[5].nominal_accumulated_ms, 45.8)

    def test_7_phase_demonstration_protocol_progression(self):
        """Verify sequential transition through the 7 cognitive demonstration phases."""
        self.assertEqual(len(PHASE_DEFINITIONS), 7)
        protocol = CognitiveDemonstrationProtocol()
        
        for expected_phase in range(1, 8):
            state = protocol.advance_phase()
            self.assertEqual(state.current_phase, expected_phase)
            self.assertIn("nodes", state.knowledge_graph)
            self.assertIn("edges", state.knowledge_graph)
            self.assertGreater(len(state.knowledge_graph["nodes"]), 0)
            self.assertGreater(len(state.knowledge_graph["edges"]), 0)

        # Verify loop restart to phase 1
        state_next_cycle = protocol.advance_phase()
        self.assertEqual(state_next_cycle.current_phase, 1)
        self.assertEqual(state_next_cycle.cycle_index, 2)

    def test_scenario_switching(self):
        """Verify conflict injection and scenario switching in the demonstration engine."""
        protocol = CognitiveDemonstrationProtocol()
        protocol.set_scenario(ScenarioType.S2_ENERGY_VS_QOS.value)
        self.assertEqual(protocol.scenario, ScenarioType.S2_ENERGY_VS_QOS.value)
        state = protocol.advance_phase()
        self.assertEqual(state.scenario, ScenarioType.S2_ENERGY_VS_QOS.value)


if __name__ == "__main__":
    unittest.main()
