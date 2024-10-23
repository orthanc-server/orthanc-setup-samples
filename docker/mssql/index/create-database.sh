#run the setup script to create the DB and the schema in the DB
#do this in a loop because the timing for when the SQL instance is ready is indeterminate
echo "----------------- creating database ---------------------------------"

for i in {1..50};
do
    /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P MyStrOngPa55word! -No -Q 'CREATE DATABASE orthanctest'
    if [ $? -eq 0 ]
    then
        echo "----------------- database created"
        break
    else
        echo "----------------- not ready yet..."
        sleep 1
    fi
done