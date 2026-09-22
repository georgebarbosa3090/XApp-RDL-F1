"""
Unit tests for the 5G/O-RAN Real-Time Protocol Engine and UE State Machine.
"""

import unittest
from analysis.realtime_protocol_engine import (
    STAGE_DEFINITIONS,
    ProtocolStage,
    RealTimeProtocolEngine,
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

    def test_ue_session_fsm_progression(self):
        """Verify sequential transition through stages 1 -> 5 without jitter."""
        fsm = UESessionFSM(ue_id=1001)
        self.assertEqual(fsm.current_stage, 0)
        self.assertFalse(fsm.is_completed)

        for expected_stage in range(1, 6):
            event = fsm.advance_stage(simulated_jitter=False)
            self.assertIsNotNone(event)
            self.assertEqual(event.stage, expected_stage)
            self.assertEqual(fsm.current_stage, expected_stage)
            self.assertAlmostEqual(
                event.accumulated_ms,
                STAGE_DEFINITIONS[expected_stage].nominal_accumulated_ms,
            )

        self.assertTrue(fsm.is_completed)
        self.assertIsNone(fsm.advance_stage())

    def test_engine_concurrency_and_summary(self):
        """Verify that the protocol engine manages concurrent sessions and produces valid stats."""
        engine = RealTimeProtocolEngine(max_concurrent_ues=5)
        
        # Step through multiple cycles
        for _ in range(15):
            events = engine.step()
            self.assertIsInstance(events, list)

        summary = engine.get_summary_statistics()
        self.assertIn("total_events", summary)
        self.assertGreater(summary["total_events"], 0)
        self.assertIn("stages", summary)
        self.assertEqual(len(summary["stages"]), 5)
        
        # Check all 5 stages have recorded samples
        for s_id in range(1, 6):
            self.assertIn(s_id, summary["stages"])
            self.assertGreater(summary["stages"][s_id]["samples_count"], 0)


if __name__ == "__main__":
    unittest.main()
