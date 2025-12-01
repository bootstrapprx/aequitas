REBUILD THE MASTER CHART (PREMIUM VERSION)
🎯 Goal

Restore and significantly enhance the Master Chart Dashboard inside the ChartForge module of Aequitas.
The new page must be modern, visually rich, analytics-driven, and far superior to the previous layout — including tree, list, and card views, with premium UI components.

1. Create a premium layout for the Master Chart Dashboard

Design a new Master Chart Dashboard page with:

Header

Large title: Master Chart Dashboard

Subtitle showing the active template or database view

Right-aligned actions:

“Interactive Editor”

“View Tree”

“Add Account”

Optional breadcrumbs

Smooth motion transitions (Framer Motion)

2. Rebuild KPI cards (analytics summary)

Create a metrics panel showing:

Total Accounts

Header Accounts

Detail Accounts

Orphan Accounts

Categories

Unique Tags

Visual requirements:

rounded-2xl

shadow-lg shadow-black/20

Icons using lucide-react inside soft gradient circles

Bold numbers (text-3xl font-bold)

Secondary label text (text-sm text-muted-foreground)

Subtle hover/entry animations (motion.div)

This KPI bar should be significantly more modern and premium than the previous version.

3. Add an “Analytics & Insights” section with charts

Insert a full analytics block below the KPIs.

Use Recharts to create:

Chart 1 — Account Types Distribution

Pie chart

Counts of: Assets, Liabilities, Equity, Revenue, Expense

Chart 2 — Categories Breakdown

Horizontal bar chart

Shows how accounts are distributed across categories

Chart 3 — Hierarchy Depth

Bar chart showing number of header levels vs detail items

Helps visualize structural density

Charts should:

Use the default theme colors

Animate on load

Have tooltips and labels

Fit inside responsive cards (rounded-xl border shadow)

4. Add a Notion-style view selector

Implement a modern segmented control with:

[ Tree View ] [ List View ] [ Cards View ]


Each tab switches the central content area.

5. Implement each view
A. Tree View (hierarchical)

Collapsible tree structure

Clean indentation

Icons for header/detail

Actions per node:

Add Child

Edit

Delete

View Details

Smooth collapse/expand animations

B. List View (spreadsheet-like)

DataTable using shadcn/ui

Columns:

Code

Name

Type

Category

Normal Balance

Tags

Status

Actions

Features:

Fuzzy search

Column sorting

Resizable columns

Sticky header

Pagination

C. Cards View (portfolio-style)

Grid of cards

Each card displays:

Code (large)

Name

Type + category badges

Tag chips

Parent header info

Action buttons

Card design:

rounded-2xl

shadow-lg

Hover lift (-translate-y-1)

Motion fade-in

6. Add a right-side “Account Details Panel”

When selecting an account in any view, open a side panel:

Tabs: Overview / Structure / Rollups / Categories / Tags / History

Show metadata, children, and related accounts

Keep the panel collapsible or slide-over (Dialog or Sheet)

7. Filtering Bar (top of page)

Recreate an advanced filter bar:

Fuzzy search

Category filter

Type filter

Normal Balance filter

Tags filter

“Reset Filters” button

Use shadcn/ui components with:

flex gap-4 items-center

rounded-xl border px-4 py-3

8. Visual Style Requirements (Premium)

Follow these principles:

Spacing similar to QuickBooks / Linear:

Page: p-8 md:p-10

Sections: mt-8

Large rounded surfaces (rounded-2xl)

Soft shadows (shadow-xl)

Dark theme optimization

Smooth transitions for all interactions

Consistent typography scale:

Title: text-3xl font-semibold

Subtitles: text-lg text-muted-foreground

Body: text-sm or text-base

9. Keep backend integration exactly as is

Do not modify endpoints or backend logic.
Only improve the UI, design, layout, and React structure.

10. Acceptance Criteria

The Master Chart page looks significantly more modern than the previous version.

Multiple visualization modes (tree, list, cards) are implemented and functional.

Analytics charts are rendered and responsive.

KPI cards are premium-grade.

All existing functionality (search, filters, detail view, actions) continues working.

No loss of data, no breaking changes.