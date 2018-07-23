#!/usr/bin/python2.7

import time, socket, os, sys, json, errno


def main(*argv):
    interval = 10
    default_port = 9989

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        arguments = argv[0]
        if len(arguments) == 1:
            server_address = ('localhost', default_port)
        elif len(arguments) == 2:
            server_address = (str(arguments[1]), default_port)
        elif len(arguments) == 3:
            server_address = (str(arguments[1]), int(arguments[2]))

        print("connecting to vnet watcher. %s " % str(server_address))
        sock.connect(server_address)
        print("connected successfully.")

        time.sleep(3)

        send_close = True

        while True:
            message = 'get_vswitch_port'
            sock.sendall(message)
        
            data = sock.recv(4096) 

            data_loaded = json.loads(data)

            os.system('clear')
            title = "[Switch Name: (MAC Address)]\n"
            title = title + "  [Port Name]"
            title = title + " "*9 + "[MAC Address]"
            title = title + " "*8 + "[IP Address]"
            title = title + " "*7 + "[Port No]"
            print title
            print "="*75
            index = 0

            for key, value in data_loaded.iteritems():
                dpid = key
                name  = value[0]
                ports = value[1]
                print("%s: (%s)" % (name, dpid))

                for port in ports:
                    nameLen   = len(str(port['name']))
                    portLen   = len(str(port['port_no']))
                    ipLen     = len(str(port['ip']))
                    nameSpace = " "*(20-nameLen)
                    portSpace = " "*(9-portLen)
                    ipSpace   = " "*(19-ipLen)
                    outstr = " "*2
                    outstr = outstr + port['name']    + nameSpace
                    outstr = outstr + port['hw_addr'] + " "*4
                    outstr = outstr + port['ip'] + ipSpace
                    outstr = outstr + port['port_no'] + portSpace
                    print("%s" % outstr)
                    index += 1
                print("\nTotal %s ports, update interval %s seconds.\n" % (index, interval))
        
            time.sleep(interval)

    except socket.error as e:
        if e.errno == errno.ECONNREFUSED:
            print("connection refused.")
            send_close = False
        else:
            print("Error, %s" %e)

    except KeyboardInterrupt as e:
        print("client stop.")

    except Exception as e:
        print("Error, %s" %e)

    finally:
        if send_close:
            sock.sendall('client_close')
        sock.close()


if __name__ == '__main__':
    main(sys.argv)
