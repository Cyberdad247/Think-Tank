# Deploying Think-Tank to Vercel with Supabase

This guide will walk you through the process of deploying the Think-Tank project to Vercel with Supabase as the database and authentication provider.

## Prerequisites

1. A [Vercel](https://vercel.com) account
2. A [Supabase](https://supabase.com) account
3. An [OpenAI](https://openai.com) account for the vector search functionality

## Step 1: Set up Supabase Project

1. Log in to your Supabase account and create a new project.
2. Note down your Supabase project URL and API keys (anon key and service role key).
3. Enable the pgvector extension:
   - Navigate to the Database section in your Supabase dashboard
   - Click on "Extensions" in the sidebar
   - Find "vector" in the list and toggle it to enable it
   - If you don't see the vector extension, you may need to upgrade to a paid plan that supports it
4. Run the SQL migration script in the Supabase SQL editor:
   - Navigate to the SQL Editor in your Supabase dashboard
   - Copy the contents of `supabase/migrations/20250530_initial_schema.sql`
   - Paste it into the SQL Editor and run the script
   - The script will automatically enable the pgvector extension if it's not already enabled

5. Verify your Supabase setup:
   - Install the project dependencies: `npm install`
   - Run the setup verification script: `npm run check-supabase`
   - This script will check if:
     - Your environment variables are correctly set
     - The pgvector extension is enabled
     - All required tables exist
     - The vector search function is working
   - If any issues are found, the script will provide guidance on how to fix them

## Step 2: Configure Environment Variables

1. Create a `.env.local` file based on the `.env.local.example` template:
   ```
   NEXT_PUBLIC_SUPABASE_URL=your-supabase-project-url
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
   SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key
   OPENAI_API_KEY=your-openai-api-key
   OPENAI_EMBEDDING_MODEL=text-embedding-ada-002
   OPENAI_MODEL=gpt-4
   NEXT_PUBLIC_APP_URL=http://localhost:3000
   ```

2. For local development, replace the placeholder values with your actual API keys.

## Step 3: Deploy to Vercel

1. Push your code to a Git repository (GitHub, GitLab, or Bitbucket).

2. Log in to your Vercel account and create a new project.

3. Import your Git repository.

4. Configure the project:
   - Framework Preset: Next.js
   - Build Command: `npm run build`
   - Output Directory: `.next`
   - Install Command: `npm install`

5. Add Environment Variables:
   - Create the following environment variables in your Vercel project settings:
     - `NEXT_PUBLIC_SUPABASE_URL`: Your Supabase project URL
     - `NEXT_PUBLIC_SUPABASE_ANON_KEY`: Your Supabase anon key
     - `SUPABASE_SERVICE_ROLE_KEY`: Your Supabase service role key
     - `OPENAI_API_KEY`: Your OpenAI API key
     - `OPENAI_EMBEDDING_MODEL`: text-embedding-ada-002
     - `OPENAI_MODEL`: gpt-4
     - `NEXT_PUBLIC_APP_URL`: Your deployed app URL (e.g., https://your-project.vercel.app)

6. Deploy the project.

## Step 4: Configure Supabase Authentication

1. In your Supabase dashboard, go to Authentication > URL Configuration.

2. Add your Vercel deployment URL to the Site URL and Redirect URLs:
   - Site URL: `https://your-project.vercel.app`
   - Redirect URLs: 
     - `https://your-project.vercel.app/auth/callback`
     - `https://your-project.vercel.app`

3. Save the changes.

## Step 5: Test the Deployment

1. Visit your deployed application at `https://your-project.vercel.app`.

2. Test the authentication flow by signing up and signing in.

3. Test the task management functionality by creating, updating, and deleting tasks.

4. Test the vector search functionality if you're using it.

## Troubleshooting

### Authentication Issues

- Make sure your Supabase URL Configuration is correctly set up.
- Check that your environment variables are correctly set in Vercel.
- Verify that the middleware is correctly configured.

### Database Issues

- Check that the SQL migration script ran successfully.
- Verify that the Row Level Security (RLS) policies are correctly set up.
- Check the Supabase logs for any errors.

### Vector Search Issues

- Make sure your OpenAI API key is valid and has sufficient credits.
- Verify that the pgvector extension is enabled in Supabase:
  - Go to Database → Extensions in your Supabase dashboard
  - Ensure "vector" is enabled
  - If you encounter "type vector does not exist" errors, this means the extension is not enabled
- Verify that the vector search function is correctly defined.
- Ensure your embeddings are being properly generated and stored.
- Run the setup verification script to diagnose issues: `npm run check-supabase`

## Maintenance

### Updating the Application

1. Make changes to your codebase locally.
2. Test the changes locally.
3. Push the changes to your Git repository.
4. Vercel will automatically deploy the changes.

### Database Migrations

For future database schema changes:

1. Create a new SQL migration file in the `supabase/migrations` directory.
2. Run the migration locally to test it.
3. Run the migration in your Supabase project using the SQL Editor.

## Security Considerations

- Keep your Supabase service role key secure and never expose it to the client.
- Use Row Level Security (RLS) policies to restrict access to data.
- Regularly rotate your API keys.
- Monitor your Supabase and Vercel logs for suspicious activity.