# Schéma SQLite databáze projektu.
import sqlite3

from common import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS competitions (
    id INTEGER PRIMARY KEY,          -- id soutěže na cz.basketball (/soutez/{id})
    name TEXT,
    area INTEGER,                    -- 0 = celostátní, jinak kraj/oblast
    season TEXT
);
CREATE TABLE IF NOT EXISTS groups (
    id INTEGER PRIMARY KEY,          -- id skupiny/fáze (?p={id})
    competition_id INTEGER,
    name TEXT
);
CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY,          -- id zápasu (/zapas/{id})
    group_id INTEGER,
    round TEXT,
    date TEXT,                       -- ISO YYYY-MM-DD
    time TEXT,
    home TEXT,
    away TEXT,
    home_score INTEGER,
    away_score INTEGER,
    quarters TEXT,                   -- JSON: kumulativní skóre po čtvrtinách [[h,a],...]
    livestats_id INTEGER,
    game_number TEXT,
    venue TEXT,
    -- doplněno z detailu zápasu:
    home_team_id INTEGER,
    away_team_id INTEGER,
    referees TEXT,
    commissioner TEXT,
    attendance INTEGER,
    detail_parsed INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS boxscores (
    match_id INTEGER,
    team_side INTEGER,               -- 1 = domácí, 2 = hosté
    player_id INTEGER,
    jersey TEXT,
    name TEXT,
    minutes TEXT,
    p2m INTEGER, p2a INTEGER,
    p3m INTEGER, p3a INTEGER,
    ftm INTEGER, fta INTEGER,
    oreb INTEGER, dreb INTEGER, reb INTEGER,
    blk INTEGER, ast INTEGER,
    stl INTEGER, tov INTEGER,
    fouls_drawn INTEGER, fouls INTEGER,
    val INTEGER, pts INTEGER, plus_minus INTEGER,
    PRIMARY KEY (match_id, team_side, player_id, name)
);
CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY,          -- id hráče (/hrac/{id})
    name TEXT,
    birth_year INTEGER,
    nationality TEXT,
    position TEXT,
    profile_parsed INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS player_seasons (
    player_id INTEGER,
    season TEXT,
    team TEXT,
    competition TEXT,
    games INTEGER,
    points INTEGER,
    PRIMARY KEY (player_id, season, team, competition)
);
CREATE INDEX IF NOT EXISTS idx_matches_group ON matches(group_id);
CREATE INDEX IF NOT EXISTS idx_box_player ON boxscores(player_id);
CREATE INDEX IF NOT EXISTS idx_box_match ON boxscores(match_id);
"""


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.executescript(SCHEMA)
    return con
