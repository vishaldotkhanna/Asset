PRAGMA foreign_keys = 1;

drop table if exists asset;

drop table if exists user;
create table user(uid integer primary key autoincrement, 
username text not null,
password text not null,
email text not null);


create table asset(aid integer primary key autoincrement,
assetname text not null,
releasedate text,
owner integer default 0,
isreserved integer default 0,
foreign key(owner) references user(uid) on delete set default);


