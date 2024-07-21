sqlite3 /app/instance/starlink.db ".schema firmware" > schema.sql
sqlite3 /app/instance/starlink.db ".dump firmware" > dump.sql

grep -vx -f schema.sql dump.sql > databaseBackup.sql
chmod 755 databaseBackup.sql
mv databaseBackup.sql /app/app/static/other/databaseBackup.sql

rm schema.sql dump.sql