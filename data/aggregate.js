window.DEMO_METRICS = {
  scope: {
    videoCount: 4,
    recordingDateCount: 1,
    referenceIntervalCount: 148,
    boundaryToleranceSeconds: 0.5,
    referenceType: "human-edited editorial timelines; not physical LIVE/DEAD truth"
  },
  arms: [
    {
      id: "player_tracknet_context",
      name: "Player + TrackNet context",
      predictedIntervals: 133,
      completeMatches: 82,
      pairPrecisionPct: 61.65,
      pairRecallPct: 55.41,
      liveLostSeconds: 175.60,
      deadKeptSeconds: 51.12,
      unknownPct: 5.46,
      balancedAccuracyPct: 87.44,
      liveRecallPct: 84.10,
      deadRecallPct: 90.78
    },
    {
      id: "tail_safe",
      name: "Tail-safe Player + TrackNet context",
      predictedIntervals: 132,
      completeMatches: 79,
      pairPrecisionPct: 59.85,
      pairRecallPct: 53.38,
      liveLostSeconds: 164.33,
      deadKeptSeconds: 62.85,
      unknownPct: 5.08,
      balancedAccuracyPct: 87.75,
      liveRecallPct: 84.33,
      deadRecallPct: 91.18
    }
  ]
};
