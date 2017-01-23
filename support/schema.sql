CREATE TABLE public.users(
        id SERIAL PRIMARY KEY,
        login VARCHAR(64) NOT NULL,
        password VARCHAR(128) NOT NULL,
        is_admin BOOLEAN DEFAULT false
    );

CREATE TABLE public.nodes(
        id SERIAL PRIMARY KEY,
        hostname VARCHAR(64) NOT NULL,
        workers_count INTEGER DEFAULT 0,
        workers_status JSONB,
        UNIQUE (hostname)
    );

CREATE TABLE public.storages(
        id SERIAL PRIMARY KEY,
        title VARCHAR(255) UNIQUE,
        mountpoint VARCHAR(255) NOT NULL
    );

CREATE TABLE public.watchfolders(
        id SERIAL PRIMARY KEY,
        id_storage INTEGER REFERENCES public.storages(id),
        path VARCHAR(255) NOT NULL,
        settings JSONB,
        UNIQUE(id_storage, path)
    );

CREATE TABLE public.actions(
        id SERIAL PRIMARY KEY,
        title VARCHAR(255) UNIQUE,
        settings XML NOT NULL
    );

CREATE TABLE public.assets(
        id SERIAL PRIMARY KEY,
        id_storage INTEGER REFERENCES public.storages(id),
        path VARCHAR(255),
        fsize INTEGER DEFAULT 0,
        ctime INTEGER DEFAULT 0,
        mtime INTEGER DEFAULT 0,
        meta JSONB,
        report JSONB,
        UNIQUE (id_storage, path)
    );

CREATE INDEX idx_storage ON assets(id_storage);
CREATE INDEX idx_path ON assets(path);
CREATE INDEX idx_mtime ON assets(mtime);

CREATE TABLE public.jobs(
        id_asset INTEGER REFERENCES public.assets(id),
        id_action INTEGER REFERENCES public.actions(id),
        id_node INTEGER,
        id_worker INTEGER,
        status INTEGER DEFAULT 0,
        progress FLOAT DEFAULT 0,
        message TEXT NOT NULL DEFAULT 'Pending',
        creation_time INTEGER DEFAULT 0,
        start_time INTEGER DEFAULT 0,
        end_time INTEGER DEFAULT 0,
        PRIMARY KEY (id_asset, id_action)
    );

CREATE INDEX idx_job_asset ON jobs(id_asset);
CREATE INDEX idx_job_action ON jobs(id_action);
CREATE INDEX idx_job_status ON jobs(status);
CREATE INDEX idx_job_ctime ON jobs(creation_time);

