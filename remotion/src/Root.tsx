import { Composition } from "remotion";
import { InstaReel, InstaReelProps } from "./InstaReel";

export const RemotionRoot = () => {
  return (
    <Composition
      id="InstaReel"
      component={InstaReel}
      durationInFrames={450} // placeholder, overridden by props
      fps={30}
      width={1080}
      height={1920}
      defaultProps={{
        videoSrc: "",
        startTimeSec: 0,
        endTimeSec: 15,
        words: [],
        hookLine: "",
      } satisfies InstaReelProps}
      calculateMetadata={async ({ props }) => {
        const durationSec = props.endTimeSec - props.startTimeSec;
        return {
          durationInFrames: Math.ceil(durationSec * 30),
        };
      }}
    />
  );
};
