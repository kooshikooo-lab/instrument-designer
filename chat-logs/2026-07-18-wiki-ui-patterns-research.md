# Wiki/Knowledge Base UI Patterns for React (Tauri App)

**Research Date:** 2026-07-18
**Target:** Offline-capable instrument design knowledge base in a Tauri/React SPA

---

## Table of Contents

1. [Recommended Tech Stack](#1-recommended-tech-stack)
2. [Content Architecture (Offline-First)](#2-content-architecture-offline-first)
3. [Landing/Index Page: Instrument Catalog](#3-landingindex-page-instrument-catalog)
4. [Individual Instrument Pages](#4-individual-instrument-pages)
5. [Layout & Navigation Patterns](#5-layout--navigation-patterns)
6. [Typography & Visual Design](#6-typography--visual-design)
7. [Rich Content Components](#7-rich-content-components)
8. [Routing Patterns](#8-routing-patterns)
9. [Reference Implementations](#9-reference-implementations)
10. [Actionable Implementation Plan](#10-actionable-implementation-plan)

---

## 1. Recommended Tech Stack

### UI Component Library (Best for This Use Case)

**Primary Recommendation: shadcn/ui + Tailwind CSS**

- Copy-paste components you own — no dependency lock-in
- Built on Radix UI primitives (accessibility-first)
- Tailwind CSS styling — works perfectly in Tauri
- Beautiful defaults, fully customizable
- `npx shadcn@latest add button card input badge tabs accordion` etc.

**Why shadcn/ui over alternatives:**
- MUI/Material UI: Too opinionated, heavy bundle, "Material Design look"
- Ant Design: Enterprise-focused, heavy
- Chakra UI: Good but shadcn has become the ecosystem standard
- Headless UI: Too minimal — shadcn gives you styled components you own

**Also consider:**
- **ReUI** (keenthemes/reui) — 1000+ production-ready shadcn-compatible components including Data Grid, Kanban, Filters, Timeline, Stepper, Tree views
- **Kibo UI** — fills gaps in shadcn ecosystem with niche components

### Markdown/Content Rendering

**Primary: `react-markdown` + plugins**
```bash
npm install react-markdown remark-gfm remark-math rehype-raw rehype-katex react-syntax-highlighter
```

- `react-markdown` — renders MDX-like content
- `remark-gfm` — GitHub Flavored Markdown (tables, task lists, strikethrough)
- `remark-math` + `rehype-katex` — math equations (if needed)
- `rehype-raw` — allows raw HTML in markdown
- `react-syntax-highlighter` (Prism) — code block highlighting
- `mermaid` — diagram rendering

### Search (Offline)

**Fuse.js** — client-side fuzzy search
```bash
npm install fuse.js
```
- Works entirely client-side, no server needed
- Fuzzy matching for instrument names/descriptions
- Lightweight (~6KB gzipped)
- Can index all content at build time

### Routing

**React Router v7** (formerly Remix)
- Nested routes with `<Outlet>`
- Breadcrumb generation via `useMatches()` + `handle` exports
- Hash-based routing works great for Tauri

---

## 2. Content Architecture (Offline-First)

### Option A: JSON-Driven Content (Recommended for Tauri)

Store all instrument data as structured JSON files bundled in the app:

```
src/
  content/
    instruments/
      didgeridoo.json
      kalimba.json
      handpan.json
      ...
    index.json          # master list of all instruments
    types.ts            # TypeScript interfaces
```

**Instrument JSON Schema:**
```json
{
  "id": "kalimba",
  "slug": "kalimba",
  "name": "Kalimba (Thumb Piano)",
  "category": "lamellophone",
  "difficulty": "beginner",
  "tags": ["african", "thumb-piano", "portable", "handmade"],
  "heroImage": "/images/kalimba-hero.jpg",
  "thumbnail": "/images/kalimba-thumb.jpg",
  "description": "A lamellophone instrument originating from Africa...",
  "sections": [
    {
      "id": "description",
      "title": "Overview",
      "content": "The kalimba is a...",
      "type": "markdown"
    },
    {
      "id": "design-tips",
      "title": "3D Design Tips",
      "content": "When modeling in CAD...",
      "type": "markdown"
    },
    {
      "id": "build-instructions",
      "title": "Build Instructions",
      "steps": [...],
      "type": "steps"
    },
    {
      "id": "tuning",
      "title": "Tuning Guide",
      "content": "...",
      "type": "markdown"
    }
  ],
  "resources": [
    { "title": "Kalimba Build Video", "url": "...", "type": "video" },
    { "title": "Free STL Files", "url": "...", "type": "file" }
  ],
  "relatedInstruments": ["mbira", "mbira-thumb-piano"],
  "metadata": {
    "origin": "Sub-Saharan Africa",
    "materials": ["wood", "metal tines"],
    "category": "lamellophone"
  }
}
```

**Why JSON over MDX/Markdown for Tauri:**
- Fully type-safe with TypeScript interfaces
- Easy to query/filter/search at runtime
- No build-time MDX compilation needed
- Perfect for offline — everything is in the bundle
- Can still render markdown content within JSON string fields

### Option B: MDX Files (If You Want Richer Authoring)

```
content/
  instruments/
    kalimba.mdx
    handpan.mdx
  _meta.json          # navigation/ordering
```

Use `frontmatter` for metadata, body for rich content:
```mdx
---
title: Kalimba
category: lamellophone
difficulty: beginner
tags: [african, thumb-piano]
heroImage: /images/kalimba-hero.jpg
---

The kalimba is a lamellophone instrument...

## 3D Design Tips

When modeling in CAD, pay attention to...

## Build Instructions

1. **Cut the base board** — Use 18mm hardwood...
2. **Mount the tines** — ...
```

Use Vite's `import.meta.glob` to import all MDX at build time:
```typescript
const modules = import.meta.glob('./content/instruments/*.mdx', { eager: true });
```

### Option C: Hybrid (JSON Metadata + Markdown Body)

JSON for structured metadata (for filtering/search), markdown files for body content. This gives you the best of both worlds.

**Recommendation for this project:** Option A (JSON-driven) is simplest and most robust for a Tauri app. You can always add MDX later for richer authoring.

---

## 3. Landing/Index Page: Instrument Catalog

### Layout Pattern: Card Grid with Search/Filter

The landing page should follow this structure (inspired by shadcn knowledge base blocks):

```
┌─────────────────────────────────────────────────┐
│  Header: "Instrument Design Wiki"               │
│  ┌─────────────────────────────────────────┐    │
│  │ 🔍 Search instruments...                │    │
│  └─────────────────────────────────────────┘    │
│  [All] [Wind] [String] [Percussion] [Custom]    │
│  ─────────────────────────────────────────────  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │ [Image]  │ │ [Image]  │ │ [Image]  │        │
│  │ Kalimba  │ │ Handpan  │ │ Didgeridoo│       │
│  │ Lamello- │ │ Idio-    │ │ Aerophone │       │
│  │ phone    │ │ phone    │ │           │       │
│  │ ★Beginner│ │ ★Medium  │ │ ★Advanced │       │
│  └──────────┘ └──────────┘ └──────────┘        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │ [Image]  │ │ [Image]  │ │ [Image]  │        │
│  │ Ocarina  │ │ Steel    │ │ Tongue   │        │
│  │          │ │ Drum     │ │ Drum     │        │
│  └──────────┘ └──────────┘ └──────────┘        │
└─────────────────────────────────────────────────┘
```

### Key Components to Build/Use:

**Search Bar** — shadcn `Command` or `Input` with Fuse.js:
```tsx
import { Command, CommandInput, CommandList, CommandItem } from '@/components/ui/command';
import Fuse from 'fuse.js';

const fuse = new Fuse(instruments, {
  keys: ['name', 'category', 'tags', 'description'],
  threshold: 0.3,
});

function InstrumentSearch() {
  const [query, setQuery] = useState('');
  const results = query ? fuse.search(query).map(r => r.item) : instruments;

  return (
    <Command>
      <CommandInput placeholder="Search instruments..." onValueChange={setQuery} />
      <CommandList>
        {results.map(inst => (
          <CommandItem key={inst.id} onSelect={() => navigate(`/instruments/${inst.slug}`)}>
            {inst.name}
          </CommandItem>
        ))}
      </CommandList>
    </Command>
  );
}
```

**Category Filter Pills** — shadcn `Badge` + `ToggleGroup`:
```tsx
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group';
import { Badge } from '@/components/ui/badge';

const categories = ['All', 'Wind', 'String', 'Percussion', 'Lamellophone', 'Idiophone'];

<ToggleGroup type="single" value={activeCategory} onValueChange={setActiveCategory}>
  {categories.map(cat => (
    <ToggleGroupItem key={cat} value={cat}>
      <Badge variant={activeCategory === cat ? 'default' : 'outline'}>{cat}</Badge>
    </ToggleGroupItem>
  ))}
</ToggleGroup>
```

**Instrument Card** — shadcn `Card`:
```tsx
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

function InstrumentCard({ instrument }: { instrument: Instrument }) {
  return (
    <Card className="hover:shadow-lg transition-shadow cursor-pointer"
          onClick={() => navigate(`/instruments/${instrument.slug}`)}>
      <CardHeader className="p-0">
        <img src={instrument.thumbnail} alt={instrument.name}
             className="w-full h-48 object-cover rounded-t-lg" />
      </CardHeader>
      <CardContent className="p-4">
        <CardTitle className="text-lg">{instrument.name}</CardTitle>
        <p className="text-sm text-muted-foreground mt-1">{instrument.category}</p>
        <div className="flex gap-2 mt-2">
          <Badge variant="secondary">{instrument.difficulty}</Badge>
          {instrument.tags.slice(0, 2).map(tag => (
            <Badge key={tag} variant="outline">{tag}</Badge>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
```

**Grid Layout:**
```tsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
  {filteredInstruments.map(inst => (
    <InstrumentCard key={inst.id} instrument={inst} />
  ))}
</div>
```

### shadcn Block Reference

shadcn has pre-built blocks specifically for this pattern:
- **AI Knowledge Base Block** (`shadcn.io/blocks/ai-knowledge-base`) — sidebar + content layout with searchable category tree, collapsible sections
- **Centered Search with Product Card Grid** — hero search + card grid
- **Product Card Grid** — responsive card layout with badges
- **Storefront Search Results** — filter pills + result list

---

## 4. Individual Instrument Pages

### Page Structure

```
┌─────────────────────────────────────────────────────┐
│  Breadcrumbs: Home > Instruments > Kalimba          │
│                                                     │
│  ┌─────────────────────────────────────────────┐    │
│  │  [Hero Image]                               │    │
│  │  Kalimba (Thumb Piano)                      │    │
│  │  Lamellophone · Beginner · African Origin   │    │
│  └─────────────────────────────────────────────┘    │
│                                                     │
│  ┌──────────┐  ┌────────────────────────────┐       │
│  │ Sidebar  │  │ Main Content               │       │
│  │          │  │                            │       │
│  │ ○ Overview│ │ ## Overview                │       │
│  │ ● Design │ │ The kalimba is a...         │       │
│  │ ○ Build  │ │                            │       │
│  │ ○ Tuning │ │ ## 3D Design Tips           │       │
│  │ ○ Media  │ │ When modeling in CAD...     │       │
│  │ ○ Links  │ │                            │       │
│  │          │ │ ## Build Instructions       │       │
│  │          │ │ 1. Cut the base board...   │       │
│  │ Related  │ │ 2. Mount the tines...       │       │
│  │ ┌──────┐ │ │                            │       │
│  │ │Mbira │ │ │ ## Tuning Guide            │       │
│  │ │Ocarin│ │ │ Standard C major tuning... │       │
│  │ └──────┘ │ │                            │       │
│  └──────────┘  └────────────────────────────┘       │
└─────────────────────────────────────────────────────┘
```

### Component Breakdown

**Sidebar (Table of Contents):**
```tsx
// Use shadcn ScrollArea + custom TOC component
import { ScrollArea } from '@/components/ui/scroll-area';

function InstrumentTOC({ sections, activeSection }) {
  return (
    <ScrollArea className="h-[calc(100vh-12rem)]">
      <nav className="space-y-1">
        {sections.map(section => (
          <a key={section.id}
             href={`#${section.id}`}
             className={cn(
               "block px-3 py-2 text-sm rounded-md transition-colors",
               activeSection === section.id
                 ? "bg-primary text-primary-foreground"
                 : "text-muted-foreground hover:text-foreground hover:bg-muted"
             )}>
            {section.title}
          </a>
        ))}
      </nav>
    </ScrollArea>
  );
}
```

**Section Rendering:**
```tsx
function InstrumentSection({ section }) {
  switch (section.type) {
    case 'markdown':
      return (
        <section id={section.id} className="prose prose-neutral dark:prose-invert max-w-none">
          <MarkdownRenderer content={section.content} />
        </section>
      );
    case 'steps':
      return (
        <section id={section.id}>
          <h2>{section.title}</h2>
          <ol className="space-y-4">
            {section.steps.map((step, i) => (
              <li key={i} className="flex gap-4">
                <span className="flex-shrink-0 w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-medium">
                  {i + 1}
                </span>
                <div>
                  <h3 className="font-semibold">{step.title}</h3>
                  <p className="text-muted-foreground">{step.description}</p>
                  {step.image && <img src={step.image} alt={step.title} className="mt-2 rounded-lg" />}
                </div>
              </li>
            ))}
          </ol>
        </section>
      );
    default:
      return null;
  }
}
```

**Related Instruments Section:**
```tsx
function RelatedInstruments({ instruments }) {
  return (
    <div className="grid grid-cols-2 gap-3">
      {instruments.map(inst => (
        <Card key={inst.id} className="hover:shadow-md transition-shadow"
              onClick={() => navigate(`/instruments/${inst.slug}`)}>
          <img src={inst.thumbnail} alt={inst.name} className="w-full h-24 object-cover rounded-t-lg" />
          <CardHeader className="p-3">
            <CardTitle className="text-sm">{inst.name}</CardTitle>
          </CardHeader>
        </Card>
      ))}
    </div>
  );
}
```

---

## 5. Layout & Navigation Patterns

### App Shell Layout

```tsx
// Root layout with sidebar navigation
function AppLayout() {
  return (
    <div className="flex h-screen">
      {/* Left sidebar - persistent navigation */}
      <aside className="w-64 border-r bg-muted/30 flex flex-col">
        <div className="p-4 border-b">
          <h1 className="font-bold text-lg">🎵 Instrument Wiki</h1>
        </div>
        <ScrollArea className="flex-1 p-3">
          <NavTree items={navigationItems} />
        </ScrollArea>
      </aside>

      {/* Main content area */}
      <main className="flex-1 overflow-auto">
        <header className="border-b p-4 flex items-center gap-4">
          <CommandDialog />  {/* ⌘K search */}
          <BreadcrumbNav />
        </header>
        <div className="p-6">
          <Outlet />  {/* React Router outlet for child routes */}
        </div>
      </main>
    </div>
  );
}
```

### Navigation Tree Component

```tsx
// Collapsible sidebar tree (Notion/GitBook style)
function NavTree({ items, level = 0 }) {
  return (
    <ul className={cn("space-y-1", level > 0 && "ml-4")}>
      {items.map(item => (
        <li key={item.id}>
          {item.children ? (
            <Collapsible>
              <CollapsibleTrigger className="flex items-center w-full px-2 py-1.5 text-sm rounded-md hover:bg-muted">
                <ChevronRight className="h-4 w-4 mr-1 transition-transform group-data-[state=open]:rotate-90" />
                {item.label}
              </CollapsibleTrigger>
              <CollapsibleContent>
                <NavTree items={item.children} level={level + 1} />
              </CollapsibleContent>
            </Collapsible>
          ) : (
            <NavLink to={item.path}
                     className={({ isActive }) => cn(
                       "block px-2 py-1.5 text-sm rounded-md transition-colors",
                       isActive ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground"
                     )}>
              {item.label}
            </NavLink>
          )}
        </li>
      ))}
    </ul>
  );
}
```

### Breadcrumbs (React Router v6+ pattern)

```tsx
import { useMatches, Link } from 'react-router-dom';

function Breadcrumbs() {
  const matches = useMatches();

  return (
    <nav aria-label="Breadcrumb">
      <ol className="flex items-center gap-1 text-sm text-muted-foreground">
        {matches
          .filter(m => m.handle?.breadcrumb)
          .map((match, index, arr) => {
            const label = typeof match.handle.breadcrumb === 'function'
              ? match.handle.breadcrumb(match)
              : match.handle.breadcrumb;
            const isLast = index === arr.length - 1;
            return (
              <li key={match.id} className="flex items-center gap-1">
                {index > 0 && <ChevronRight className="h-3 w-3" />}
                {isLast ? (
                  <span className="text-foreground font-medium">{label}</span>
                ) : (
                  <Link to={match.pathname} className="hover:text-foreground">{label}</Link>
                )}
              </li>
            );
          })}
      </ol>
    </nav>
  );
}
```

Route definition with breadcrumbs:
```tsx
const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    handle: { breadcrumb: 'Home' },
    children: [
      { index: true, element: <LandingPage /> },
      {
        path: 'instruments',
        element: <InstrumentsLayout />,
        handle: { breadcrumb: 'Instruments' },
        children: [
          { index: true, element: <InstrumentCatalog /> },
          {
            path: ':slug',
            element: <InstrumentDetail />,
            loader: instrumentLoader,
            handle: {
              breadcrumb: (m) => m.data?.name ?? 'Loading...',
            },
          },
        ],
      },
    ],
  },
]);
```

---

## 6. Typography & Visual Design

### Type Scale (Recommended for Wiki/Documentation)

Use a **Major Second (1.125)** or **Minor Third (1.2)** ratio — documentation-heavy content benefits from subtle hierarchy:

```css
/* Define as CSS custom properties */
:root {
  --font-sans: 'Inter', system-ui, sans-serif;
  --font-serif: 'Source Serif 4', Georgia, serif;
  --font-mono: 'JetBrains Mono', monospace;

  /* Type scale */
  --text-xs: 0.75rem;      /* 12px */
  --text-sm: 0.875rem;     /* 14px */
  --text-base: 1rem;       /* 16px */
  --text-lg: 1.125rem;     /* 18px */
  --text-xl: 1.25rem;      /* 20px */
  --text-2xl: 1.5rem;      /* 24px */
  --text-3xl: 1.875rem;    /* 30px */
  --text-4xl: 2.25rem;     /* 36px */
}
```

### Key Typography Rules

| Property | Value | Why |
|----------|-------|-----|
| Body font-size | `1rem` (16px min) | Accessibility baseline |
| Body line-height | 1.5–1.6 | Readability sweet spot |
| Heading line-height | 1.1–1.3 | Tighter for display text |
| Max content width | `65ch` | 45-75 chars/line for readability |
| Paragraph spacing | `1.5em` | WCAG 1.4.12 recommendation |
| Font sizes | `rem` not `px` | Respects user browser settings |

### Font Pairing Recommendation

- **Headings:** Inter (or Source Serif 4 for editorial feel)
- **Body:** Inter (clean, highly readable on screens)
- **Code:** JetBrains Mono (or Fira Code)
- **Pairing strategy:** Same family, different weights (safest approach)

### Fluid Typography with clamp()

```css
h1 { font-size: clamp(1.875rem, 1.5rem + 2vw, 3rem); }
h2 { font-size: clamp(1.5rem, 1.25rem + 1.5vw, 2.25rem); }
h3 { font-size: clamp(1.25rem, 1rem + 1vw, 1.875rem); }
```

### Color Palette (Instrument Wiki Theme)

```css
:root {
  --background: 0 0% 100%;
  --foreground: 240 10% 3.9%;
  --primary: 240 5.9% 10%;
  --primary-foreground: 0 0% 98%;
  --muted: 240 4.8% 95.9%;
  --muted-foreground: 240 3.8% 46.1%;
  --accent: 240 4.8% 95.9%;
  --border: 240 5.9% 90%;
  --ring: 240 5.9% 10%;
}

.dark {
  --background: 240 10% 3.9%;
  --foreground: 0 0% 98%;
  --primary: 0 0% 98%;
  --primary-foreground: 240 5.9% 10%;
}
```

---

## 7. Rich Content Components

### Markdown Renderer with Full Feature Support

```tsx
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

const markdownComponents = {
  // Headings with anchor links
  h2({ children, ...props }) {
    const id = typeof children === 'string'
      ? children.toLowerCase().replace(/\s+/g, '-').replace(/[^\w-]/g, '')
      : '';
    return <h2 id={id} className="group" {...props}>
      {children}
      <a href={`#${id}`} className="ml-2 opacity-0 group-hover:opacity-100">#</a>
    </h2>;
  },

  // Code blocks with syntax highlighting + copy button
  code({ inline, className, children, ...props }) {
    const match = /language-(\w+)/.exec(className || '');
    const codeContent = String(children).replace(/\n$/, '');

    if (!inline && match) {
      return (
        <div className="my-4 rounded-lg overflow-hidden border">
          <div className="bg-gray-800 text-gray-200 px-4 py-2 flex justify-between items-center text-sm">
            <span>{match[1]}</span>
            <button onClick={() => navigator.clipboard.writeText(codeContent)}
                    className="text-gray-400 hover:text-white">
              <Copy className="h-4 w-4" />
            </button>
          </div>
          <SyntaxHighlighter language={match[1]} style={oneDark}
                             customStyle={{ margin: 0, fontSize: '0.875rem' }}>
            {codeContent}
          </SyntaxHighlighter>
        </div>
      );
    }

    return <code className="bg-muted px-1.5 py-0.5 rounded text-sm font-mono" {...props}>{children}</code>;
  },

  // Tables with horizontal scroll
  table({ children, ...props }) {
    return (
      <div className="overflow-x-auto my-6 rounded-lg border">
        <table className="min-w-full text-sm" {...props}>{children}</table>
      </div>
    );
  },

  // Blockquotes as callouts
  blockquote({ children, ...props }) {
    return (
      <blockquote className="border-l-4 border-primary pl-4 py-2 my-4 bg-muted/50 rounded-r-lg" {...props}>
        {children}
      </blockquote>
    );
  },

  // Images with captions and rounded corners
  img({ src, alt, ...props }) {
    return (
      <figure className="my-6">
        <img src={src} alt={alt} className="rounded-lg w-full" loading="lazy" {...props} />
        {alt && <figcaption className="text-center text-sm text-muted-foreground mt-2">{alt}</figcaption>}
      </figure>
    );
  },
};

function MarkdownRenderer({ content }: { content: string }) {
  return (
    <div className="prose prose-neutral dark:prose-invert max-w-none">
      <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]}
                     components={markdownComponents}>
        {content}
      </ReactMarkdown>
    </div>
  );
}
```

### Collapsible/Toggle Sections

Use shadcn `Collapsible` or `Accordion`:

```tsx
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { ChevronDown } from 'lucide-react';

function CollapsibleSection({ title, children, defaultOpen = false }) {
  return (
    <Collapsible defaultOpen={defaultOpen}>
      <CollapsibleTrigger className="flex items-center justify-between w-full py-3 border-b hover:bg-muted/50 px-2 rounded transition-colors">
        <span className="font-medium">{title}</span>
        <ChevronDown className="h-4 w-4 transition-transform group-data-[state=open]:rotate-180" />
      </CollapsibleTrigger>
      <CollapsibleContent className="pt-4 pb-2">
        {children}
      </CollapsibleContent>
    </Collapsible>
  );
}
```

### Callout/Info Boxes

```tsx
function Callout({ type = 'info', title, children }) {
  const variants = {
    info: { icon: Info, border: 'border-blue-500', bg: 'bg-blue-50 dark:bg-blue-950/30' },
    warning: { icon: AlertTriangle, border: 'border-yellow-500', bg: 'bg-yellow-50 dark:bg-yellow-950/30' },
    tip: { icon: Lightbulb, border: 'border-green-500', bg: 'bg-green-50 dark:bg-green-950/30' },
    danger: { icon: AlertCircle, border: 'border-red-500', bg: 'bg-red-50 dark:bg-red-950/30' },
  };
  const { icon: Icon, border, bg } = variants[type];

  return (
    <div className={cn("border-l-4 rounded-r-lg p-4 my-4", border, bg)}>
      <div className="flex items-center gap-2 font-medium mb-1">
        <Icon className="h-4 w-4" />
        {title}
      </div>
      <div className="text-sm">{children}</div>
    </div>
  );
}
```

### Image Gallery

```tsx
function ImageGallery({ images }: { images: { src: string; caption: string }[] }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 gap-4 my-6">
      {images.map((img, i) => (
        <figure key={i} className="group cursor-pointer">
          <img src={img.src} alt={img.caption}
               className="rounded-lg w-full aspect-square object-cover group-hover:shadow-lg transition-shadow" />
          <figcaption className="text-xs text-muted-foreground mt-2 text-center">{img.caption}</figcaption>
        </figure>
      ))}
    </div>
  );
}
```

---

## 8. Routing Patterns

### Recommended Route Structure

```tsx
const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    handle: { breadcrumb: 'Home' },
    children: [
      {
        index: true,
        element: <LandingPage />,
      },
      {
        path: 'instruments',
        element: <InstrumentsLayout />,
        handle: { breadcrumb: 'Instruments' },
        children: [
          {
            index: true,
            element: <InstrumentCatalog />,
            handle: { breadcrumb: 'Browse' },
          },
          {
            path: ':slug',
            element: <InstrumentDetail />,
            loader: async ({ params }) => {
              const instrument = getInstrument(params.slug);
              if (!instrument) throw new Response('Not Found', { status: 404 });
              return instrument;
            },
            handle: {
              breadcrumb: (match) => match.data?.name ?? 'Loading...',
            },
          },
        ],
      },
      {
        path: 'about',
        element: <AboutPage />,
        handle: { breadcrumb: 'About' },
      },
    ],
  },
]);
```

### Loading States

```tsx
import { useNavigation } from 'react-router-dom';

function InstrumentDetail() {
  const instrument = useLoaderData<typeof instrumentLoader>();
  const navigation = useNavigation();
  const isLoading = navigation.state === 'loading';

  if (isLoading) {
    return (
      <div className="space-y-4 animate-pulse">
        <div className="h-64 bg-muted rounded-lg" />
        <div className="h-8 bg-muted rounded w-1/3" />
        <div className="space-y-2">
          <div className="h-4 bg-muted rounded w-full" />
          <div className="h-4 bg-muted rounded w-5/6" />
          <div className="h-4 bg-muted rounded w-2/3" />
        </div>
      </div>
    );
  }

  return (
    <article>
      {/* ... instrument content */}
    </article>
  );
}
```

### 404 Page for Instruments

```tsx
function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[50vh] text-center">
      <FileQuestion className="h-16 w-16 text-muted-foreground mb-4" />
      <h2 className="text-2xl font-bold mb-2">Instrument Not Found</h2>
      <p className="text-muted-foreground mb-6">
        We couldn't find the instrument you're looking for.
      </p>
      <Button asChild>
        <Link to="/instruments">Browse All Instruments</Link>
      </Button>
    </div>
  );
}
```

---

## 9. Reference Implementations

### Projects to Study

| Project | What to Learn | URL |
|---------|---------------|-----|
| **SST-Docs** | JSON-driven documentation with 16+ content blocks, offline export | github.com/ShadowShardTools/SST-Docs |
| **Papyr React** | Notion-style wiki with FileHierarchy, NoteViewer, GraphView, TableOfContents | github.com/Ray-kong/papyr-react |
| **kbexplorer** | Card grid + constellation graph + reading view for knowledge bases | github.com/anokye-labs/kbexplorer-template |
| **deepwiki-open** | Wiki tree view with sections, importance levels, collapsible navigation | github.com/AsyncFuncAI/deepwiki-open |
| **Codex Wiki** | Three-pane layout (folder tree + editor + preview), full-text search | github.com/bocan/codex |
| **Neuron** | Local-first Markdown workspace with VS Code-style docks | github.com/shiv-khetan/Neuron |
| **Capsa** | MDX docs platform with ⌘K command palette, static prerendering | github.com/SID-Technologies/Capsa |
| **GitHubWiki** | Markdown-powered wiki with Fuse.js search, dark mode, breadcrumbs | github.com/BenDol/GithubWiki |

### Instrument Website Design Patterns

| Site | Key Design Pattern |
|------|-------------------|
| **S.E. Shires** | Category-first editorial layout with visual section breaks, bold typographic headers |
| **MAG Instruments** | Atmospheric colors, clean typography, large-scale images, nature-inspired |
| **Eastman Strings** | Compartmentalized content with image backgrounds, bronze/teal color palette |
| **Knock On Wood** | Bespoke culturally-inspired icons, warm tones, culturally authentic textures |
| **Fender Acoustasonic** | 3D model exploration, parallax scrolling, model comparison grid |
| **D'Angelico** | Scrollable narrative journey, digital storytelling, historical timeline |

### Key Design Lessons from Instrument Sites

1. **Hero imagery is critical** — Close-up instrument photography sells the craft
2. **Category-first navigation** — Group instruments by type, then allow filtering
3. **Editorial tone** — Read more like a curated catalog than a spec sheet
4. **Warm color palettes** — Bronze, cream, warm grays, earthy tones
5. **Typography pairing** — Strong serif headings + clean sans-serif body signals heritage + modernity
6. **3D interaction** — If you have 3D models, make them interactive (Three.js/React Three Fiber)

---

## 10. Actionable Implementation Plan

### Phase 1: Foundation (Week 1)

1. **Setup project** — Vite + React + TypeScript + Tailwind CSS
2. **Install shadcn/ui** — `npx shadcn@latest init`
3. **Add components** — card, badge, input, command, scroll-area, collapsible, separator, tabs, sheet
4. **Setup React Router** — Nested routes with layout
5. **Create app shell** — Sidebar + main content + header with breadcrumbs
6. **Define content schema** — TypeScript interfaces for instrument data
7. **Create sample data** — 3-4 instrument JSON files as proof of concept

### Phase 2: Catalog Page (Week 2)

1. **Build InstrumentCard component** — Image, name, category, difficulty badge
2. **Build filter bar** — Category toggle group + search input
3. **Implement Fuse.js search** — Index all instruments for instant client-side search
4. **Build grid layout** — Responsive card grid (1/2/3 columns)
5. **Add empty state** — When no instruments match search/filter

### Phase 3: Instrument Detail Page (Week 2-3)

1. **Build InstrumentDetail layout** — Hero image + sidebar TOC + main content
2. **Implement MarkdownRenderer** — react-markdown + GFM + syntax highlighting
3. **Build section types** — Markdown, Steps, Image Gallery, Resources
4. **Add callout components** — Info, Warning, Tip blocks
5. **Build collapsible sections** — For build steps, detailed instructions
6. **Add Related Instruments** — Card grid of related instruments
7. **Implement scroll-spy** — Highlight active TOC item based on scroll position

### Phase 4: Polish (Week 3-4)

1. **Add dark mode** — Toggle with system preference detection
2. **Add ⌘K search dialog** — Command palette for quick navigation
3. **Add keyboard shortcuts** — Navigate between instruments (← →)
4. **Optimize images** — Lazy loading, proper aspect ratios
5. **Add loading states** — Skeleton loaders for smooth transitions
6. **Add animations** — Subtle transitions with Framer Motion (optional)
7. **Accessibility audit** — Contrast ratios, keyboard nav, screen reader labels

### Key Packages to Install

```bash
# Core
npm install react-router-dom
npm install tailwindcss @tailwindcss/typography

# shadcn/ui
npx shadcn@latest init
npx shadcn@latest add card badge input command scroll-area collapsible separator tabs sheet dialog

# Content rendering
npm install react-markdown remark-gfm rehype-raw
npm install react-syntax-highlighter @types/react-syntax-highlighter

# Search
npm install fuse.js

# Icons
npm install lucide-react

# Animations (optional)
npm install framer-motion
```

---

## Summary: Quick Decision Guide

| Decision | Recommendation |
|----------|---------------|
| UI Library | **shadcn/ui** + Tailwind CSS |
| Content Format | **JSON files** with markdown body strings |
| Search | **Fuse.js** (client-side, offline) |
| Routing | **React Router v7** with nested routes |
| Markdown | **react-markdown** + remark-gfm + Prism |
| Fonts | **Inter** (body) + **JetBrains Mono** (code) |
| Dark Mode | **CSS variables** + `prefers-color-scheme` |
| Icons | **Lucide React** |
| Color Scheme | Warm neutrals (cream, bronze, charcoal) |
| Layout | Sidebar + main content (wiki-style) |
| Breadcrumbs | `useMatches()` + `handle` exports |
