declare module 'react-simple-maps' {
  import { FC, ReactNode, MouseEvent, CSSProperties } from 'react'

  export interface GeoRecord {
    rsmKey: string
    id: string
    properties: Record<string, unknown>
    geometry: Record<string, unknown>
  }

  export interface ProjectionConfig {
    scale?: number
    center?: [number, number]
    rotate?: [number, number, number]
    parallels?: [number, number]
    precision?: number
  }

  export interface ComposableMapProps {
    projection?: string
    projectionConfig?: ProjectionConfig
    style?: CSSProperties
    className?: string
    children?: ReactNode
  }

  export interface ZoomableGroupProps {
    zoom?: number
    minZoom?: number
    maxZoom?: number
    center?: [number, number]
    children?: ReactNode
  }

  export interface GeographiesProps {
    geography: string | object
    children: (props: { geographies: GeoRecord[] }) => ReactNode
  }

  export interface GeographyStyleEntry {
    fill?: string
    stroke?: string
    strokeWidth?: number
    outline?: string
    cursor?: string
  }

  export interface GeographyProps {
    geography: GeoRecord
    fill?: string
    stroke?: string
    strokeWidth?: number
    style?: {
      default?: GeographyStyleEntry
      hover?: GeographyStyleEntry
      pressed?: GeographyStyleEntry
    }
    onMouseEnter?: (event: MouseEvent<SVGPathElement>) => void
    onMouseLeave?: (event: MouseEvent<SVGPathElement>) => void
    onClick?: (event: MouseEvent<SVGPathElement>) => void
    className?: string
  }

  export interface MarkerProps {
    coordinates: [number, number]
    children?: ReactNode
    onMouseEnter?: (event: MouseEvent<SVGPathElement>) => void
    onMouseLeave?: (event: MouseEvent<SVGPathElement>) => void
    onClick?: (event: MouseEvent<SVGPathElement>) => void
    style?: {
      default?: CSSProperties
      hover?: CSSProperties
      pressed?: CSSProperties
    }
  }

  export const ComposableMap: FC<ComposableMapProps>
  export const ZoomableGroup: FC<ZoomableGroupProps>
  export const Geographies: FC<GeographiesProps>
  export const Geography: FC<GeographyProps>
  export const Marker: FC<MarkerProps>
}
