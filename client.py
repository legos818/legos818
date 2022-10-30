import binascii
import socket
import time
import sys
from collections import OrderedDict

def parser(message, start, parts):
    
    message_start = start + 2
    message_segment = message[start:message_start]
    
    message_end = message_start + (int(message_segment, 16) * 2)
    parts.append(message[message_start:message_end])

    if message[message_end:message_end + 2] == "00" or message_end > len(message):
        return parts
    else:
        return parser(message, message_end, parts)

def make_dns_request(addr = "tmz.com"):
    ID     = "0010"
    QR     = "0"
    OPCODE = "0000"
    AA     = "0"
    TC     = "0"
    RD     = "1"
    RA     = "0"
    Z      = "000"
    RCODE  = "0000"

    dns_request = QR
    dns_request += OPCODE
    dns_request += AA
    dns_request += TC
    dns_request += RD
    dns_request += RA
    dns_request += Z
    dns_request += RCODE
    dns_request = "{:04x}".format(int(dns_request, 2))

    QDCOUNT= "0001"
    ANCOUNT= "0000"
    NSCOUNT= "0000"
    ARCOUNT= "0000"

    message = ""
    message += ID
    message += dns_request
    message += QDCOUNT
    message += ANCOUNT
    message += NSCOUNT
    message += ARCOUNT

    split_addr = addr.split(".")
    for word in split_addr:
        split_len = "{:02x}".format(len(word))
        addr_part = binascii.hexlify(word.encode())
        message += split_len
        message += addr_part.decode()

    message += "00" # Terminating bit for QNAME

    # Type of request
    QTYPE = "0001"
    message += QTYPE

    # Class for lookup. 1 is Internet
    QCLASS = "0001"
    message += QCLASS

    return message

def decode_message(message):    
    decoded_ip = []

    ID = message[0:4]
    dns_request = message[4:8]
    QDCOUNT = message[8:12]
    ANCOUNT = message[12:16]
    NSCOUNT = message[16:20]
    ARCOUNT = message[20:24]

    parameters = "{:b}".format(int(dns_request, 16)).zfill(16)

    # Question section
    Q_section = parser(message, 24, [])
    QNAME = ""
 
    for item in Q_section:
        QNAME += (binascii.unhexlify(item).decode())
        QNAME += "."
    QNAME = QNAME[:-1]

    QTYPE_first = 24 + (len("".join(Q_section))) + (len(Q_section) * 2) + 2
    QCLASS_first = QTYPE_first + 4

    QTYPE = message[QTYPE_first:QCLASS_first]
    QCLASS = message[QCLASS_first:QCLASS_first + 4]
    
    print("\nHeader")
    print("ID = ",  ID)
    print("QR", parameters[0:1])
    print("OPCODE", parameters[1:5])

    print("Flags: ")
    print("AA", parameters[5:6])
    print("TC", parameters[6:7])
    print("RD", parameters[7:8])
    print("RA", parameters[8:9])

    print("Z", parameters[9:12])
    print("RCODE", parameters[12:16])
    
    print("\nQuestion Section")
    print("QNAME = ",  QNAME)
    print("QTYPE = ",  QTYPE, " = A")
    print("QCLASS = ",  QCLASS)

    # Answer section
    A_section_first = QCLASS_first + 4
    
    A_total = max([int(ANCOUNT, 16), int(NSCOUNT, 16), int(ARCOUNT, 16)])
    print("\n# ANSWER SECTION")
    
    for answers in range(A_total):
        if (A_section_first < len(message)):
            ANAME = message[A_section_first:A_section_first + 4] # Refers to Question
            ATYPE = message[A_section_first + 4:A_section_first + 8]
            ACLASS = message[A_section_first + 8:A_section_first + 12]
            TTL = int(message[A_section_first + 12:A_section_first + 20], 16)
            RDLENGTH = int(message[A_section_first + 20:A_section_first + 24], 16)
            RDDATA = message[A_section_first + 24:A_section_first + 24 + (RDLENGTH * 2)]

            decode = []
            for pair in range(0, len(RDDATA), 2):
                decode.append(RDDATA[pair:pair+2])

            RDDATA_decoded = ""
            for item in decode:
                RDDATA_decoded += (str(int(item, 16)))
                RDDATA_decoded += "."
            RDDATA_decoded = RDDATA_decoded[:-1]
                
            A_section_first = A_section_first + 24 + (RDLENGTH * 2)

            print("# ANSWER ", answers)
            print("QDCOUNT = ",  QDCOUNT)
            print("ANCOUNT = ",  ANCOUNT)
            print("NSCOUNT = ",  NSCOUNT)
            print("ARCOUNT = ",  ARCOUNT)
            
            print("ANAME = ",  ANAME)
            print("ATYPE = ",  ATYPE, " = A")
            print("ACLASS = ",  ACLASS)
            
            print("\nTTL = ",  TTL)
            print("RDLENGTH = ",  RDLENGTH)
            print("RDDATA = ",  RDDATA)
            print("RDDATA decoded (decoded_message) = ",  RDDATA_decoded, "\n")
            decoded_ip = RDDATA_decoded
    return (decoded_ip)

def send_udp_message(message, addr, port):

    server_addr = (addr, port)

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.sendto(binascii.unhexlify(message), server_addr)
        data, _ = sock.recvfrom(10000)

    return binascii.hexlify(data).decode("utf-8")

####################################################################################

if len(sys.argv) > 1:
    url = sys.argv[1]
else:
    url = "www.tmz.com"
    
message = make_dns_request(url)

print("Request:\n" + message)
print("\nRequest (decoded):")# + decode_message(message))
_ = decode_message(message)

initial_time = time.time()
response = send_udp_message(message, "169.237.229.88", 53)
ending_time = time.time()

elapsed_time = str(ending_time - initial_time)
print('The Round Trip Time is {}'.format(elapsed_time))

print("\nresponse:\n" + response)

print("\nresponse (decoded):")
new_ip = decode_message(response)




#target_host = decode_message2(response)
target_host = "10.10.34.35"

#https://gist.github.com/mrpapercut/92422ecf06b5ab8e64e502da5e33b9f7
 
target_port = 80  # create a socket object 
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
# connect the client 
#client.bind()
initial_time2 = time.time()
client.connect((target_host, target_port))  
 
target_host2 = "tmz.com"
# send some data 
request = "GET / HTTP/1.1\r\nHost:%s\r\n\r\n" % target_host2
client.send(request.encode())  
 
# receive some data 
response = client.recv(10000)  
ending_time2 = time.time()
elapsed_time2 = str(ending_time2 - initial_time2)
print('The Round Trip Time is {}'.format(elapsed_time2))
#http_response = repr(response)
#http_response_len = len(http_response)
 
#display the response
#print("\n[RECV] - length: %d\n" % http_response_len)
print("\n Http request", response.decode())
     
