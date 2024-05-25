import asyncio
import sys

# from ss_player.PlayerClient import PlayerClient

# from ss_player.kokurita_client import PlayerClient
from ss_player.mnaito_client2 import PlayerClient
# from ss_player.rnishi_client import PlayerClient
#from ss_player.snara_client import PlayerClient


def main():
    server_url = sys.argv[1]
    loop = asyncio.new_event_loop()
    print(f'client start : {server_url}')
    asyncio.set_event_loop(loop)
    client: PlayerClient = loop.run_until_complete(PlayerClient.create(server_url, loop))
    try:
        loop.run_until_complete(client.play())
    except KeyboardInterrupt:
        loop.run_until_complete(client.close())
        loop.close()
    except SystemExit:

        loop.run_until_complete(client.close())
        loop.close()


if __name__ == '__main__':
    main()
