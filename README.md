# Collabrative Text Editor

A Collabrative text editing app built in python using Socket Programming and PyQt5 for Frontend GUI.

## Module Requirements:
- [dotenv](https://pypi.org/project/python-dotenv/)
  ```
   pip install python-dotenv
  ```
- [PyQt5](https://pypi.org/project/PyQt5/)
   ```
   pip install PyQt5
   ```

## Instructions to execute the code:
- Create a .env file containing the following keys:
    * HOST: The IP address of the server.
    * PORT: The port number on which server should listen for TCP Requests.
    * CERT_FILE: The path to the SSL Certificate file.
    * KEY_FILE: The path to the SSL Key file.

- Run the server using following command
  ```
  python server.py
  ```

- Run the client using following command
  ```
  python client.pyw
  ```
