export type BandType = 'wind' | 'brass';

export interface BandEntry {
  year: number;
  division: string;
  rank: number | null;
  division_size: number | null;
  absolute_position: number | null;
  field_size: number | null;
  points: number | null;
  max_points: number | null;
  conductor: string | null;
  pieces: string[];
}

export interface BandRecord {
  name: string;
  slug: string;
  entries: BandEntry[];
}

export interface DatasetMetadata {
  years: number[];
  divisions: string[];
  max_field_size: number;
  min_year: number;
  max_year: number;
  generated_at: string;
}

export interface BandDataset {
  bands: BandRecord[];
  metadata: DatasetMetadata;
}

export interface StreamingLink {
  spotify?: string | null;
  apple_music?: string | null;
  album?: string | null;
  recording_title?: string | null;
}

export interface PiecePerformance {
  band: string;
  entry: BandEntry;
  streaming?: StreamingLink | null;
}

export interface PieceRecord {
  name: string;
  slug: string;
  composer?: string | null;
  composerNames?: string[];
  performances: PiecePerformance[];
}

export interface ComposerPieceSummary {
  name: string;
  slug: string;
}

export interface ComposerRecord {
  name: string;
  slug: string;
  normalized: string;
  pieces: ComposerPieceSummary[];
}

export interface EliteTestPiece {
  composer: string;
  piece: string;
}

export interface EliteTestPiecesData {
  test_pieces: { [year: string]: EliteTestPiece };
}
