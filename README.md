 TODO List:
 Part I:
      * Wireshark TCP protocol.
      * Using the code from the module.
 Part II:
       **Server:**  The cloud.
          ** Gets as parameter a port to listen to.
          * Holds List of identities for each client, as well as IPs for different computers
            and backup files.
          * Differs between different computer using IP.
          * Function to backup files.
          * Can send updates to a client about changes on a different computer.
          * Has a time interval of asking the server if there are any changes.
          
      **Client:** Can work from different computers and directories.
           ** Gets as parameters IP address, Port, directory to a folder, time lap of approaching the server.
            And identity (Optional).
            
           * Holds an identity - 128 long string, with random chars & digits.
           * Hold a directories to files for backup.
           
           * The client needs to monitor any changes in the files or sub-files 
              Then send it to **deep** backup in the server.
           * Commit changes on another computer.
