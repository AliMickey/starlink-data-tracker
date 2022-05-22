sqlite3 /app/instance/starlink.db ".schema firmware speedtests" > schema.sql
sqlite3 /app/instance/starlink.db ".dump firmware speedtests" > dump.sql
grep -vx -f schema.sql dump.sql > databaseBackup.sql
mv databaseBackup.sql /app/starlink/static/databaseBackup.sql
rm schema.sql dump.sql