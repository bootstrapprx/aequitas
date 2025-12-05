# Aequitas Dashboard Layout Redesign Prompt

Please redesign the Aequitas software interface to match the modern dashboard layout shown in the reference video. Here are the specific design requirements:

## Overall Layout Structure

### Header
- Clean white header bar with the "aequitas" logo on the left (lowercase, sans-serif font)
- Center: Page/section title (e.g., "Overviews", "Invoices")
- Right side: Icon toolbar with:
  - Refresh/sync icon
  - Download icon
  - Settings/gear icon
  - Teal/turquoise notification or profile icon
  - Menu/more options icon

### Main Content Area
- Light gray/off-white background (#F5F7FA or similar)
- Card-based layout with white cards featuring subtle shadows
- Generous padding and spacing between cards
- Rounded corners on all cards (8-12px border radius)

## Dashboard/Overview Page Design

### Grid Layout
Create a responsive grid with these card components:

1. **Large Financial Chart Card** (Top Left)
   - Title: "Finamcal" with search icon
   - Area chart with gradient fill (teal/green gradient)
   - Line graph overlay
   - Y-axis values (0-10000)
   - X-axis percentages (3500%, 304, 3400, 400, 3596)
   - Grid lines in light gray

2. **Budget Distribution Donut Chart** (Top Right)
   - Title: "Budget Advisers"
   - Large donut chart with three segments:
     - Dark navy blue (~30%)
     - Yellow/gold (~35%)
     - Teal/turquoise (~35%)
   - Center percentage: "30%"
   - Legend on the right with colored indicators
   - Total value displayed: "8,981"

3. **Large Number Cards** (Bottom Left)
   - Display key metrics with large, bold numbers
   - Format: "138,300" with smaller subtitle text
   - Another card showing "34,3,90" with "Comemned" label in teal

4. **Additional Metrics Cards** (Bottom Right)
   - "24,699" with subtitle labels
   - "Comencities: 15,0,00"
   - "Grtes" with percentage values (11%, 7%)
   - Small donut charts similar to the top right design

## Invoices/List Page Design

### Left Panel - List View
- Title: "Invioces" with close (X) button
- Subtitle: "Manaipces" with expand icon
- List items with:
  - Colored icon on the left (teal, orange, red, yellow, navy)
  - Company/item name
  - Amount on the right
  - Some items show "Paid" stamp in red
  - Examples: "Comecers", "Conepochens", "Botypesol", "Htctoscrinery", "Metionels incobingl", "Trafisergl"

### Right Panel - Details View
- Title: "Mempes" with menu icon
- Summary statistics with small donut charts
- Metric cards showing counts and percentages
- Action buttons:
  - Yellow/gold button: "Errem Drart"
  - Dark navy button (secondary action)
- Bar chart at bottom: "Memges Addatradte"
  - Multi-colored vertical bars (teal, yellow, navy)
  - X-axis labels: "MUTD", "Setchrints", "fandmits", "Emarts"

## Color Palette
Primary colors to use:
- **Teal/Turquoise**: #00B8A9 or similar (primary accent)
- **Dark Navy**: #1A2B4A or similar (secondary accent)
- **Yellow/Gold**: #F8B739 or similar (tertiary accent)
- **White**: #FFFFFF (card backgrounds)
- **Light Gray**: #F5F7FA (page background)
- **Text Dark**: #2D3748 (primary text)
- **Text Light**: #718096 (secondary text)
- **Success Green**: #48BB78 (for positive metrics)
- **Alert Red**: #E53E3E (for warnings/paid stamps)

## Design Principles
1. **Card-based design**: All components should be contained in white cards with shadows
2. **Generous whitespace**: Ample padding within and between cards
3. **Soft shadows**: Use subtle box-shadows (e.g., `0 2px 8px rgba(0,0,0,0.08)`)
4. **Rounded corners**: 8-12px border radius on all cards and components
5. **Clean typography**: Sans-serif font (Inter, SF Pro, or similar)
6. **Consistent iconography**: Use modern, minimalist icons throughout
7. **Data visualization**: Charts should use the color palette consistently
8. **Responsive grid**: Cards should reflow gracefully on different screen sizes
9. **Hover states**: Cards should have subtle hover effects (slight shadow increase or scale)
10. **Micro-interactions**: Smooth transitions and animations (200-300ms)

## Technical Implementation Notes
- Use CSS Grid or Flexbox for the card layout
- Implement with a modern framework (React, Vue, or similar)
- Use a charting library like Chart.js, Recharts, or D3.js for visualizations
- Ensure responsive breakpoints for tablet and mobile views
- Add loading states for data-heavy cards
- Implement smooth page transitions between Overview and detail views

## Specific Component Requirements

### Charts
- Use gradient fills for area charts
- Implement donut charts with centered text
- Bar charts should have rounded tops
- All charts should have hover tooltips showing exact values
- Grid lines should be subtle (light gray, 1px)

### Cards
```css
.card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: all 0.2s ease;
}

.card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
}
```

### Buttons
- Primary button: Teal background with white text
- Secondary button: Navy background with white text
- Tertiary button: Yellow/gold background with dark text
- All buttons should have rounded corners and hover states

### Icons
- Use a consistent icon set (Heroicons, Feather Icons, or similar)
- Icons should be 20-24px for toolbar
- Icons should be 16-20px for inline elements

Please implement this design system across the entire Aequitas application, ensuring consistency in spacing, colors, typography, and interaction patterns throughout all pages and components.