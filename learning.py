import asyncio
import time
from datetime import datetime

def fetch_data(param):
    print (f"Do something with {param}")
    time.sleep(param)
    print(f"Done with {param}")
    return f"Result of {param}"
    


def main():
    # print(datetime.now().strftime("%H:%M:%S"))
    result1 = fetch_data(1)
    print("Fetch 1 fully completed")
    # print(datetime.now().strftime("%H:%M:%S"))
    result2 = fetch_data(2)
    print("Fetch 2 fully completed")
    # print(datetime.now().strftime("%H:%M:%S"))
    return [result1, result2]
    


t1 = time.perf_counter()
results = main()
print(results)
t2 = time.perf_counter()
print(f"Total time taken: {t2 - t1:.2f} seconds")
    



















##Event loop

# if __name__ == "__main__":
#     asyncio.run(main())
