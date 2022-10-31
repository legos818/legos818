if (parameters[5:6] == "1"):
        # Question section
        #print(parameters[5:6],"\n\n\n\n\n\n\n\n\n")
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
        print("QTYPE = ",  QTYPE, " = ", type_decode(QTYPE))
        print("QCLASS = ",  QCLASS)

        # Answer section
        A_section_first = QCLASS_first + 4
        
        A_total = max([int(ANCOUNT, 16), int(NSCOUNT, 16), int(ARCOUNT, 16)])
        print("\n# ANSWER SECTION")
        Additional_section_first = 0

        for answers in range(A_total):
            
            if (A_section_first < len(message)):
                ANAME = message[A_section_first:A_section_first + 4] # Refers to Question
                ATYPE = message[A_section_first + 4:A_section_first + 8]
                ACLASS = message[A_section_first + 8:A_section_first + 12]
                TTL = int(message[A_section_first + 12:A_section_first + 20], 16)
                RDLENGTH = int(message[A_section_first + 20:A_section_first + 24], 16)
                RDDATA = message[A_section_first + 24:A_section_first + 24 + (RDLENGTH * 2)]

                if ATYPE == type_decode("0001"):
                    octets = [RDDATA[i:i+2] for i in range(0, len(RDDATA), 2)]
                    RDDATA_decoded = ".".join(list(map(lambda x: str(int(x, 16)), octets)))
                else: 
                    RDDATA_decoded = ".".join(map(lambda p: binascii.unhexlify(p).decode('iso8859-1'), parser(RDDATA, 0, [])))
                
                
                A_section_first = A_section_first + 24 + (RDLENGTH * 2)

                print("# ANSWER ", answers)
                print("QDCOUNT = ",  QDCOUNT)
                print("ANCOUNT = ",  ANCOUNT)
                print("NSCOUNT = ",  NSCOUNT)
                print("ARCOUNT = ",  ARCOUNT)
                
                print("ANAME = ",  ANAME)
                print("ATYPE = ",  ATYPE, type_decode(ATYPE))
                print("ACLASS = ",  ACLASS)
                
                print("\nTTL = ",  TTL)
                print("RDLENGTH = ",  RDLENGTH)
                print("RDDATA = ",  RDDATA)
                print("RDDATA decoded (decoded_message) = ",  RDDATA_decoded, "\n")
                #decoded_ip = RDDATA_decoded
                

        Additional_section_first = A_section_first
        
        print("\n\n\n", Additional_section_first)
        print("\n\n\n", len(message))
        #print(message[A_section_end:A_section_end+4])
        A_total = max([int(ANCOUNT, 16), int(NSCOUNT, 16), int(ARCOUNT, 16)])
        print("\n\n\n",A_total)

        print("\n# Additional SECTION")

        for answers in range(A_total):
            
            if (Additional_section_first < len(message)):
                ADD_NAME = message[Additional_section_first:Additional_section_first + 4] # Refers to Question
                ADD_TYPE = message[Additional_section_first + 4:Additional_section_first + 8]
                ADD_CLASS = message[Additional_section_first + 8:Additional_section_first + 12]
                ADD_TTL = int(message[Additional_section_first + 12:Additional_section_first + 20], 16)
                ADD_RDLENGTH = int(message[Additional_section_first + 20:Additional_section_first + 24], 16)
                ADD_RDDATA = message[Additional_section_first + 24:Additional_section_first + 24 + (ADD_RDLENGTH * 2)]
            
                '''decode = []
                if ADD_TYPE == "0001":

                    for pair in range(0, len(ADD_RDDATA), 2):
                        decode.append(ADD_RDDATA[pair:pair+2])

                    ADD_RDDATA_decoded = ""
                    for item in decode:
                        ADD_RDDATA_decoded += (str(int(item, 16)))
                        ADD_RDDATA_decoded += "."
                    ADD_RDDATA_decoded = ADD_RDDATA_decoded[:-1]
                else: 
                    ADD_RDDATA_decoded = ".".join(map(lambda p: binascii.unhexlify(p).decode('iso8859-1'), parser(ADD_RDDATA, 0, [])))'''
                if ATYPE == type_decode("0001"):
                    octets = [ADD_RDDATA[i:i+2] for i in range(0, len(ADD_RDDATA), 2)]
                    ADD_RDDATA_decoded = ".".join(list(map(lambda x: str(int(x, 16)), octets)))
                else: 
                    ADD_RDDATA_decoded = ".".join(map(lambda p: binascii.unhexlify(p).decode('iso8859-1'), parser(ADD_RDDATA, 0, [])))
                    
                    
                Additional_section_first = Additional_section_first + 24 + (ADD_RDLENGTH * 2)

                print("# ANSWER ", answers)
                print("QDCOUNT = ",  QDCOUNT)
                print("ANCOUNT = ",  ANCOUNT)
                print("NSCOUNT = ",  NSCOUNT)
                print("ARCOUNT = ",  ARCOUNT)
                
                print("ANAME = ",  ADD_NAME)
                print("ATYPE = ",  ADD_TYPE, type_decode(ADD_TYPE))
                print("ACLASS = ",  ADD_CLASS)
                
                print("\nTTL = ",  ADD_TTL)
                print("RDLENGTH = ",  ADD_RDLENGTH)
                print("RDDATA = ",  ADD_RDDATA)
                print("RDDATA decoded (decoded_message) = ",  ADD_RDDATA_decoded, "\n")
                decoded_ip = ADD_RDDATA_decoded
        return (decoded_ip)
