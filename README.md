**A multi-device file backup system**

The client tasks:
* Detect a change in his files that has been made
* Report to the server about the change

The server tasks:
* Backup all of the client files
* Sync all of the client's devices

**The main idea:**

The server is responsible for the backup task, after the client connects to him, the server will check which command the client needs to do, for example - modify, create, delete and more.
The server will execute this command in his backup files.
After that the server will save the command that has been executed for the client's other devices to be synced.

The client's role is to detect changes in his file system and reports to the server for backup.
The client creates a TCP connection with the server, then sends him the command and the file that has been changed (created/modified/deleted/moved...)
When the client connects with another device to the server, the server is executing all of the reported changes by this client on the new connected device. This way the server ensures the synchronization between the devices
