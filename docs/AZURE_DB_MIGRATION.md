# Azure Database Migration Guide

This guide describes how to extract data from a PostgreSQL database located within a private Azure VNet and migrate it to the new server (`swe.fm.tul.cz`).

## Overview
The Azure PostgreSQL instance is not publicly accessible. To extract the data, we must use a "jumpbox" VM within the same VNet.

## Prerequisites
*   Access to the Azure Portal.
*   Permission to create a small Virtual Machine in the target VNet.
*   The hostname, username, and password for the Azure PostgreSQL instance.

## Step 1: Create a Temporary Jumpbox
1.  In the Azure Portal, create a new **Ubuntu Server 22.04 LTS** Virtual Machine.
2.  **Networking:** Ensure it is placed in the **same Virtual Network** and a subnet that has connectivity to the Azure PostgreSQL instance.
3.  **Public IP:** Enable a public IP and SSH (port 22) so you can connect to it.

## Step 2: Install PostgreSQL Client
SSH into the jumpbox and install the required tools:
```bash
sudo apt-get update
sudo apt-get install -y postgresql-client
```

## Step 3: Extract the Data (pg_dump)
Run the following command to create a custom-format dump of your database:
```bash
pg_dump -h <AZURE_DB_HOSTNAME> -U <DB_USER> -d <DB_NAME> -F c -f db_backup.dump
```
*When prompted, enter the database password.*

## Step 4: Transfer the Dump to the New Server
From the jumpbox, use `scp` to transfer the dump file to `swe.fm.tul.cz`:
```bash
scp db_backup.dump <USER>@swe.fm.tul.cz:/home/<USER>/
```

## Step 5: Restore the Data
SSH into `swe.fm.tul.cz` and restore the dump into the local PostgreSQL instance:
```bash
pg_restore -h localhost -U <LOCAL_USER> -d <LOCAL_DB_NAME> -C -1 db_backup.dump
```
*Note: The `-C` flag creates the database if it doesn't exist. The `-1` runs the restore in a single transaction.*

## Step 6: Cleanup
1.  Verify the data on the new server.
2.  **Delete the temporary Azure VM** to avoid ongoing costs.
