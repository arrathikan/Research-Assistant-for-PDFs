import statusArtwork from '../../assets/paper-status-reference.png';
import libraryArtwork from '../../assets/library-reference.png';

export type ResearchArtworkKind = 'paper' | 'processing' | 'ready' | 'hero';
const VIEWS: Record<ResearchArtworkKind, string> = {
  paper: '220 90 440 440', processing: '860 90 440 440', ready: '1510 90 440 440',
  hero: '1050 95 480 225',
};

/** Display the supplied illustrations without altering their original raster files. */
export function ResearchArtwork({ kind, className = '' }: { kind: ResearchArtworkKind; className?: string }) {
  const hero = kind === 'hero';
  return <svg aria-hidden="true" focusable="false" data-art-kind={kind} viewBox={VIEWS[kind]}
    className={'shrink-0 ' + (hero ? 'library-illustration ' : '') + className}>
    <image href={hero ? libraryArtwork : statusArtwork} width={hero ? 1672 : 2172} height={hero ? 941 : 724} />
  </svg>;
}
