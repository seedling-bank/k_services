import asyncio
import json
import ssl
import traceback

import loguru
import pandas as pd
import websockets

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
                                loguru.logger.error(f"{symbol}")
                                # await self.price_queue.put(data)
                                await ws.pong()

                        except Exception as e:
                            pass
            except Exception as e:
                await asyncio.sleep(3)

    async def main(self):

        symbol_mapping_list = await get_symbol_mapping()

        symbol_mapping_list = list(set(symbol_mapping_list))

        tasks = []

        for index, symbol in enumerate(symbol_mapping_list):
            tasks.append(asyncio.create_task(self.get_and_update_kline_data(symbol=symbol)))
            print(len(tasks))
        await asyncio.gather(*tasks)


if __name__ == '__main__':
    k_server = KServices()
    asyncio.run(k_server.main())

