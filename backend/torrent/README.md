you may find that p2p activity is not alllowed on school network

we torrented at home and then brought it over driving to campus and connecting a drive from home

$ du -sh RC_2024-01.zst
32G     RC_2024-01.zst
(ENV3) mycpu:~/ocss/reddit/comments$ du -sh RC_2024-02.zst
29G     RC_2024-02.zst
(ENV3) mycpu:~/ocss/reddit/comments$ du -sh RC_2024-03.zst
31G     RC_2024-03.zst
(ENV3) mycpu:~/ocss/reddit/comments$ zstd -d *.zst
3 files decompressed : 1644029006338 bytes total

$ du -sh RC_2024-01
523G    RC_2024-01

$ du -sh db_data # put into clickhouse
19G
36G
54G
72G
90G

steps:

```bash
clickhouse-client --host 127.0.0.1 --port 9000 --user default --password heyheyhey --database default

```

