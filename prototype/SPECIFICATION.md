# Technická Specifikace: Katalog Projektů FM TUL

Tento dokument slouží jako technická dokumentace pro aplikaci **Katalog Projektů FM TUL** a návrh architektury pro její rozšíření o backend a perzistentní databázi.

---

## 1. Současný stav (Frontend Prototype)

Aplikace je momentálně implementována jako **Single Page Application (SPA)** běžící v prohlížeči (Client-side), využívající React a TypeScript. Data jsou mockovaná (statická).

### 1.1 Technologie
*   **Framework**: React 19
*   **Jazyk**: TypeScript
*   **Styling**: Tailwind CSS
*   **Ikony**: Lucide React
*   **State Management**: React Context (pro jazyk), `useState` (pro data)
*   **Lokalizace**: Vlastní implementace (`LanguageContext`), podpora CZ/EN.

### 1.2 Funkcionality podle rolí

#### A. Veřejnost (Host)
*   **Dashboard**: Zobrazení seznamu projektů (Grid layout).
*   **Filtrace**: Filtrování podle předmětu a akademického roku.
*   **Vyhledávání**: Fulltextové vyhledávání v názvech a tazích.
*   **Detail projektu**: Modální okno s popisem, týmem, tagy a odkazy (GitHub, Live Demo).
*   **Jazyk**: Možnost přepínání CZ/EN.

#### B. Student
*   **Dashboard**: Stejný jako pro veřejnost.
*   **Studentská zóna**:
    *   Zobrazení "Můj tým" pro aktuální projekty.
    *   **Peer Feedback**: Formulář pro hodnocení kolegů. Rozděleno na:
        *   Silné stránky (Green zone).
        *   Prostor pro zlepšení (Orange zone).
    *   Historie odeslaných hodnocení.

#### C. Lektor (Admin)
*   **Správa projektů**: Formulář pro přidání projektu.
    *   Možnost vybrat studenty ze seznamu nebo přidat manuálně (Jméno + Email).
    *   Validace vstupů.
*   **Správa předmětů**: Přidání nového předmětu (Zkratka, Název).
*   **Přehled hodnocení**: Tabzobrazení všech peer feedbacků seskupených podle projektů.

---

## 2. Návrh Architektury (Backend & Databáze)

Pro přechod z prototypu do produkce je nutné vybudovat backendovou API vrstvu a databázi.

### 2.1 Doporučený Tech Stack

Doporučuji zachovat ekosystém TypeScriptu pro sdílení typů mezi frontendem a backendem.

#### Varianta A: Moderní Fullstack (Next.js) - **DOPORUČENO**
Pokud je cílem rychlý vývoj a SEO optimalizace pro veřejný katalog.
*   **Framework**: Next.js (Migrace ze SPA na SSR/SSG).
*   **Backend**: Next.js API Routes / Server Actions.
*   **ORM**: Prisma nebo Drizzle ORM.
*   **Výhody**: Jeden repozitář, sdílené typy, snadný deployment (Vercel/Docker), výborné SEO pro katalog.

#### Varianta B: Enterprise Standard (NestJS)
Pokud je aplikace součástí většího univerzitního systému mikroservis.
*   **Frontend**: React (stávající).
*   **Backend**: NestJS (Node.js framework).
*   **API**: REST nebo GraphQL.
*   **ORM**: TypeORM.
*   **Výhody**: Striktní architektura, Dependency Injection, snadné testování, oddělení FE a BE týmů.

### 2.2 Databáze

Pro tento typ dat (vztahy mezi studenty, projekty a hodnocením) je nezbytná **Relační databáze (SQL)**. NoSQL (Mongo) se nedoporučuje kvůli potřebě integrity dat (např. aby feedback nezůstal viset po smazání studenta).

*   **Databáze**: **PostgreSQL**
    *   Standard v průmyslu, open-source, robustní, podpora JSON typů (pro tagy nebo metadata).

#### Návrh DB Schématu (ERD Draft)

```sql
-- Enum pro role
CREATE TYPE user_role AS ENUM ('student', 'teacher', 'admin');

-- Tabulka Uživatelů (Studenti i Lektoři)
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  full_name VARCHAR(255) NOT NULL,
  role user_role DEFAULT 'student',
  created_at TIMESTAMP DEFAULT NOW()
);

-- Tabulka Předmětů
CREATE TABLE subjects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code VARCHAR(10) UNIQUE NOT NULL, -- např. WAP
  name VARCHAR(255) NOT NULL
);

-- Tabulka Projektů
CREATE TABLE projects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title VARCHAR(255) NOT NULL,
  short_description VARCHAR(150),
  full_description TEXT,
  academic_year VARCHAR(9) NOT NULL, -- "2023/2024"
  subject_id UUID REFERENCES subjects(id),
  github_url VARCHAR(255),
  live_url VARCHAR(255),
  image_url VARCHAR(255),
  tags TEXT[], -- Array of strings
  created_at TIMESTAMP DEFAULT NOW()
);

-- Vazební tabulka Projekt <-> Student (M:N)
CREATE TABLE project_authors (
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  PRIMARY KEY (project_id, user_id)
);

-- Tabulka Feedbacků
CREATE TABLE feedbacks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id),
  from_user_id UUID REFERENCES users(id),
  to_user_id UUID REFERENCES users(id),
  strengths TEXT NOT NULL,
  improvements TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  CONSTRAINT prevent_self_feedback CHECK (from_user_id != to_user_id)
);
```

### 2.3 Autentizace a Autorizace

Jelikož jde o aplikaci pro TUL, **nesmíte** implementovat vlastní registraci/login s hesly.

1.  **Integrace SSO**: Nutnost napojení na univerzitní **Shibboleth (SAML)** nebo **LDAP**.
2.  **Session Management**:
    *   Při prvním přihlášení přes SSO se uživatel vytvoří v tabulce `users` (pokud neexistuje).
    *   Role (Student vs. Lektor) se ideálně dotáhnou z atributů identity providera (IdP).

### 2.4 API Endpointy (Návrh)

*   `GET /api/projects` - Veřejný, podpora query params `?year=...&subject=...`
*   `GET /api/projects/:id` - Detail projektu.
*   `POST /api/projects` - Admin only (Lektor).
*   `POST /api/feedback` - Auth only (Student), validace, že student je součástí týmu.
*   `GET /api/admin/feedbacks` - Admin only, reporty.

---

## 3. Plán realizace (Roadmap)

1.  **Fáze 1**: Inicializace backend repozitáře (Next.js nebo NestJS) a nastavení Dockeru pro PostgreSQL.
2.  **Fáze 2**: Definice Prisma/TypeORM schématu a migrace databáze.
3.  **Fáze 3**: Vytvoření Seed skriptu pro naplnění DB testovacími daty (z `mockData.ts`).
4.  **Fáze 4**: Implementace API endpointů (CRUD pro projekty a předměty).
5.  **Fáze 5**: Napojení Frontend aplikace na API (nahrazení `useState` za `fetch/axios` nebo React Query).
6.  **Fáze 6**: Implementace SSO loginu (Mock SSO pro dev, Shibboleth pro prod).
