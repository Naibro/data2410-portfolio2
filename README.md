# data2410-portfolio2

DRTP - application.py

Transfers a file between a client and a server using DRTP
		
**********
HOW TO USE
**********

The program requires the use of two running instances in order to start a file transfer.
One with the --server flag, and the other with --client flag, although the server
can be left running once it has been started, and then followed by a client instance.

In order to run the application, you have to first start the server using the -s flag,
including one of three reliable methods (stop-and-wait, GBN or SR).
For example: "python3 application.py -s -r stop-and-wait".
This will give you a running server using the stop-and-wait method.

After running the server, the client can be run the same way, but needs a file name to be transferred using the -f flag:
"python3 application.py -c -r stop-and-wait -f picture.gif". This will give you a running client using the
stop-and-wait method and the specified file will be sent.

**Both the server and the client** need to use the same reliable method in order to work properly.
The same goes for the -i (--ipaddress) and -p (--port) flags. If they are not specified however, the default
ip-address '127.0.0.1' and port '8088' will be used. The program also checks if the ip-address and the port are valid.

It is also possible to run the server and the client with an artificial test by specifying one of two test cases
(skip_ack or skip_seq) using the -t or the --test flag, but this flag doesn't have to be used.
**skip_ack** is used by the server and **skip_seq** is used by the client.

Also by specifying the --help or -h flag, helpful messages can be shown.
For example: "python3 application.py -h".

******************
ARGPARSE ARGUMENTS
******************

# Arguments used for the client/sender
parser.add_argument('-c', '--client', action='store_true', help='enable client mode')

parser.add_argument('-f', '--file', type=str, choices=['picture.gif'], help='input a file to be sent', required=True)
# Arguments used for the server/receiver
parser.add_argument('-s', '--server', action='store_true', help='enable server mode')
# Arguments common for both server and client
parser.add_argument('-p', '--port', type=int, default=8088, help='allows selection of a port', metavar='[1024-65535]')

parser.add_argument('-i', '--ipaddress', type=str, default='127.0.0.1', help='allows selection of an ip-address')

parser.add_argument('-r', '--reliability', choices=['stop-and-wait', 'GBN', 'SR'], required=True,
                    help='allows selection of different reliability functions')

parser.add_argument('-t', '--test', type=str, choices=['skip_ack', 'skip_seq'],
                    help='selection of which test case to run')

**skip_ack** is used for the server side and the **skip_seq** is used for the client side.

*****************
THINGS TO NOTICE
*****************

?