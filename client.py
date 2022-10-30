import binascii
import socket
import time
import sys
from collections import OrderedDict

def get_type(type):
    types = [
        "ERROR", # type 0 does not exist
        "A",
        "NS",
        "MD",
        "MF",
        "CNAME",
        "SOA",
        "MB",
        "MG",
        "MR",
        "NULL",
        "WKS",
        "PTS",
        "HINFO",
        "MINFO",
        "MX",
        "TXT"
    ]

    return "{:04x}".format(types.index(type)) if isinstance(type, str) else types[type]

def parse_parts(message, start, parts):
    part_start = start + 2
    part_len = message[start:part_start]
    
    if len(part_len) == 0:
        return parts
    
    part_end = part_start + (int(part_len, 16) * 2)
    parts.append(message[part_start:part_end])

    if message[part_end:part_end + 2] == "00" or part_end > len(message):
        return parts
    else:
        return parse_parts(message, part_end, parts)

def make_dns_request(type = "A", address = "tmz.com"):
    ID     = 10
    QR     = 0
    OPCODE = 0
    AA     = 0
    TC     = 0
    RD     = 1
    RA     = 0
    Z      = 0
    RCODE  = 0

    query_params = str(QR)
    query_params += str(OPCODE).zfill(4)
    query_params += str(AA) + str(TC) + str(RD) + str(RA)
    query_params += str(Z).zfill(3)
    query_params += str(RCODE).zfill(4)
    query_params = "{:04x}".format(int(query_params, 2))

    QDCOUNT= 1
    ANCOUNT= 0
    NSCOUNT= 0
    ARCOUNT= 0

    message = ""
    message += "{:04x}".format(ID)
    message += query_params
    message += "{:04x}".format(QDCOUNT)
    message += "{:04x}".format(ANCOUNT)
    message += "{:04x}".format(NSCOUNT)
    message += "{:04x}".format(ARCOUNT)

    addr_parts = address.split(".")
    for part in addr_parts:
        addr_len = "{:02x}".format(len(part))
        addr_part = binascii.hexlify(part.encode())
        message += addr_len
        message += addr_part.decode()

    message += "00" # Terminating bit for QNAME

    # Type of request
    QTYPE = get_type(type)
    message += QTYPE

    # Class for lookup. 1 is Internet
    QCLASS = 1
    message += "{:04x}".format(QCLASS)

    return message

def decode_message(message):    
    res = []
    res2 =[]

    ID            = message[0:4]
    query_params  = message[4:8]
    QDCOUNT       = message[8:12]
    ANCOUNT       = message[12:16]
    NSCOUNT       = message[16:20]
    ARCOUNT       = message[20:24]

    params = "{:b}".format(int(query_params, 16)).zfill(16)
    QPARAMS = OrderedDict([
        ("QR", params[0:1]),
        ("OPCODE", params[1:5]),
        ("AA", params[5:6]),
        ("TC", params[6:7]),
        ("RD", params[7:8]),
        ("RA", params[8:9]),
        ("Z", params[9:12]),
        ("RCODE", params[12:16])
    ])

    # Question section
    QUESTION_SECTION_STARTS = 24
    question_parts = parse_parts(message, QUESTION_SECTION_STARTS, [])
    
    QNAME = ".".join(map(lambda p: binascii.unhexlify(p).decode(), question_parts))    

    QTYPE_STARTS = QUESTION_SECTION_STARTS + (len("".join(question_parts))) + (len(question_parts) * 2) + 2
    QCLASS_STARTS = QTYPE_STARTS + 4

    QTYPE = message[QTYPE_STARTS:QCLASS_STARTS]
    QCLASS = message[QCLASS_STARTS:QCLASS_STARTS + 4]
    
    res.append("\n# HEADER")
    res.append("ID: " + ID)
    res.append("QUERYPARAMS: ")
    for qp in QPARAMS:
        res.append(" - " + qp + ": " + QPARAMS[qp])
    res.append("\n# QUESTION SECTION")
    res.append("QNAME: " + QNAME)
    res.append("QTYPE: " + QTYPE + " (\"" + get_type(int(QTYPE, 16)) + "\")")
    res.append("QCLASS: " + QCLASS)

    # Answer section
    ANSWER_SECTION_STARTS = QCLASS_STARTS + 4
    
    NUM_ANSWERS = max([int(ANCOUNT, 16), int(NSCOUNT, 16), int(ARCOUNT, 16)])
    if NUM_ANSWERS > 0:
        res.append("\n# ANSWER SECTION")
        
        for ANSWER_COUNT in range(NUM_ANSWERS):
            if (ANSWER_SECTION_STARTS < len(message)):
                ANAME = message[ANSWER_SECTION_STARTS:ANSWER_SECTION_STARTS + 4] # Refers to Question
                ATYPE = message[ANSWER_SECTION_STARTS + 4:ANSWER_SECTION_STARTS + 8]
                ACLASS = message[ANSWER_SECTION_STARTS + 8:ANSWER_SECTION_STARTS + 12]
                TTL = int(message[ANSWER_SECTION_STARTS + 12:ANSWER_SECTION_STARTS + 20], 16)
                RDLENGTH = int(message[ANSWER_SECTION_STARTS + 20:ANSWER_SECTION_STARTS + 24], 16)
                RDDATA = message[ANSWER_SECTION_STARTS + 24:ANSWER_SECTION_STARTS + 24 + (RDLENGTH * 2)]

                if ATYPE == get_type("A"):
                    octets = [RDDATA[i:i+2] for i in range(0, len(RDDATA), 2)]
                    RDDATA_decoded = ".".join(list(map(lambda x: str(int(x, 16)), octets)))
                else:
                    RDDATA_decoded = ".".join(map(lambda p: binascii.unhexlify(p).decode('iso8859-1'), parse_parts(RDDATA, 0, [])))
                    
                ANSWER_SECTION_STARTS = ANSWER_SECTION_STARTS + 24 + (RDLENGTH * 2)

            try: ATYPE
            except NameError: None
            else:  
                res.append("# ANSWER " + str(ANSWER_COUNT + 1))
                res.append("QDCOUNT: " + str(int(QDCOUNT, 16)))
                res.append("ANCOUNT: " + str(int(ANCOUNT, 16)))
                res.append("NSCOUNT: " + str(int(NSCOUNT, 16)))
                res.append("ARCOUNT: " + str(int(ARCOUNT, 16)))
                
                res.append("ANAME: " + ANAME)
                res.append("ATYPE: " + ATYPE + " (\"" + get_type(int(ATYPE, 16)) + "\")")
                res.append("ACLASS: " + ACLASS)
                
                res.append("\nTTL: " + str(TTL))
                res.append("RDLENGTH: " + str(RDLENGTH))
                res.append("RDDATA: " + RDDATA)
                res.append("RDDATA decoded (result): " + RDDATA_decoded + "\n")
                res2.append(RDDATA_decoded)
    return "\n".join(res)
def decode_message2(message):    
    res = []
    res2 =[]

    ID            = message[0:4]
    query_params  = message[4:8]
    QDCOUNT       = message[8:12]
    ANCOUNT       = message[12:16]
    NSCOUNT       = message[16:20]
    ARCOUNT       = message[20:24]

    params = "{:b}".format(int(query_params, 16)).zfill(16)
    QPARAMS = OrderedDict([
        ("QR", params[0:1]),
        ("OPCODE", params[1:5]),
        ("AA", params[5:6]),
        ("TC", params[6:7]),
        ("RD", params[7:8]),
        ("RA", params[8:9]),
        ("Z", params[9:12]),
        ("RCODE", params[12:16])
    ])

    # Question section
    QUESTION_SECTION_STARTS = 24
    question_parts = parse_parts(message, QUESTION_SECTION_STARTS, [])
    
    QNAME = ".".join(map(lambda p: binascii.unhexlify(p).decode(), question_parts))    

    QTYPE_STARTS = QUESTION_SECTION_STARTS + (len("".join(question_parts))) + (len(question_parts) * 2) + 2
    QCLASS_STARTS = QTYPE_STARTS + 4

    QTYPE = message[QTYPE_STARTS:QCLASS_STARTS]
    QCLASS = message[QCLASS_STARTS:QCLASS_STARTS + 4]
    
    res.append("\n# HEADER")
    res.append("ID: " + ID)
    res.append("QUERYPARAMS: ")
    for qp in QPARAMS:
        res.append(" - " + qp + ": " + QPARAMS[qp])
    res.append("\n# QUESTION SECTION")
    res.append("QNAME: " + QNAME)
    res.append("QTYPE: " + QTYPE + " (\"" + get_type(int(QTYPE, 16)) + "\")")
    res.append("QCLASS: " + QCLASS)

    # Answer section
    ANSWER_SECTION_STARTS = QCLASS_STARTS + 4
    
    NUM_ANSWERS = max([int(ANCOUNT, 16), int(NSCOUNT, 16), int(ARCOUNT, 16)])
    if NUM_ANSWERS > 0:
        res.append("\n# ANSWER SECTION")
        
        for ANSWER_COUNT in range(NUM_ANSWERS):
            if (ANSWER_SECTION_STARTS < len(message)):
                ANAME = message[ANSWER_SECTION_STARTS:ANSWER_SECTION_STARTS + 4] # Refers to Question
                ATYPE = message[ANSWER_SECTION_STARTS + 4:ANSWER_SECTION_STARTS + 8]
                ACLASS = message[ANSWER_SECTION_STARTS + 8:ANSWER_SECTION_STARTS + 12]
                TTL = int(message[ANSWER_SECTION_STARTS + 12:ANSWER_SECTION_STARTS + 20], 16)
                RDLENGTH = int(message[ANSWER_SECTION_STARTS + 20:ANSWER_SECTION_STARTS + 24], 16)
                RDDATA = message[ANSWER_SECTION_STARTS + 24:ANSWER_SECTION_STARTS + 24 + (RDLENGTH * 2)]

                if ATYPE == get_type("A"):
                    octets = [RDDATA[i:i+2] for i in range(0, len(RDDATA), 2)]
                    RDDATA_decoded = ".".join(list(map(lambda x: str(int(x, 16)), octets)))
                else:
                    RDDATA_decoded = ".".join(map(lambda p: binascii.unhexlify(p).decode('iso8859-1'), parse_parts(RDDATA, 0, [])))
                    
                ANSWER_SECTION_STARTS = ANSWER_SECTION_STARTS + 24 + (RDLENGTH * 2)

            try: ATYPE
            except NameError: None
            else:  
                res.append("# ANSWER " + str(ANSWER_COUNT + 1))
                res.append("QDCOUNT: " + str(int(QDCOUNT, 16)))
                res.append("ANCOUNT: " + str(int(ANCOUNT, 16)))
                res.append("NSCOUNT: " + str(int(NSCOUNT, 16)))
                res.append("ARCOUNT: " + str(int(ARCOUNT, 16)))
                
                res.append("ANAME: " + ANAME)
                res.append("ATYPE: " + ATYPE + " (\"" + get_type(int(ATYPE, 16)) + "\")")
                res.append("ACLASS: " + ACLASS)
                
                res.append("\nTTL: " + str(TTL))
                res.append("RDLENGTH: " + str(RDLENGTH))
                res.append("RDDATA: " + RDDATA)
                res.append("RDDATA decoded (result): " + RDDATA_decoded + "\n")
                res2.append(RDDATA_decoded)
    return RDDATA_decoded

def send_udp_message(message, address, port):
    """send_udp_message sends a message to UDP server
    message should be a hexadecimal encoded string
    """
    message = message.replace(" ", "").replace("\n", "")
    server_address = (address, port)

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.sendto(binascii.unhexlify(message), server_address)
        data, _ = sock.recvfrom(10000)

    return binascii.hexlify(data).decode("utf-8")

if len(sys.argv) > 1:
    url = sys.argv[1]
else:
    url = "www.tmz.com"
    
message = make_dns_request("A", url)

print("Request:\n" + message)
print("\nRequest (decoded):" + decode_message(message))

initial_time = time.time()
response = send_udp_message(message, "169.237.229.88", 53)
ending_time = time.time()

elapsed_time = str(ending_time - initial_time)
print('The Round Trip Time is {}'.format(elapsed_time))

print("\nResponse:\n" + response)

print("\nResponse (decoded):" + decode_message(response))


target_host = decode_message2(response)

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
     
