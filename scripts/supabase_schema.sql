-- Tangawisa backend schema for Supabase PostgreSQL.
-- Run this file in Supabase SQL Editor.
-- It creates the tables used by the current FastAPI SQLAlchemy models.

create extension if not exists pgcrypto;

do $$
begin
    create type userrole as enum ('client', 'seller', 'admin', 'support');
exception
    when duplicate_object then null;
end $$;

do $$
begin
    create type messagetype as enum ('text', 'image', 'file');
exception
    when duplicate_object then null;
end $$;

do $$
begin
    create type messagestatus as enum ('sent', 'delivered', 'read');
exception
    when duplicate_object then null;
end $$;

create or replace function set_updated_at()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql
set search_path = public, pg_temp;

create table if not exists users (
    id bigserial primary key,
    full_name varchar(120) not null,
    email varchar(150) not null unique,
    phone_number varchar(30),
    hashed_password varchar(255) not null,
    role userrole not null default 'client',
    is_active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists categories (
    id bigserial primary key,
    name varchar(80) not null unique,
    slug varchar(100) not null unique,
    description text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists shops (
    id bigserial primary key,
    owner_id bigint not null references users(id),
    name varchar(120) not null unique,
    slug varchar(140) not null unique,
    description text,
    logo_url varchar(255),
    banner_url varchar(255),
    city varchar(80),
    is_active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists products (
    id bigserial primary key,
    shop_id bigint not null references shops(id),
    category_id bigint references categories(id),
    name varchar(150) not null,
    description text,
    price_hint numeric(10, 2),
    stock_quantity integer not null default 0,
    is_active boolean not null default true,
    is_featured boolean not null default false,
    is_new_arrival boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists product_images (
    id bigserial primary key,
    product_id bigint not null references products(id),
    image_url varchar(255) not null,
    display_order integer not null default 0,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists favorites (
    id bigserial primary key,
    user_id bigint not null references users(id),
    product_id bigint not null references products(id),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint uq_favorite_user_product unique (user_id, product_id)
);

create table if not exists conversations (
    id bigserial primary key,
    client_id bigint not null references users(id),
    seller_id bigint not null references users(id),
    shop_id bigint not null references shops(id),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint uq_conversation_pair_shop unique (client_id, seller_id, shop_id)
);

create table if not exists messages (
    id bigserial primary key,
    conversation_id bigint not null references conversations(id),
    sender_id bigint not null references users(id),
    message_type messagetype not null default 'text',
    body text,
    media_url varchar(255),
    reply_to_message_id varchar(50),
    reply_to_preview text,
    status messagestatus not null default 'sent',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists notifications (
    id bigserial primary key,
    user_id bigint not null references users(id),
    title varchar(160) not null,
    body text not null,
    type varchar(50) not null,
    is_read boolean not null default false,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists reports (
    id bigserial primary key,
    reporter_id bigint not null references users(id),
    target_type varchar(30) not null,
    target_id bigint not null,
    reason text not null,
    status varchar(30) not null default 'open',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists support_tickets (
    id bigserial primary key,
    requester_id bigint not null references users(id),
    subject varchar(160) not null,
    description text not null,
    status varchar(30) not null default 'open',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists support_messages (
    id bigserial primary key,
    ticket_id bigint not null references support_tickets(id),
    sender_id bigint not null references users(id),
    body text not null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists site_contents (
    id bigserial primary key,
    site_key varchar(100) not null unique,
    payload jsonb not null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists ix_users_id on users(id);
create index if not exists ix_users_email on users(email);
create index if not exists ix_categories_slug on categories(slug);
create index if not exists ix_shops_owner_id on shops(owner_id);
create index if not exists ix_shops_slug on shops(slug);
create index if not exists ix_products_shop_id on products(shop_id);
create index if not exists ix_products_category_id on products(category_id);
create index if not exists ix_products_name on products(name);
create index if not exists ix_product_images_product_id on product_images(product_id);
create index if not exists ix_favorites_user_id on favorites(user_id);
create index if not exists ix_favorites_product_id on favorites(product_id);
create index if not exists ix_conversations_client_id on conversations(client_id);
create index if not exists ix_conversations_seller_id on conversations(seller_id);
create index if not exists ix_conversations_shop_id on conversations(shop_id);
create index if not exists ix_messages_conversation_id on messages(conversation_id);
create index if not exists ix_messages_sender_id on messages(sender_id);
create index if not exists ix_notifications_user_id on notifications(user_id);
create index if not exists ix_reports_reporter_id on reports(reporter_id);
create index if not exists ix_reports_target_id on reports(target_id);
create index if not exists ix_support_tickets_requester_id on support_tickets(requester_id);
create index if not exists ix_support_messages_ticket_id on support_messages(ticket_id);
create index if not exists ix_support_messages_sender_id on support_messages(sender_id);
create index if not exists ix_site_contents_id on site_contents(id);
create index if not exists ix_site_contents_site_key on site_contents(site_key);

-- Dedicated runtime role used by the FastAPI backend. Its password is managed
-- separately in Vercel/Supabase and is never stored in this migration file.
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

-- Tangawisa clients only use FastAPI. Keep the public Data API closed and let
-- the dedicated backend role pass RLS after the application authorization.
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

drop trigger if exists trg_users_updated_at on users;
create trigger trg_users_updated_at before update on users
for each row execute function set_updated_at();

drop trigger if exists trg_categories_updated_at on categories;
create trigger trg_categories_updated_at before update on categories
for each row execute function set_updated_at();

drop trigger if exists trg_shops_updated_at on shops;
create trigger trg_shops_updated_at before update on shops
for each row execute function set_updated_at();

drop trigger if exists trg_products_updated_at on products;
create trigger trg_products_updated_at before update on products
for each row execute function set_updated_at();

drop trigger if exists trg_product_images_updated_at on product_images;
create trigger trg_product_images_updated_at before update on product_images
for each row execute function set_updated_at();

drop trigger if exists trg_favorites_updated_at on favorites;
create trigger trg_favorites_updated_at before update on favorites
for each row execute function set_updated_at();

drop trigger if exists trg_conversations_updated_at on conversations;
create trigger trg_conversations_updated_at before update on conversations
for each row execute function set_updated_at();

drop trigger if exists trg_messages_updated_at on messages;
create trigger trg_messages_updated_at before update on messages
for each row execute function set_updated_at();

drop trigger if exists trg_notifications_updated_at on notifications;
create trigger trg_notifications_updated_at before update on notifications
for each row execute function set_updated_at();

drop trigger if exists trg_reports_updated_at on reports;
create trigger trg_reports_updated_at before update on reports
for each row execute function set_updated_at();

drop trigger if exists trg_support_tickets_updated_at on support_tickets;
create trigger trg_support_tickets_updated_at before update on support_tickets
for each row execute function set_updated_at();

drop trigger if exists trg_support_messages_updated_at on support_messages;
create trigger trg_support_messages_updated_at before update on support_messages
for each row execute function set_updated_at();

drop trigger if exists trg_site_contents_updated_at on site_contents;
create trigger trg_site_contents_updated_at before update on site_contents
for each row execute function set_updated_at();
