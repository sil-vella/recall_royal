--
-- PostgreSQL database dump
--

-- Dumped from database version 14.13 (Debian 14.13-1.pgdg120+1)
-- Dumped by pg_dump version 14.13 (Debian 14.13-1.pgdg120+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: categories; Type: TABLE; Schema: public; Owner: monument_db_user
--

CREATE TABLE public.categories (
    id integer NOT NULL,
    category_name character varying(50) NOT NULL
);


ALTER TABLE public.categories OWNER TO monument_db_user;

--
-- Name: categories_id_seq; Type: SEQUENCE; Schema: public; Owner: monument_db_user
--

CREATE SEQUENCE public.categories_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.categories_id_seq OWNER TO monument_db_user;

--
-- Name: categories_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: monument_db_user
--

ALTER SEQUENCE public.categories_id_seq OWNED BY public.categories.id;


--
-- Name: celebs; Type: TABLE; Schema: public; Owner: monument_db_user
--

CREATE TABLE public.celebs (
    id integer NOT NULL,
    name character varying(100) NOT NULL
);


ALTER TABLE public.celebs OWNER TO monument_db_user;

--
-- Name: celebs_categories; Type: TABLE; Schema: public; Owner: monument_db_user
--

CREATE TABLE public.celebs_categories (
    celeb_id integer NOT NULL,
    category_id integer NOT NULL
);


ALTER TABLE public.celebs_categories OWNER TO monument_db_user;

--
-- Name: celebs_id_seq; Type: SEQUENCE; Schema: public; Owner: monument_db_user
--

CREATE SEQUENCE public.celebs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.celebs_id_seq OWNER TO monument_db_user;

--
-- Name: celebs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: monument_db_user
--

ALTER SEQUENCE public.celebs_id_seq OWNED BY public.celebs.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: monument_db_user
--

CREATE TABLE public.users (
    id integer NOT NULL,
    name character varying(100),
    email character varying(100)
);


ALTER TABLE public.users OWNER TO monument_db_user;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: monument_db_user
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_id_seq OWNER TO monument_db_user;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: monument_db_user
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: categories id; Type: DEFAULT; Schema: public; Owner: monument_db_user
--

ALTER TABLE ONLY public.categories ALTER COLUMN id SET DEFAULT nextval('public.categories_id_seq'::regclass);


--
-- Name: celebs id; Type: DEFAULT; Schema: public; Owner: monument_db_user
--

ALTER TABLE ONLY public.celebs ALTER COLUMN id SET DEFAULT nextval('public.celebs_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: monument_db_user
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: categories; Type: TABLE DATA; Schema: public; Owner: monument_db_user
--

COPY public.categories (id, category_name) FROM stdin;
1	actors
4	streamers
\.


--
-- Data for Name: celebs; Type: TABLE DATA; Schema: public; Owner: monument_db_user
--

COPY public.celebs (id, name) FROM stdin;
1	brad_pitt
2	tom_hanks
3	scarlett_johansson
4	sweet_anita
\.


--
-- Data for Name: celebs_categories; Type: TABLE DATA; Schema: public; Owner: monument_db_user
--

COPY public.celebs_categories (celeb_id, category_id) FROM stdin;
1	1
2	1
3	1
4	4
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: monument_db_user
--

COPY public.users (id, name, email) FROM stdin;
\.


--
-- Name: categories_id_seq; Type: SEQUENCE SET; Schema: public; Owner: monument_db_user
--

SELECT pg_catalog.setval('public.categories_id_seq', 4, true);


--
-- Name: celebs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: monument_db_user
--

SELECT pg_catalog.setval('public.celebs_id_seq', 4, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: monument_db_user
--

SELECT pg_catalog.setval('public.users_id_seq', 1, false);


--
-- Name: categories categories_category_name_key; Type: CONSTRAINT; Schema: public; Owner: monument_db_user
--

ALTER TABLE ONLY public.categories
    ADD CONSTRAINT categories_category_name_key UNIQUE (category_name);


--
-- Name: categories categories_pkey; Type: CONSTRAINT; Schema: public; Owner: monument_db_user
--

ALTER TABLE ONLY public.categories
    ADD CONSTRAINT categories_pkey PRIMARY KEY (id);


--
-- Name: celebs_categories celebs_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: monument_db_user
--

ALTER TABLE ONLY public.celebs_categories
    ADD CONSTRAINT celebs_categories_pkey PRIMARY KEY (celeb_id, category_id);


--
-- Name: celebs celebs_pkey; Type: CONSTRAINT; Schema: public; Owner: monument_db_user
--

ALTER TABLE ONLY public.celebs
    ADD CONSTRAINT celebs_pkey PRIMARY KEY (id);


--
-- Name: celebs unique_celeb_name; Type: CONSTRAINT; Schema: public; Owner: monument_db_user
--

ALTER TABLE ONLY public.celebs
    ADD CONSTRAINT unique_celeb_name UNIQUE (name);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: monument_db_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: celebs_categories celebs_categories_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: monument_db_user
--

ALTER TABLE ONLY public.celebs_categories
    ADD CONSTRAINT celebs_categories_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.categories(id) ON DELETE CASCADE;


--
-- Name: celebs_categories celebs_categories_celeb_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: monument_db_user
--

ALTER TABLE ONLY public.celebs_categories
    ADD CONSTRAINT celebs_categories_celeb_id_fkey FOREIGN KEY (celeb_id) REFERENCES public.celebs(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

