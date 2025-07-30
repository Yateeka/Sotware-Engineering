# Interactive 2D World Map Component

A fully interactive 2D world map component built with React, Next.js, and react-simple-maps. This component provides a clean, responsive, and interactive way to visualize countries around the world.

## Features

✅ **2D Mercator Projection** - Flat, accurate geographical representation  
✅ **Interactive Hover Effects** - Countries highlight and scale on hover  
✅ **Click Actions** - Alert displays with country name when clicked  
✅ **Real-time Country Display** - Shows hovered country name below the map  
✅ **Fully Responsive** - Works perfectly on all device sizes  
✅ **React Hooks Integration** - Uses useState for state management  
✅ **Tailwind CSS Styling** - Clean, modern styling with smooth transitions  
✅ **TypeScript Support** - Full type safety and IntelliSense  

## Installation

1. Install the required dependency:
```bash
npm install react-simple-maps --legacy-peer-deps
```

2. Copy the component file `components/WorldMap.tsx` to your project

3. Import and use the component:
```tsx
import WorldMap from '../components/WorldMap';

function MyPage() {
  return (
    <div>
      <h1>My Interactive Map</h1>
      <WorldMap />
    </div>
  );
}
```

## Component API

The `WorldMap` component is a functional React component that doesn't require any props. It manages its own state internally.

### State Management
- `hoveredCountry`: Tracks which country is currently being hovered
- `clickedCountry`: Tracks the last clicked country

### Key Functions
- `getCountryName(geo)`: Extracts country name from geography data
- `handleMouseEnter(geo)`: Handles country hover events
- `handleMouseLeave()`: Handles mouse leave events
- `handleClick(geo)`: Handles country click events

## Data Source

The component uses the reliable public TopoJSON source:
```
https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json
```

This provides accurate geographical data for all countries worldwide.

## Styling

The component uses Tailwind CSS classes for styling and includes:
- Responsive design with `max-w-6xl` container
- Smooth transitions and hover effects
- Blue color scheme for interactivity
- Card-like design with shadows and rounded corners
- Gradient backgrounds for visual appeal

## Usage Examples

### Basic Usage
```tsx
<WorldMap />
```

### With Custom Container
```tsx
<div className="my-custom-container">
  <h2>Countries of the World</h2>
  <WorldMap />
</div>
```

## Browser Compatibility

- Modern browsers with ES6+ support
- React 16.8+ (hooks support)
- Next.js 12+ recommended

## Customization

The component can be easily customized by modifying:
- Color schemes in the `style` prop of `Geography` components
- Container styling and layout
- Country name display format
- Click action behavior (currently shows alert)

## File Structure

```
components/
  WorldMap.tsx              # Main component
types/
  react-simple-maps.d.ts    # TypeScript definitions
pages/
  map.tsx                   # Basic map page
  standalone-map.tsx        # Full-featured demo page
```

## Dependencies

- `react` (^19.0.0)
- `react-simple-maps` (^3.0.0)
- `tailwindcss` (^4)
- `next` (15.3.5)

## Technical Details

- **Projection**: geoMercator with scale: 130, center: [0, 20]
- **Dimensions**: 1000x500 (responsive)
- **Performance**: Optimized with React.memo potential
- **Accessibility**: Keyboard navigation support can be added

## License

This component is part of your project and follows your project's license terms.
