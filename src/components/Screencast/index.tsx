import React, {useEffect, useRef, useState} from 'react';
import useBaseUrl from '@docusaurus/useBaseUrl';

import dimensions from './dimensions.json';

type Name = keyof typeof dimensions;

interface Props {
  name: Name;
  alt: string;
}

export default function Screencast({name, alt}: Props): React.ReactElement {
  const [loaded, setLoaded] = useState(false);
  const img = useRef<HTMLImageElement>(null);
  const src = useBaseUrl(`/screencasts/${name}.svg`);
  const [width, height] = dimensions[name];

  useEffect(() => {
    if (img.current?.complete) {
      setLoaded(true);
    }
  }, []);

  return (
    <span className="screencast-frame" style={{aspectRatio: `${width} / ${height}`}}>
      {!loaded && (
        <span className="screencast-frame__loading">loading the recording</span>
      )}
      <img
        ref={img}
        className="screencast"
        src={src}
        alt={alt}
        width={width}
        height={height}
        onLoad={() => setLoaded(true)}
        onError={() => setLoaded(true)}
      />
    </span>
  );
}
