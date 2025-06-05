create table public.users
(
    id                    varchar(128)            not null
        primary key,
    email                 varchar                 not null
        unique,
    name                  varchar                 not null,
    lastname              varchar                 not null,
    role                  varchar,
    identification_number varchar,
    phone                 varchar,
    address               varchar,
    city                  varchar,
    country               varchar,
    creation_date         timestamp default now() not null,
    last_update           timestamp default now()
);

alter table public.users
    owner to postgres;

create table public.events
(
    creator_id         varchar(128)            not null
        references public.users,
    title              varchar                 not null
        unique,
    description        varchar,
    event_type         varchar,
    status             varchar,
    location           varchar,
    tracks             character varying[],
    notification_mails character varying[],
    review_skeleton    json,
    pricing            json,
    dates              json,
    contact            varchar,
    organized_by       varchar,
    media              json[],
    mdata              json,
    id                 uuid                    not null
        primary key,
    creation_date      timestamp default now() not null,
    last_update        timestamp default now()
);

alter table public.events
    owner to postgres;

create table public.chairs
(
    tracks        character varying[],
    user_id       varchar(128)            not null
        references public.users,
    event_id      uuid                    not null
        references public.events,
    creation_date timestamp default now() not null,
    last_update   timestamp default now(),
    primary key (user_id, event_id)
);

alter table public.chairs
    owner to postgres;

create table public.inscriptions
(
    user_id       varchar(128)            not null
        references public.users,
    event_id      uuid                    not null
        references public.events,
    status        varchar                 not null,
    roles         character varying[]     not null,
    affiliation   varchar,
    id            uuid                    not null
        primary key,
    creation_date timestamp default now() not null,
    last_update   timestamp default now()
);

alter table public.inscriptions
    owner to postgres;

create index ix_inscription_event_id
    on public.inscriptions (event_id);

create index ix_inscription_user_id
    on public.inscriptions (user_id);

create table public.organizers
(
    user_id       varchar(128)            not null
        references public.users,
    event_id      uuid                    not null
        references public.events,
    creation_date timestamp default now() not null,
    last_update   timestamp default now(),
    primary key (user_id, event_id)
);

alter table public.organizers
    owner to postgres;

create table public.works
(
    event_id      uuid                    not null
        references public.events,
    author_id     varchar(128)            not null
        references public.users,
    title         varchar                 not null,
    track         varchar                 not null,
    abstract      varchar                 not null,
    keywords      character varying[]     not null,
    authors       json                    not null,
    talk          json,
    state         varchar                 not null,
    deadline_date timestamp               not null,
    id            uuid                    not null
        primary key,
    creation_date timestamp default now() not null,
    last_update   timestamp default now(),
    constraint event_id_title_uc
        unique (event_id, title)
);

alter table public.works
    owner to postgres;

create table public.reviewers
(
    work_id         uuid                    not null
        references public.works,
    review_deadline timestamp               not null,
    user_id         varchar(128)            not null
        references public.users,
    event_id        uuid                    not null
        references public.events,
    creation_date   timestamp default now() not null,
    last_update     timestamp default now(),
    primary key (work_id, user_id, event_id)
);

alter table public.reviewers
    owner to postgres;

create table public.payments
(
    event_id       uuid                    not null
        references public.events,
    inscription_id uuid                    not null
        references public.inscriptions,
    fare_name      varchar                 not null,
    status         varchar                 not null,
    works          uuid[],
    id             uuid                    not null
        primary key,
    creation_date  timestamp default now() not null,
    last_update    timestamp default now()
);

alter table public.payments
    owner to postgres;

create index ix_payment_inscription_id
    on public.payments (inscription_id);

create index ix_payment_event_id
    on public.payments (event_id);

create table public.submissions
(
    event_id      uuid                    not null
        references public.events,
    work_id       uuid                    not null
        references public.works,
    state         varchar                 not null,
    id            uuid                    not null
        primary key,
    creation_date timestamp default now() not null,
    last_update   timestamp default now()
);

alter table public.submissions
    owner to postgres;

create index ix_submission_event_id
    on public.submissions (event_id);

create index ix_submission_work_id
    on public.submissions (work_id);

create table public.reviews
(
    submission_id uuid
        references public.submissions,
    reviewer_id   varchar(128)
        references public.users,
    event_id      uuid
        references public.events,
    work_id       uuid
        references public.works,
    status        varchar,
    review        json,
    shared        boolean,
    id            uuid                    not null
        primary key,
    creation_date timestamp default now() not null,
    last_update   timestamp default now()
);

alter table public.reviews
    owner to postgres;