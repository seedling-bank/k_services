import asyncio
import json
import ssl
import threading
import time
import traceback

import loguru
import pandas as pd
import websockets

from base import db
from models.symbol_mapping import SymbolMapping, PriceOfData


async def get_symbol_mapping():
    try:
        symbol_query = (
            SymbolMapping
            .select(SymbolMapping.symbol)
        )
        symbol_mapping_df = pd.DataFrame(list(symbol_query.dicts()))
        pd.set_option('display.max_columns', None)
        symbol_mapping_list = symbol_mapping_df["symbol"].tolist()
        return symbol_mapping_list
    except Exception as e:
        loguru.logger.exception(e)
        loguru.logger.exception(traceback.format_exc())


class KServices():

    def __init__(self):
        self.price_queue = asyncio.Queue()

    # async def get_and_update_k_line_data(self, symbol):
    #     global response
    #     try:
    #         symbol = symbol.lower()
    #         uri = f"wss://stream.binance.com/ws/{symbol}@kline_1m"
    #
    #         ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    #         ssl_context.check_hostname = False
    #         ssl_context.verify_mode = ssl.CERT_NONE
    #
    #         # async with websockets.connect(uri, ping_interval=180, ssl=ssl_context, extra_headers=) as ws:
    #         while True:
    #             try:
    #                 async with websockets.connect(uri, ping_interval=180, ping_timeout=40, ssl=ssl_context) as ws:
    #                     response = await ws.recv()
    #                     response_json = json.loads(response)
    #
    #                     data = {
    #                         "eventtime": response_json["E"],
    #                         "symbol": response_json["k"]["s"],
    #                         "start": response_json["k"]["t"],
    #                         "end": response_json["k"]["T"],
    #                         "interval": response_json["k"]["i"],
    #                         "open": response_json["k"]["o"],
    #                         "close": response_json["k"]["c"],
    #                         "high": response_json["k"]["h"],
    #                         "low": response_json["k"]["l"],
    #                         "volume": response_json["k"]["v"],
    #                     }
    #
    #                     k_end = int(response_json["k"]["T"] / 1000)
    #
    #                     if int(response_json["E"] / 1000) == (k_end + 1):
    #                         loguru.logger.error(data)
    #                         await self.price_queue.put(data)
    #                         await ws.pong()
    #             except asyncio.exceptions.CancelledError:
    #                 raise
    #             except (websockets.exceptions.ConnectionClosedError, ConnectionResetError):
    #                 await asyncio.sleep(5)  # 等待一段时间后重连
    #             except asyncio.TimeoutError:
    #                 await asyncio.sleep(5)  # 等待一段时间后重连
    #     except Exception as e:
    #         loguru.logger.exception(e)
    #         loguru.logger.error(traceback.format_exc())

    async def get_and_update_kline_data(self, symbol, a=1):
        while True:
            try:
                uri = f"wss://stream.binance.com/ws/{symbol.lower()}@kline_1m"
                ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                async with websockets.connect(uri, ping_interval=180, ssl=ssl_context) as ws:
                    while True:
                        try:
                            response = await ws.recv()
                            res = json.loads(response)
                            # print(res)
                            data = {
                                "eventtime": res["E"],
                                "symbol": res["k"]["s"],
                                "start": res["k"]["t"],
                                "end": res["k"]["T"],
                                "interval": res["k"]["i"],
                                "open": res["k"]["o"],
                                "close": res["k"]["c"],
                                "high": res["k"]["h"],
                                "low": res["k"]["l"],
                                "volume": res["k"]["v"],
                            }

                            # 这根K线的这一分钟收盘分钟是
                            k_end = int(res["k"]["T"] / 1000)

                            if int(res["E"] / 1000) == (k_end + 1):
                                print(data)
                                PriceOfData.insert(data).execute()
                                # await self.price_queue.put(data)
                                await ws.pong()

                        except Exception as e:
                            pass
                            # logger.error(f"{format_exc()}")
                            # logger.error(f"get_and_update_kline_data: {e}|")

            except Exception as e:
                # logger.error(f"get_and_update_kline_data: {e}|3s准备重新执行..........")
                await asyncio.sleep(3)

    async def main(self):

        symbol_mapping_list = await get_symbol_mapping()

        symbol_mapping_list = list(set(symbol_mapping_list))

        tasks = []

        for i in range(0, len(symbol_mapping_list), 100):
            symbol_list_10 = symbol_mapping_list[i:i + 100]

            for symbol in symbol_list_10:
                task = asyncio.create_task(self.get_and_update_kline_data(symbol=symbol))
                tasks.append(task)

            loguru.logger.debug(f"{i + 100}个任务完成.................")

            for index, task in enumerate(tasks):
                if task.done() and task.exception():
                    # 如果任务完成但出现异常，重新启动任务
                    loguru.logger.error(f"Task {index} failed. Restarting...")
                    tasks[index] = asyncio.create_task(
                        self.get_and_update_kline_data(symbol=symbol_mapping_list[index]))

            await asyncio.sleep(45)

        loguru.logger.debug("全部任务开启完成.................")
        print(len(tasks))
        await asyncio.gather(*tasks)

    async def run(self):

        await asyncio.create_task(self.main())

    async def run_tasks(self):
        try:
            await asyncio.create_task(self.preparing_for_the_task())

            while True:
                try:
                    data = await self.price_queue.get()
                    PriceOfData.insert(data).execute()
                except Exception as e:
                    loguru.logger.exception(e)
                    loguru.logger.error(traceback.format_exc())
        except Exception as e:
            loguru.logger.exception(e)
            loguru.logger.error(traceback.format_exc())


if __name__ == '__main__':
    get_profit_loss = KServices()
    # asyncio.run(get_profit_loss.run_tasks())
    asyncio.run(get_profit_loss.run())
