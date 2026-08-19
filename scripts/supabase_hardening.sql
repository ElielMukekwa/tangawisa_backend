-- Apply to an existing Tangawisa Supabase schema.
-- Safe to re-run: it preserves data and recreates only the backend RLS policies.

alter function public.set_updated_at() set search_path = public, pg_temp;

do $$
begin
    create role tangawisa_backend nologin noinherit;
exception
    when duplicate_object then null;
end $$;

grant usage on schema public to tangawisa_backend;
grant usage on type userrole, messagetype, messagestatus to tangawisa_backend;
grant select, insert, update, delete on all tables in schema public to tangawisa_backend;
grant usage, select on all sequences in schema public to tangawisa_backend;

alter default privileges in schema public
grant select, insert, update, delete on tables to tangawisa_backend;
alter default privileges in schema public
grant usage, select on sequences to tangawisa_backend;

revoke all on all tables in schema public from anon, authenticated;
revoke all on all sequences in schema public from anon, authenticated;
alter default privileges in schema public revoke all on tables from anon, authenticated;
alter default privileges in schema public revoke all on sequences from anon, authenticated;

do $$
declare
    table_name text;
begin
    foreach table_name in array array[
        'users', 'categories', 'shops', 'products', 'product_images',
        'favorites', 'conversations', 'messages', 'notifications', 'reports',
        'support_tickets', 'support_messages', 'site_contents'
    ]
    loop
        execute format('alter table public.%I enable row level security', table_name);
        execute format(
            'drop policy if exists tangawisa_backend_full_access on public.%I',
            table_name
        );
        execute format(
            'create policy tangawisa_backend_full_access on public.%I '
            'for all to tangawisa_backend using (true) with check (true)',
            table_name
        );
    end loop;
end $$;

revoke execute on function public.set_updated_at() from public;
grant execute on function public.set_updated_at() to tangawisa_backend;
