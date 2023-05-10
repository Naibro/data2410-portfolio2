# data2410-portfolio2

DRTP

Transfers a file between a client and a server using DRTP
		
***********
HOW TO USE
***********

In simpleperf is rather simple. Helpful messages can be shown when specifying the --help or -h flag. For example:
python3 simpleperf.py -h

The program hinges on using either the --server flag or the --client flag in order to start a data transfer. You also need
one server that is on and a client to send data.

In order to run simpleperf, you can for example write:
"python3 simpleperf.py -s" to utilize the default values specified below. This will not give you an interval, but
only a print of the results when the test has finished.

You can then for example run:
"python3 simpleperf.py -c" to run the default values for the client. This will immediately start a transfer and the
results will come after 25 seconds.

You can also send a specific number of bytes with the -n flag like this:
"python3 simpleperf.py -c -n 100MB" or even a specific time with the -t flag.

# Arguments used for the client/sender
parser.add_argument('-c', '--client', action='store_true', help='enable client mode')
parser.add_argument('-f', '--file', type=str, choices=['picture.jpg'], help='input a file to be sent')

# Arguments used for the server/receiver
parser.add_argument('-s', '--server', action='store_true', help='enable server mode')

# Arguments common for both server and client
parser.add_argument('-p', '--port', type=int, default=8088, help='allows selection of a port', metavar='[1024-65535]')
parser.add_argument('-i', '--ipaddress', type=str, default='127.0.0.1', help='allows selection of an ip-address')
parser.add_argument('-r', '--reliability', choices=['stop-and-wait', 'GBN', 'SR'], required=True,
                    help='allows selection of different reliability functions')
parser.add_argument('-t', '--test', type=str, choices=['skip_ack', 'skip_seq'],
                    help='selection of which test case to run')

*****************
THINGS TO NOTICE
*****************

The program has a small bug when the "time" loop has finished and the client and server are supposed
to send an "BYE" and "ACK" message, in which is doesnt print out the results. It seems that
this only happens when specifying the --interval or -i flag. 
Sometimes it works, sometimes not. I'm not sure why that happens.