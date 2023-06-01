import datetime

from sqlalchemy import MetaData, Table, Column, PrimaryKeyConstraint, Index
from sqlalchemy.dialects.mysql import ENUM, JSON, VARCHAR, INTEGER, DATETIME, TINYINT, SMALLINT, TEXT, TIMESTAMP, DOUBLE, BIGINT, DATE, CHAR, BOOLEAN

# metadata object used to relate all tables
metadata = MetaData()

"""
TGstation sql schema models

modelname = Table("tablename", metadata
    Column("columnname", COLUMNTYPE(), kwargs*)*,

    PrimaryKeyConstraint(str),

    [Index("indexname", "columnname"*)]*
)
"""

Admin = Table(
    "admin",
    metadata,
    Column("ckey", VARCHAR(32), nullable=False),
    Column("rank", VARCHAR(32), nullable=False),
    Column("feedback", VARCHAR(255), default=None),
    PrimaryKeyConstraint("ckey"),
)

Admin_Log = Table(
    "admin_log",
    metadata,
    Column("id", INTEGER(11), nullable=False, autoincrement=True),
    Column("datetime", DATETIME(), nullable=False),
    Column("round_id", INTEGER(11, unsigned=True), nullable=False),
    Column("adminckey", VARCHAR(32), nullable=False),
    Column("adminip", INTEGER(10, unsigned=True), nullable=False),
    Column(
        "operation",
        ENUM(
            "add admin",
            "remove admin",
            "change admin rank",
            "add rank",
            "remove rank",
            "chagne rank flags",
        ),
        nullable=False,
    ),
    Column("target", VARCHAR(32), nullable=False),
    Column("log", VARCHAR(1000), nullable=False),
    PrimaryKeyConstraint("id"),
)

Admin_Ranks = Table(
    "admin_ranks",
    metadata,
    Column("rank", VARCHAR(32), nullable=False),
    Column("flags", SMALLINT(5, unsigned=True), nullable=False),
    Column("exclude_flags", SMALLINT(5, unsigned=True), nullable=False),
    Column("can_edit_flags", SMALLINT(5, unsigned=True), nullable=False),
    PrimaryKeyConstraint("rank"),
)

Ban = Table(
    "ban",
    metadata,
    Column("id", INTEGER(11, unsigned=True), nullable=False, autoincrement=True),
    Column("bantime", DATETIME(), nullable=False),
    Column("server_ip", INTEGER(10, unsigned=True), nullable=False),
    Column("server_port", SMALLINT(5, unsigned=True), nullable=False),
    Column("round_id", INTEGER(11, unsigned=True), nullable=False),
    Column("role", VARCHAR(32), default=None),
    Column("expiration_time", DATETIME(), default=None),
    Column("applies_to_admins", TINYINT(1, unsigned=True), nullable=False, default=0),
    Column("reason", VARCHAR(2048), nullable=False),
    Column("ckey", VARCHAR(32), default=None),
    Column("ip", INTEGER(10, unsigned=True), default=None),
    Column("computerid", VARCHAR(32), default=None),
    Column("a_ckey", VARCHAR(32), nullable=False),
    Column("a_ip", INTEGER(10, unsigned=True), nullable=False),
    Column("a_computerid", VARCHAR(32), nullable=False),
    Column("who", VARCHAR(2048), nullable=False),
    Column("adminwho", VARCHAR(2048), nullable=False),
    Column("edits", TEXT(), default=None),
    Column("unbanned_datetime", DATETIME(), default=None),
    Column("unbanned_ckey", VARCHAR(32), default=None),
    Column("unbanned_ip", INTEGER(10, unsigned=True), default=None),
    Column("unbanned_computerid", VARCHAR(32), default=None),
    Column("unbanned_round_id", INTEGER(11, unsigned=True), default=None),
    PrimaryKeyConstraint("id"),
    Index("idx_ban_isbanned", "ckey", "role", "unbanned_datetime", "expiration_time"),
    Index(
        "idx_ban_isbanned_details",
        "ckey",
        "ip",
        "computerid",
        "role",
        "unbanned_datetime",
        "expiration_time",
    ),
    Index(
        "idx_ban_count",
        "bantime",
        "a_ckey",
        "applies_to_admins",
        "unbanned_datetime",
        "expiration_time",
    ),
)

Connection_Log = Table(
    "connection_log",
    metadata,
    Column("id", INTEGER(11), nullable=False, autoincrement=True),
    Column("datetime", DATETIME(), default=None),
    Column("server_ip", INTEGER(10, unsigned=True), nullable=False),
    Column("server_port", SMALLINT(5, unsigned=True), nullable=False),
    Column("round_id", INTEGER(11, unsigned=True), nullable=False),
    Column("ckey", VARCHAR(45), default=None),
    Column("ip", INTEGER(10, unsigned=True), nullable=False),
    Column("computerid", VARCHAR(45), default=None),
    PrimaryKeyConstraint("id"),
)

Death = Table(
    "death",
    metadata,
    Column("id", INTEGER(11), nullable=False, autoincrement=True),
    Column("pod", VARCHAR(50), nullable=False),
    Column("x_coord", SMALLINT(5, unsigned=True), nullable=False),
    Column("y_coord", SMALLINT(5, unsigned=True), nullable=False),
    Column("z_coord", SMALLINT(5, unsigned=True), nullable=False),
    Column("mapname", VARCHAR(32), nullable=False),
    Column("server_ip", INTEGER(10, unsigned=True), nullable=False),
    Column("server_port", SMALLINT(5, unsigned=True), nullable=False),
    Column("round_id", INTEGER(11), nullable=False),
    Column("tod", DATETIME(), nullable=False, comment="Time of death"),
    Column("job", VARCHAR(32), nullable=False),
    Column("special", VARCHAR(32), default=None),
    Column("name", VARCHAR(96), nullable=False),
    Column("byondkey", VARCHAR(32), nullable=False),
    Column("laname", VARCHAR(96), default=None),
    Column("lakey", VARCHAR(32), default=None),
    Column("bruteloss", SMALLINT(5, unsigned=True), nullable=False),
    Column("brainloss", SMALLINT(5, unsigned=True), nullable=False),
    Column("fireloss", SMALLINT(5, unsigned=True), nullable=False),
    Column("oxyloss", SMALLINT(5, unsigned=True), nullable=False),
    Column("toxloss", SMALLINT(5, unsigned=True), nullable=False),
    Column("cloneloss", SMALLINT(5, unsigned=True), nullable=False),
    Column("staminaloss", SMALLINT(5, unsigned=True), nullable=False),
    Column("last_words", VARCHAR(255), default=None),
    Column("suicide", TINYINT(1), nullable=False, default=0),
    PrimaryKeyConstraint("id"),
)

Feedback = Table(
    "feedback",
    metadata,
    Column("id", INTEGER(11, unsigned=True), nullable=False, autoincrement=True),
    Column("datetime", DATETIME(), nullable=False),
    Column("round_id", INTEGER(11, unsigned=True), nullable=False),
    Column("key_name", VARCHAR(32), nullable=False),
    Column(
        "key_type",
        ENUM("text", "amount", "tally", "nested tally", "associative"),
        nullable=False,
    ),
    Column("version", TINYINT(3, unsigned=True), nullable=False),
    Column("json", JSON(), nullable=False),
    PrimaryKeyConstraint("id"),
)

IPintel = Table(
    "ipintel",
    metadata,
    Column("ip", INTEGER(10, unsigned=True), nullable=False),
    Column(
        "date",
        TIMESTAMP(),
        nullable=False,
        default=datetime.datetime.now,
        onupdate=datetime.datetime.now,
    ),
    Column("intel", DOUBLE(), nullable=False, default=0.0),
    PrimaryKeyConstraint("ip"),
    Index("idx_ipintel", "ip", "intel", "date"),
)

Legacy_Population = Table(
    "legacy_population",
    metadata,
    Column("id", INTEGER(11), nullable=False, autoincrement=True),
    Column("playercount", INTEGER(11), default=None),
    Column("admincount", INTEGER(11), default=None),
    Column("time", DATETIME(), nullable=False),
    Column("server_ip", INTEGER(10, unsigned=True), nullable=False),
    Column("server_port", SMALLINT(5, unsigned=True), nullable=False),
    Column("round_id", INTEGER(11, unsigned=True), nullable=False),
    PrimaryKeyConstraint("id"),
)

Library = Table(
    "library",
    metadata,
    Column("id", INTEGER(11), nullable=False, autoincrement=True),
    Column("author", VARCHAR(45), nullable=False),
    Column("title", VARCHAR(45), nullable=False),
    Column("content", TEXT(), nullable=False),
    Column(
        "category",
        ENUM("Any", "Fiction", "Non-Fiction", "Adult", "Reference", "Religion"),
        nullable=False,
    ),
    Column("ckey", VARCHAR(32), nullable=False, default="LEGACY"),
    Column("datetime", DATETIME(), nullable=False),
    Column("deleted", TINYINT(1, unsigned=True), default=None),
    Column("round_id_created", INTEGER(11, unsigned=True), nullable=False),
    PrimaryKeyConstraint("id"),
    Index("deleted_idx", "deleted"),
    Index("idx_lib_id_del", "id", "deleted"),
    Index("idx_lib_del_title", "deleted", "title"),
    Index("idx_lib_search", "deleted", "author", "title", "category"),
)

Messages = Table(
    "messages",
    metadata,
    Column("id", INTEGER(11), nullable=False, autoincrement=True),
    Column(
        "type",
        ENUM("memo", "message", "message sent", "note", "watchlist entry"),
        nullable=False,
    ),
    Column("targetckey", VARCHAR(32), nullable=False),
    Column("adminckey", VARCHAR(32), nullable=False),
    Column("text", VARCHAR(2048), nullable=False),
    Column("timestamp", DATETIME(), nullable=False),
    Column("server", VARCHAR(32), default=None),
    Column("server_ip", INTEGER(10, unsigned=True), nullable=False),
    Column("server_port", SMALLINT(5, unsigned=True), nullable=False),
    Column("round_id", INTEGER(11, unsigned=True), nullable=False),
    Column("secret", TINYINT(1, unsigned=True), nullable=False),
    Column("expire_timestamp", DATETIME(), default=None),
    Column("severity", ENUM("high", "medium", "minor", "none"), default=None),
    Column("lasteditor", VARCHAR(32), default=None),
    Column("edits", TEXT()),
    Column("deleted", TINYINT(1, unsigned=True), nullable=False, default=0),
    Column("deleted_ckey", VARCHAR(32), default=None),
    PrimaryKeyConstraint("id"),
    Index("idx_msg_ckey_time", "targetckey", "timestamp", "deleted"),
    Index(
        "idx_msg_type_ckeys_time",
        "type",
        "targetckey",
        "adminckey",
        "timestamp",
        "deleted",
    ),
    Index("idx_msg_type_ckey_time_odr", "type", "targetckey", "timestamp", "deleted"),
)

Role_Time = Table(
    "role_time",
    metadata,
    Column("ckey", VARCHAR(32), nullable=False),
    Column("job", VARCHAR(32), nullable=False),
    Column("minutes", INTEGER(unsigned=True), nullable=False),
    PrimaryKeyConstraint("ckey", "job"),
)

role_time_log = Table(
    "role_time_log",
    metadata,
    Column("id", BIGINT(20), nullable=False, autoincrement=True),
    Column("ckey", VARCHAR(32), nullable=False),
    Column("job", VARCHAR(128), nullable=False),
    Column("delta", INTEGER(11), nullable=False),
    Column(
        "datetime",
        TIMESTAMP(),
        nullable=False,
        default=datetime.datetime.now,
        onupdate=datetime.datetime.now,
    ),
    PrimaryKeyConstraint("id"),
    Index("ckey", "ckey"),
    Index("job", "job"),
    Index("datetime", "datetime"),
)

Player = Table(
    "player",
    metadata,
    Column("ckey", VARCHAR(32), nullable=False),
    Column("byond_key", VARCHAR(32), default=None),
    Column("firstseen", DATETIME(), nullable=False),
    Column("firstseen_round_id", INTEGER(11, unsigned=True), nullable=False),
    Column("lastseen", DATETIME(), nullable=False),
    Column("lastseen_round_id", INTEGER(11, unsigned=True), nullable=False),
    Column("ip", INTEGER(10, unsigned=True), nullable=False),
    Column("computerid", VARCHAR(32), nullable=False),
    Column("lastadminrank", VARCHAR(32), nullable=False, default="Player"),
    Column("accountjoindate", DATE(), default=None),
    Column("flags", SMALLINT(5, unsigned=True), nullable=False, default=0),
    Column("discord_id", BIGINT(20), default=None),
    PrimaryKeyConstraint("ckey"),
    Index("idx_player_cid_ckey", "computerid", "ckey"),
    Index("idx_player_ip_ckey", "ip", "ckey"),
)

Poll_Option = Table(
    "poll_option",
    metadata,
    Column("id", INTEGER(11), nullable=False, autoincrement=True),
    Column("pollid", INTEGER(11), nullable=False),
    Column("text", VARCHAR(255), nullable=False),
    Column("minval", INTEGER(3), default=None),
    Column("maxval", INTEGER(3), default=None),
    Column("descmin", VARCHAR(32), default=None),
    Column("descmid", VARCHAR(32), default=None),
    Column("descmax", VARCHAR(32), default=None),
    Column(
        "default_percentage_calc", TINYINT(1, unsigned=True), nullable=False, default=1
    ),
    Column("deleted", TINYINT(1, unsigned=True), nullable=False, default=0),
    PrimaryKeyConstraint("id"),
    Index("idx_pop_pollid", "pollid"),
)

Poll_Question = Table(
    "poll_question",
    metadata,
    Column("id", INTEGER(11), nullable=False, autoincrement=True),
    Column(
        "polltype",
        ENUM("OPTION", "TEXT", "NUMVAL", "MULTICHOICE", "IRV"),
        nullable=False,
    ),
    Column("created_datetime", DATETIME(), nullable=False),
    Column("starttime", DATETIME(), nullable=False),
    Column("endtime", DATETIME(), nullable=False),
    Column("question", VARCHAR(255), nullable=False),
    Column("subtitle", VARCHAR(255), default=None),
    Column("adminonly", TINYINT(1, unsigned=True), nullable=False),
    Column("multiplechoiceoptions", INTEGER(2), default=None),
    Column("createdby_ckey", VARCHAR(32), nullable=False),
    Column("createdby_ip", INTEGER(10, unsigned=True), nullable=False),
    Column("dontshow", TINYINT(1, unsigned=True), nullable=False),
    Column("allow_revoting", TINYINT(1, unsigned=True), nullable=False),
    Column("deleted", TINYINT(1, unsigned=False), nullable=False, default=0),
    PrimaryKeyConstraint("id"),
    Index(
        "idx_pquest_question_time_ckey",
        "question",
        "starttime",
        "endtime",
        "createdby_ckey",
        "createdby_ip",
    ),
    Index("idx_pquest_time_deleted_id", "starttime", "endtime", "deleted", "id"),
    Index(
        "idx_pquest_id_time_type_admin",
        "id",
        "starttime",
        "endtime",
        "polltype",
        "adminonly",
    ),
)

Poll_Textreply = Table(
    "poll_textreply",
    metadata,
    Column("id", INTEGER(11), nullable=False, autoincrement=True),
    Column("datetime", DATETIME(), nullable=False),
    Column("pollid", INTEGER(11), nullable=False),
    Column("ckey", VARCHAR(32), nullable=False),
    Column("ip", INTEGER(10, unsigned=True), nullable=False),
    Column("replytext", VARCHAR(2048), nullable=False),
    Column("adminrank", VARCHAR(32), nullable=False),
    Column("deleted", TINYINT(1, unsigned=True), nullable=False, default=0),
    PrimaryKeyConstraint("id"),
    Index("idx_ptext_pollid_ckey", "pollid", "ckey"),
)

Poll_Vote = Table(
    "poll_vote",
    metadata,
    Column("id", INTEGER(11), nullable=False, autoincrement=True),
    Column("datetime", DATETIME(), nullable=False),
    Column("pollid", INTEGER(11), nullable=False),
    Column("optionid", INTEGER(11), nullable=False),
    Column("ckey", VARCHAR(32), nullable=False),
    Column("ip", INTEGER(10, unsigned=True), nullable=False),
    Column("adminrank", VARCHAR(32), nullable=False),
    Column("rating", INTEGER(2), default=None),
    Column("deleted", TINYINT(1, unsigned=True), nullable=False, default=0),
    PrimaryKeyConstraint("id"),
    Index("idx_pvote_pollid_ckey", "pollid", "ckey"),
    Index("idx_pvote_optionid_ckey", "optionid", "ckey"),
)

Game_Round = Table(
    "round",
    metadata,
    Column("id", INTEGER(11), nullable=False, autoincrement=True),
    Column("initialize_datetime", DATETIME(), nullable=False),
    Column("start_datetime", DATETIME(), default=None),
    Column("shutdown_datetime", default=None),
    Column("end_datetime", default=None),
    Column("server_ip", INTEGER(10, unsigned=True), nullable=False),
    Column("server_port", SMALLINT(5, unsigned=True), nullable=False),
    Column("commit_hash", CHAR(40), default=None),
    Column("game_mode", VARCHAR(32), default=None),
    Column("game_mode_result", VARCHAR(64), default=None),
    Column("end_state", VARCHAR(64), default=None),
    Column("shuttle_name", VARCHAR(64), default=None),
    Column("map_name", VARCHAR(32), default=None),
    Column("station_name", VARCHAR(80), default=None),
    PrimaryKeyConstraint("id"),
)

Schema_Revision = Table(
    "schema_revision",
    metadata,
    Column("major", TINYINT(3, unsigned=True), nullable=False),
    Column("minor", TINYINT(3, unsigned=True), nullable=False),
    Column(
        "date",
        DATETIME(),
        nullable=False,
        default=datetime.datetime.now,
        onupdate=datetime.datetime.now,
    ),
    PrimaryKeyConstraint("major", "minor"),
)

Stickyban = Table(
    "stickyban",
    metadata,
    Column("ckey", VARCHAR(32), nullable=False),
    Column("reason", VARCHAR(2048), nullable=False),
    Column("banning_admin", VARCHAR(32), nullable=False),
    Column("datetime", DATETIME(), nullable=False, default=datetime.datetime.now),
    PrimaryKeyConstraint("ckey"),
)

Stickyban_Matched_Ckey = Table(
    "stickyban_matched_ckey",
    metadata,
    Column("stickyban", VARCHAR(32), nullable=False),
    Column("matched_ckey", VARCHAR(32), nullable=False),
    Column("first_matched", DATETIME(), nullable=False, default=datetime.datetime.now),
    Column(
        "last_matched",
        TIMESTAMP(),
        nullable=False,
        default=datetime.datetime.now,
        onupdate=datetime.datetime.now,
    ),
    Column("exempt", TINYINT(1), nullable=False, default=0),
    PrimaryKeyConstraint("stickyban", "matched_ckey"),
)

Stickyban_Matched_Ip = Table(
    "stickyban_matched_ip",
    metadata,
    Column("stickyban", VARCHAR(32), nullable=False),
    Column("matched_ip", INTEGER(unsigned=True), nullable=False),
    Column("first_matched", DATETIME(), nullable=False, default=datetime.datetime.now),
    Column(
        "last_matched",
        TIMESTAMP(),
        nullable=False,
        default=datetime.datetime.now,
        onupdate=datetime.datetime.now,
    ),
    PrimaryKeyConstraint("stickyban", "matched_ip"),
)

Stickyban_Matched_Cid = Table(
    "stickyban_matched_cid",
    metadata,
    Column("stickyban", VARCHAR(32), nullable=False),
    Column("matched_cid", VARCHAR(32), nullable=False),
    Column("first_matched", DATETIME(), nullable=False, default=datetime.datetime.now),
    Column(
        "last_matched",
        TIMESTAMP(),
        nullable=False,
        default=datetime.datetime.now,
        onupdate=datetime.datetime.now,
    ),
    PrimaryKeyConstraint("stickyban", "matched_cid"),
)

Achievements = Table(
    "achievements",
    metadata,
    Column("ckey", VARCHAR(32), nullable=False),
    Column("achievement_key", VARCHAR(32), nullable=False),
    Column("value", INTEGER(), default=None),
    Column(
        "last_updated",
        DATETIME(),
        nullable=False,
        default=datetime.datetime.now,
        onupdate=datetime.datetime.now,
    ),
    PrimaryKeyConstraint("ckey", "achievement_key"),
)

Achievement_Metadata = Table(
    "achievement_metadata",
    metadata,
    Column("achievement_key", VARCHAR(32), nullable=False),
    Column("achievement_version", SMALLINT(unsigned=True), nullable=False, default=0),
    Column("achievement_type", ENUM("achievement", "score", "award"), default=None),
    Column("achievement_name", VARCHAR(64), default=None),
    Column("achievement_description", VARCHAR(512), default=None),
    PrimaryKeyConstraint("achievement_key"),
)

Ticket = Table(
    "ticket",
    metadata,
    Column("id", INTEGER(11, unsigned=True), nullable=False, autoincrement=True),
    Column("server_ip", INTEGER(10, unsigned=True), nullable=False),
    Column("server_port", SMALLINT(5, unsigned=True), nullable=False),
    Column("round_id", INTEGER(11, unsigned=True), nullable=False),
    Column("ticket", SMALLINT(11, unsigned=True), nullable=False),
    Column("action", VARCHAR(20), nullable=False, default="Message"),
    Column("message", TEXT(), nullable=False),
    Column("timestamp", DATETIME(), nullable=False),
    Column("recipient", VARCHAR(32), default=None),
    Column("sender", VARCHAR(32), default=None),
    PrimaryKeyConstraint("id"),
)

Discord_Links = Table(
    "discord_links",
    metadata,
    Column("id", INTEGER(11, unsigned=True), nullable=False, autoincrement=True),
    Column("ckey", VARCHAR(32), nullable=False),
    Column("discord_id", BIGINT(20), nullable=True, default=None),
    Column("timestamp", DATETIME(), nullable=False),
    Column("one_time_token", VARCHAR(100), nullable=False),
    Column("valid", BOOLEAN(), nullable=False, default=False),
    PrimaryKeyConstraint("id"),
)
