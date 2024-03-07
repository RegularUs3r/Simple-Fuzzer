import argparse
import asyncio
import aiohttp
from requests import request
from time import sleep
from urllib3 import disable_warnings



def fuzz():
     disable_warnings()
     parser = argparse.ArgumentParser()
     parser.add_argument("-f", "--request-file", dest="request_file", metavar="", required=True)
     parser.add_argument("-w", "--wordlist", metavar="", required=True)
     parser.add_argument("-x", "--proxy", metavar="")
     parser.add_argument("-fs", "--filter-size", dest="filter_size", metavar="")
     parser.add_argument("-fc", "--filter-code", dest="filter_code", metavar="")
     parser.add_argument("-t", "--throttling", metavar="")
     args = parser.parse_args()
     request_file = args.request_file
     proxy = args.proxy
     wordlist = args.wordlist
     filter_size = args.filter_size
     filter_code = args.filter_code
     throttling = args.throttling

     proxy = proxy if proxy else None
     headers = {}
     with open(request_file, "r") as file:
          fline = file.readline().strip("\n").split(" ")
          method = fline[0]
          path = fline[1]
          for lines in file:
               lines = lines.strip()
               if "Host" in lines: host = "https://"+str(lines.split(" ")[1])
               elif " " in lines:
                    param_name, param_value = lines.split(": ")
                    headers[param_name] = param_value
               else: body = lines

     
     with open(wordlist, "r") as wordlist:
          for word in wordlist:
               word = word.strip()
               if "FUZZ" in body:
                    asyncio.run(body_request(method,host,path,headers,body,proxy,word,filter_size,filter_code,throttling))
               elif "FUZZ" in path:
                    asyncio.run(url_fuzzer(method,host,path,headers,proxy,word,filter_size,filter_code,throttling))
                    

async def body_request(method,host,path,headers,body,proxy,word,filter_size,filter_code,throttling):
     session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False))
     payload = body.replace("FUZZ", word)
     async with session.request(method, host+path, data=payload, proxy=proxy, headers=headers) as r:
          r_size = r.headers['content-length']
          r_code = r.status
          if filter_size:
               if "," in filter_size:
                    sizes = filter_size.split(",")
                    if str(r_size) not in sizes:
                         print(f"Payload-[{word}] Status Code-[{r_code}] Response Size-[{r_size}]")
               else:
                   if str(filter_size) != str(r_size):
                         print(f"Payload-[{word}] Status Code-[{r_code}] Response Size-[{r_size}]") 
          elif filter_code:
               if "," in filter_code:
                    codes = filter_code.split(",")
                    if str(r_code) not in codes:
                         print(f"Payload-[{word}] Status Code-[{r_code}] Response Size-[{r_size}]")
               else:     
                    if str(filter_code) != str(r_code):
                         print(f"Payload-[{word}] Status Code-[{r_code}] Response Size-[{r_size}]")
          elif filter_size and filter_code:
               if "," in filter_size or "," in filter_code:
                    sizes = filter_size.split(",")
                    codes = filter_code.split(",")
                    if str(r_size) not in sizes or str(r_code) not in codes:
                         print(f"Payload-[{word}] Status Code-[{r_code}] Response Size-[{r_size}]")
               
               if str(filter_size) != str(r_size) and str(filter_code) != str(r_code):
                    print(f"Payload-[{word}] Status Code-[{r_code}] Response Size-[{r_size}]")
          else:
               print(f"Payload-[{word}] Status Code-[{r_code}] Response Size-[{r_size}]")
          sleep(int(throttling))
          await session.close()




async def url_fuzzer(method,host,path,headers,proxy,word,filter_size,filter_code,throttling):
     session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False))
     payload = path.replace("FUZZ", word)
     async with session.request(method, host+payload, proxy=proxy, headers=headers) as r:
          r_size = r.headers['content-length']
          r_code = r.status
          if filter_size:
               if "," in filter_size:
                    sizes = filter_size.split(",")
                    if str(r_size) not in sizes:
                         print(f"Payload-[{word}] Status Code-[{r_code}] Response Size-[{r_size}]")
               else:
                   if str(filter_size) != str(r_size):
                         print(f"Payload-[{word}] Status Code-[{r_code}] Response Size-[{r_size}]") 
          elif filter_code:
               if "," in filter_code:
                    codes = filter_code.split(",")
                    if str(r_code) not in codes:
                         print(f"Payload-[{word}] Status Code-[{r_code}] Response Size-[{r_size}]")
               else:     
                    if str(filter_code) != str(r_code):
                         print(f"Payload-[{word}] Status Code-[{r_code}] Response Size-[{r_size}]")
          elif filter_size and filter_code:
               if "," in filter_size or "," in filter_code:
                    sizes = filter_size.split(",")
                    codes = filter_code.split(",")
                    if str(r_size) not in sizes or str(r_code) not in codes:
                         print(f"Payload-[{word}] Status Code-[{r_code}] Response Size-[{r_size}]")
               
               if str(filter_size) != str(r_size) and str(filter_code) != str(r_code):
                    print(f"Payload-[{word}] Status Code-[{r_code}] Response Size-[{r_size}]")
          else:
               print(f"Payload-[{word}] Status Code-[{r_code}] Response Size-[{r_size}]")
          sleep(int(throttling))
          await session.close()

fuzz()
