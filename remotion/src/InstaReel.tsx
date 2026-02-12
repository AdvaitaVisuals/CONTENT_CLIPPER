import React, { useMemo } from "react";
import {
  AbsoluteFill,
  Sequence,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { Video } from "@remotion/media";
import { createTikTokStyleCaptions } from "@remotion/captions";
import type { Caption, TikTokPage } from "@remotion/captions";

type WordTimestamp = {
  word: string;
  start: number; // seconds
  end: number; // seconds
};

export type InstaReelProps = {
  videoSrc: string;
  startTimeSec: number;
  endTimeSec: number;
  words: WordTimestamp[];
  hookLine: string;
};

const SWITCH_CAPTIONS_EVERY_MS = 1500;
const HIGHLIGHT_COLOR = "#FFD700";

const CaptionPage: React.FC<{ page: TikTokPage }> = ({ page }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const currentTimeMs = (frame / fps) * 1000;
  const absoluteTimeMs = page.startMs + currentTimeMs;

  return (
    <AbsoluteFill
      style={{
        justifyContent: "flex-end",
        alignItems: "center",
        paddingBottom: 280,
      }}
    >
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "center",
          gap: 8,
          maxWidth: 900,
          padding: "0 40px",
        }}
      >
        {page.tokens.map((token, i) => {
          const isActive =
            token.fromMs <= absoluteTimeMs && token.toMs > absoluteTimeMs;

          return (
            <span
              key={`${token.fromMs}-${i}`}
              style={{
                fontSize: 64,
                fontWeight: 900,
                fontFamily: "Arial Black, Arial, sans-serif",
                color: isActive ? HIGHLIGHT_COLOR : "white",
                textShadow: isActive
                  ? "0 0 20px rgba(255,215,0,0.8), 2px 2px 4px rgba(0,0,0,0.9)"
                  : "2px 2px 4px rgba(0,0,0,0.9), 0 0 10px rgba(0,0,0,0.5)",
                textTransform: "uppercase",
                transform: isActive ? "scale(1.15)" : "scale(1)",
                transition: "transform 0.1s, color 0.1s",
              }}
            >
              {token.text}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

export const InstaReel: React.FC<InstaReelProps> = ({
  videoSrc,
  startTimeSec,
  endTimeSec,
  words,
  hookLine,
}) => {
  const { fps } = useVideoConfig();
  const clipDurationSec = endTimeSec - startTimeSec;




  {/* Captions layer */ }
  {
    pages.map((page, index) => {
      return (
        <Sequence
          key={index}
          from={page.startMs * (fps / 1000)}
          durationInFrames={page.durationMs * (fps / 1000)}
        >
          <CaptionPage page={page} />
        </Sequence>
      );
    })
  }

  {/* Optional: Hook Line layer (Desi style overlay at the top) */ }
  {
    hookLine && (
      <AbsoluteFill
        style={{
          justifyContent: "flex-start",
          alignItems: "center",
          paddingTop: 150,
        }}
      >
        <div
          style={{
            background: "rgba(255, 61, 0, 0.9)",
            padding: "10px 30px",
            borderRadius: "50px",
            color: "white",
            fontSize: 50,
            fontWeight: 900,
            border: "4px solid white",
            boxShadow: "0 10px 30px rgba(0,0,0,0.5)",
          }}
        >
          {hookLine}
        </div>
      </AbsoluteFill>
    )
  }
    </AbsoluteFill >
  );
};
