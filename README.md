# Think-Tank

A hybrid system that combines task management functionality with advanced AI research capabilities, leveraging RAG (Retrieval-Augmented Generation) and agentic planning. Now optimized for Vercel Edge Functions and Supabase!

## Project Overview

Think-Tank serves as both:
1. A structured task management platform with features for creating, organizing, and tracking tasks
2. An advanced AI research assistant leveraging RAG and agentic capabilities

This dual nature allows Think-Tank to provide intelligent assistance while maintaining a structured approach to organizing information and workflows.

## Architecture

The Think-Tank architecture follows a modern serverless approach:

- **Frontend Layer**: React and Next.js with component-based architecture
- **Backend Layer**: Next.js Edge Functions (TypeScript)
- **AI Core Services**: RAG Engine, Vector Search with OpenAI embeddings
- **Data Layer**: Supabase (PostgreSQL with pgvector extension)
- **Authentication**: Supabase Auth

## Technology Stack

### Frontend Technologies
- Next.js 14+
- React 18+
- TypeScript
- TailwindCSS
- react-beautiful-dnd

### Backend Technologies
- Next.js Edge Functions
- TypeScript
- Supabase Client SDK

### AI and ML Technologies
- LangChain.js
- OpenAI API (embeddings and completions)
- pgvector for vector search

### Database Technologies
- Supabase (PostgreSQL)
- pgvector extension

### Infrastructure Technologies
- Vercel
- Supabase

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- A Supabase account
- An OpenAI API key

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/think-tank.git
   cd think-tank
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Set up environment variables:
   ```bash
   cp .env.local.example .env.local
   ```
   Then edit `.env.local` with your Supabase and OpenAI credentials.

4. Set up the Supabase database:
   - Create a new Supabase project
   - Run the SQL migration in `supabase/migrations/20250530_initial_schema.sql`

5. Start the development server:
   ```bash
   npm run dev
   ```

## Deployment

For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

## Project Structure

```
think-tank/
├── app/                        # Next.js app directory
│   ├── api/                    # Edge Function API routes
│   │   ├── auth/               # Authentication endpoints
│   │   ├── tasks/              # Task management endpoints
│   │   └── vector-search/      # Vector search endpoints
│   ├── globals.css             # Global styles
│   ├── layout.tsx              # Root layout
│   └── page.tsx                # Main page component
├── components/                 # React components
│   └── TaskChecklist.tsx       # Task checklist component
├── context/                    # React context providers
│   └── TaskContext.tsx         # Task context provider
├── middleware.ts               # Next.js middleware for auth
├── public/                     # Static assets
├── supabase/                   # Supabase configuration
│   └── migrations/             # Database migrations
├── utils/                      # Utility functions
│   └── supabase.ts             # Supabase client
├── .env.local.example          # Example environment variables
├── DEPLOYMENT.md               # Deployment guide
├── next.config.js              # Next.js configuration
├── package.json                # Project dependencies
├── tailwind.config.js          # Tailwind CSS configuration
├── tsconfig.json               # TypeScript configuration
└── vercel.json                 # Vercel deployment configuration
```

## Features

- **Task Management**: Create, update, delete, and reorder tasks
- **Authentication**: Sign up, sign in, and sign out with Supabase Auth
- **Vector Search**: Search for similar documents using OpenAI embeddings and pgvector
- **Real-time Updates**: Real-time task updates using Supabase's Realtime functionality
- **Edge Functions**: Fast, globally distributed API endpoints using Vercel Edge Functions

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the terms of the license included in the repository.
